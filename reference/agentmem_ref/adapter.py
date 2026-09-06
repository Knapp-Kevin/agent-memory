"""The governed adapter.

Implements the end-to-end path the runtime-evidence program requires:

```text
evidence -> proposal -> authority envelope -> permitted action set
         -> selected action -> substrate mutation -> decision receipt
         -> retrieval candidate -> governed admission -> active context
```

Everything the mapped substrate cannot supply is supplied here: enforced scope
filtering, an authority gate in front of every write, lifecycle state,
tombstones, and receipts. The substrate stores; it never decides.

Stdlib only apart from the schema validation reached through `receipts`.
"""

from __future__ import annotations

from typing import Callable, Mapping, Sequence

import random
from dataclasses import dataclass, field

from . import policy, receipts
from .evidence_qualification import EvidenceItem
from .verification import VerifierRegistry
from .readmission import RejectedValueRegistry
from .substrate import DeterministicIds, Episode, Fact, TemporalGraphPort


class Clock:
    """Deterministic clock, so runs are reproducible."""

    def __init__(self, start: int = 0) -> None:
        self._t = start

    def now(self) -> str:
        self._t += 1
        return f"2026-01-01T00:00:{self._t:02d}Z"


class DeterministicSelector:
    """Prefers the requested operation when permitted, else the first permitted action."""

    mode = "deterministic"

    def select(self, permitted: tuple[str, ...], preferred: str | None) -> str:
        if not permitted:
            return receipts.NO_ACTION
        if preferred in permitted:
            return preferred
        return permitted[0]


class StochasticSelector:
    """Samples uniformly from the permitted set.

    Doctrine permits stochastic action selection *inside* an authority
    envelope. It is the adapter, not this selector, that guarantees the choice
    stays inside: a selector is untrusted by construction, so whatever it
    returns is re-checked against the permitted set before use.
    """

    mode = "stochastic"

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def select(self, permitted: tuple[str, ...], preferred: str | None) -> str:
        if not permitted:
            return receipts.NO_ACTION
        return self._rng.choice(list(permitted))


@dataclass
class CommitResult:
    decision: policy.Decision
    pama_decision: dict
    receipt: dict
    events: list[dict] = field(default_factory=list)
    committed: bool = False
    fact_uuid: str | None = None
    refusal: str | None = None


@dataclass
class AdmissionResult:
    candidates: list[str] = field(default_factory=list)
    admitted: list[str] = field(default_factory=list)
    refusals: dict[str, str] = field(default_factory=dict)
    # GAP-SEC-02 (LD5): additive record fields. Defaulted so the 70 existing
    # governed_recall call sites, which read only candidates/admitted/refusals,
    # are unaffected. Schema-backing this class is GAP-ARCH-01 / Sprint 4; this
    # cycle must not freeze a contract that boundary freeze will re-shape.
    decisions: dict[str, dict] = field(default_factory=dict)
    policy_version: str = ""
    evaluated_at: str = ""


@dataclass(frozen=True)
class RecallContext:
    """Authority context for one governed recall request.

    Domain refs are logical authority boundaries. They are not storage
    partitions and their tuple order does not imply hierarchy. A target context
    may carry several active domains so mandatory compartment constraints can
    be checked conjunctively without redefining ordinary domain routes.
    """

    target_domain_refs: tuple[str, ...]
    principal_ref: str = ""
    project_ref: str = ""
    task_ref: str = ""
    purpose: str = ""


class GovernedMemoryAdapter:
    """Wraps a permissive substrate in the governance it does not provide."""

    def __init__(
        self,
        substrate: TemporalGraphPort,
        tenant: str,
        clock: Clock | None = None,
        selector=None,
        verifier_registry: "VerifierRegistry | None" = None,
    ) -> None:
        # ADR-037 step 4b-2. Verifier trust is configured HERE, by the host that
        # builds the adapter -- not passed per operation by whoever is making a
        # proposal. Registering your own verifier is certifying your own
        # evidence. An empty registry is the safe default: evidence naming a
        # verifier nobody holds stays `asserted`, exactly as step 2 defined.
        self._verifier_registry = verifier_registry or VerifierRegistry()
        self._substrate = substrate
        self._tenant = tenant
        self._clock = clock or Clock()
        self._selector = selector or DeterministicSelector()
        # GAP-SEC-08 (LD1): draw identifiers from the substrate when it offers
        # a counter, so adapters sharing a substrate cannot mint colliding ids.
        # Attribute discovery, not a Protocol member: TemporalGraphPort is a
        # Protocol and declaring next_id would break external implementations.
        # Single-adapter sequences are unchanged -- a substrate counter starting
        # at zero with one consumer emits exactly what the per-adapter counter
        # emitted before.
        substrate_ids = getattr(substrate, "_ids", None)
        self._ids = substrate_ids if isinstance(substrate_ids, DeterministicIds) else DeterministicIds("ref")
        self.containment_violations: list[str] = []
        self._state_version: dict[str, int] = {}
        self._disputed: set[str] = set()
        self._tombstones: dict[str, dict] = {}
        self._fact_scope: dict[str, dict] = {}
        # GAP-SEC-03 (LD2): fact -> the memory it was written for. _fact_scope
        # carries no memory reference and _current_fact_by_memory holds only the
        # *current* fact per memory, so neither can authorize deleting a
        # superseded fact. Snapshotted by restart_runtime (LD2b).
        self._fact_memory: dict[str, str] = {}
        self._shared_domain_members: dict[str, set[str]] = {}
        self._current_fact_by_memory: dict[str, str] = {}
        self._rejected_values = RejectedValueRegistry()
        self.events: list[dict] = []

    # -- isolation-domain administration -------------------------------

    def set_shared_domain_members(self, domain_ref: str, members: tuple[str, ...]) -> None:
        """Replace current membership for a governed shared-memory domain.

        This is a narrow reference seam, not a complete membership service.
        Recall always consults the current set so revocation affects subsequent
        admission without rewriting the retained memory itself.
        """
        if not domain_ref:
            raise ValueError("shared domain requires a stable domain ref")
        self._shared_domain_members[domain_ref] = set(members)

    # -- write path -----------------------------------------------------

    def commit_proposal(
        self,
        proposal: policy.Proposal,
        fact_text: str,
        episode: Episode | None = None,
        *,
        evidence: "Sequence[EvidenceItem] | None" = None,
        attestation: policy.ExternalVerification | None = None,
    ) -> CommitResult:
        """Commit a proposal through the governed path.

        SCOPE ADDITION, disclosed (ADR-037 step 4b-2, entry #24). The flip
        removed the asserted discharge for `require_review`, and this adapter --
        the primary governed entry point -- had **no** way to present evidence:
        it called `policy.evaluate` directly. Every adapter caller would have
        been left with a refusal and no reachable remediation, which is the halt
        ADR-037's sequencing principle forbids.

        `evidence` is optional and defaults to None, so a caller that supplies
        none behaves exactly as before -- it simply parks where it used to
        discharge on assertion. Supplying evidence routes through
        `policy.evaluate_with_qualified_evidence`, which enforces R5's ladder.

        **There is deliberately no `verifiers=` parameter.** Verifier trust is
        held by this adapter's `verifier_registry`, configured by the host that
        constructs it. A per-call mapping would let a caller register its own
        verifier, which is certifying its own evidence -- `review_satisfied=True`
        rebuilt with more Python (operator ruling, 2026-09-05).

        Evidence never touches `review_satisfied` or `approval_refs`. Those are
        legacy migration state; qualified discharge is its own path.

        Mirrors Loop 7's disclosed addition of `external_verification` to
        `governed_delete` for the same reason: capping a discharge without
        providing the replacement channel removes a legitimate operation rather
        than governing it.
        """
        correlation = self._ids.next()
        if episode is not None:
            self._substrate.add_episode(episode)
        propose_event = self._event("memory.propose", proposal.target_reference, correlation)

        if evidence:
            from .evidence_qualification import group_by_dependence

            decision = policy.evaluate_with_qualified_evidence(
                proposal,
                group_by_dependence(
                    evidence, verifiers=self._verifier_registry.as_mapping()
                ),
                attestation=attestation,
            )
        else:
            decision = policy.evaluate(proposal)
        authorize_event = self._event(
            "memory.authorize",
            proposal.target_reference,
            correlation,
            causation_id=propose_event["event_id"],
            policy_version=decision.policy_version,
            authority={
                "permitted_actions": list(decision.permitted_actions),
                "prohibited_actions": list(decision.prohibited_actions),
                "selection_mode": "none",
            },
        )
        events = [propose_event, authorize_event]

        stale = self._is_stale(proposal)
        readmission_blocked = self._readmission_blocked(proposal, fact_text)
        selected = self._select_action(
            decision,
            proposal,
            blocked_by_stale=stale or readmission_blocked,
        )
        commits = selected == proposal.operation
        before_state = f"v{self._state_version.get(proposal.target_reference, 0)}"

        if readmission_blocked:
            events.append(
                self._event(
                    "memory.readmission_blocked",
                    proposal.target_reference,
                    correlation,
                    causation_id=authorize_event["event_id"],
                    policy_version=decision.policy_version,
                )
            )

        fact_uuid = None
        if commits:
            if proposal.operation == "correction":
                self._supersede_current(proposal)
                self._rejected_values.readmit(
                    memory_id=proposal.target_reference,
                    value=fact_text,
                    proposal_id=proposal.proposal_id,
                    readmitted_at=self._clock.now(),
                )
            fact_uuid = self._write(proposal, fact_text)
            self._current_fact_by_memory[proposal.target_reference] = fact_uuid
            events.append(
                self._event(
                    "memory.commit",
                    proposal.target_reference,
                    correlation,
                    causation_id=authorize_event["event_id"],
                    policy_version=decision.policy_version,
                )
            )
        after_state = f"v{self._state_version.get(proposal.target_reference, 0)}"

        receipt_id = self._ids.next()
        receipt = receipts.build_receipt(
            receipt_id=receipt_id,
            proposal=proposal,
            decision=decision,
            selected_action=selected,
            selection_mode=self._selector.mode if selected != receipts.NO_ACTION else "none",
            timestamp=self._clock.now(),
            before_state=before_state,
            after_state=after_state,
            rollback_ref=f"recovery:{proposal.target_reference}:{before_state}" if commits else None,
        )
        pama_decision = receipts.build_pama_decision(
            proposal,
            decision,
            selected,
            self._selector.mode if selected != receipts.NO_ACTION else None,
            receipt_id,
        )
        events.append(
            self._event(
                "memory.receipt",
                proposal.target_reference,
                correlation,
                causation_id=events[-1]["event_id"],
                receipt_ref=receipt_id,
            )
        )
        self.events.extend(events)

        refusal = None
        if stale:
            refusal = "stale_authorization"
        elif readmission_blocked:
            refusal = "rejected_value_requires_reconciliation"

        return CommitResult(
            decision=decision,
            pama_decision=pama_decision,
            receipt=receipt,
            events=events,
            committed=commits,
            fact_uuid=fact_uuid,
            refusal=refusal,
        )

    def _is_stale(self, proposal: policy.Proposal) -> bool:
        """Authority binds to the state it was resolved against."""
        if not proposal.state_snapshot:
            return False
        current = f"v{self._state_version.get(proposal.target_reference, 0)}"
        return proposal.state_snapshot != current

    def _readmission_blocked(self, proposal: policy.Proposal, fact_text: str) -> bool:
        """Fail closed when an exact rejected value attempts silent re-entry.

        An externally approved correction is an explicit reversal path. It may
        re-admit a previously rejected value because policy has already required
        review for correction. Ordinary promotion/import-style writes cannot.
        """
        if self._rejected_values.active(proposal.target_reference, fact_text) is None:
            return False
        approved_reversal = (
            proposal.operation == "correction"
            and proposal.review_satisfied
            and bool(proposal.approval_refs)
            and not proposal.approves_own_authority
        )
        return not approved_reversal

    def _supersede_current(self, proposal: policy.Proposal) -> None:
        """Invalidate the current fact and record its value as rejected.

        This is the minimum correction seam needed to test ADR-023/ADR-027
        composition. It does not claim full #142 closure.
        """
        current_uuid = self._current_fact_by_memory.get(proposal.target_reference)
        if not current_uuid:
            return
        current = self._substrate.get_fact(current_uuid)
        if current is None or current.is_event_invalid:
            return

        rejected_at = self._clock.now()
        self._rejected_values.reject(
            memory_id=proposal.target_reference,
            value=current.fact_text,
            superseded_fact_uuid=current.uuid,
            correction_proposal_id=proposal.proposal_id,
            evidence_refs=tuple(proposal.evidence_refs),
            scope=proposal.scope,
            rejected_at=rejected_at,
        )
        self._substrate.invalidate_fact(
            current.uuid,
            invalid_at=rejected_at,
            expired_at=self._clock.now(),
        )

    def _select_action(self, decision: policy.Decision, proposal: policy.Proposal, blocked_by_stale: bool) -> str:
        permitted = decision.permitted_actions
        if not permitted:
            return receipts.NO_ACTION
        if blocked_by_stale:
            return "defer" if "defer" in permitted else permitted[0]

        choice = self._selector.select(permitted, proposal.operation)
        return self._contain(permitted, choice)

    def _contain(self, permitted: tuple[str, ...], choice: str) -> str:
        """Re-check any selector's output against the envelope.

        A selector is untrusted: deterministic, stochastic, or learned, it
        proposes and does not authorize. A choice outside the permitted set is
        a containment violation, recorded and failed closed to a deferral
        rather than executed. Randomness does not create permission.
        """
        try:
            receipts.enforce_selection(permitted, choice)
        except ValueError as exc:
            self.containment_violations.append(str(exc))
            return "defer" if "defer" in permitted else permitted[0]
        return choice

    def _write(self, proposal: policy.Proposal, fact_text: str) -> str:
        domain_refs = tuple(proposal.isolation_domain_refs) or ((proposal.scope,) if proposal.scope else (self._tenant,))
        required_domains = tuple(dict.fromkeys(proposal.required_isolation_domain_refs))
        if required_domains and not set(required_domains).issubset(set(domain_refs)):
            raise ValueError("required isolation domains must also be bound isolation domains")

        uuid = self._ids.next()
        self._substrate.write_fact(
            Fact(
                uuid=uuid,
                fact_text=fact_text,
                group_id=self._tenant,
                episode_uuids=tuple(proposal.evidence_refs),
                valid_at=self._clock.now(),
                created_at=self._clock.now(),
            )
        )
        self._fact_scope[uuid] = {
            "domain_refs": domain_refs,
            "required_domain_refs": required_domains,
            "project_ref": proposal.project_ref,
            "task_ref": proposal.task_ref,
            "purpose": proposal.purpose,
        }
        self._fact_memory[uuid] = proposal.target_reference
        self._state_version[proposal.target_reference] = self._state_version.get(proposal.target_reference, 0) + 1
        return uuid

    # -- read path ------------------------------------------------------

    def governed_recall(self, query: str, context: RecallContext | None = None) -> AdmissionResult:
        """Retrieve candidates, then admit only what current authority allows.

        Tenant partitioning is enforced before retrieval. Logical isolation
        domains, mandatory compartment constraints, shared-space membership,
        project, and task are evaluated at admission because the in-memory
        substrate is trusted to return same-tenant candidates for policy
        evaluation. Candidate presence remains distinct from admission authority.
        """
        context = context or RecallContext(target_domain_refs=(self._tenant,))
        evaluated_at = self._clock.now()
        result = AdmissionResult(
            policy_version=policy.POLICY_VERSION, evaluated_at=evaluated_at
        )
        correlation = self._ids.next()
        for fact, _score in self._substrate.search(query, group_ids=[self._tenant]):
            result.candidates.append(fact.uuid)
            refusal = self._admission_refusal(fact, context)
            if refusal:
                result.refusals[fact.uuid] = refusal
            else:
                result.admitted.append(fact.uuid)
            # GAP-SEC-02 (LD4): record the built-in decision. Every refusal
            # reason was previously computed and discarded -- ContextualRecall-
            # Adapter only ever sees candidates that already passed, so built-in
            # decisions were recorded by neither layer.
            result.decisions[fact.uuid] = self._recall_decision(
                fact.uuid, context, refusal, evaluated_at
            )
        self.events.append(
            self._recall_event(query, context, result, correlation, evaluated_at)
        )
        return result

    def _recall_decision(
        self,
        candidate_ref: str,
        context: RecallContext,
        refusal: str | None,
        evaluated_at: str,
    ) -> dict:
        """A built-in admission decision in the canonical recall-decision shape.

        Reuses `contextual-recall-admission.schema.json` rather than inventing a
        record, so both recall layers speak one vocabulary.
        """
        decision = {
            "schema_version": "1.0.0",
            "profile_version": "0.1.0",
            "decision_id": self._ids.next(),
            "candidate_ref": candidate_ref,
            "policy": {
                # LD6: the recall path does not call policy.evaluate. Recording
                # "evaluated" would fabricate a decision the reference never
                # made; of the four enum members, "unavailable" is the honest
                # one -- no contextual policy was available to evaluate. A value
                # meaning "built-in admission" does not exist in the schema and
                # belongs to Sprint 4 / GAP-ARCH-01.
                "policy_ref": "contextual-recall-policy:none",
                "policy_version": policy.POLICY_VERSION,
                "status": "unavailable",
                "selection_mode": "deterministic",
            },
            "context": {
                "target_domain_refs": list(context.target_domain_refs),
                "principal_ref": context.principal_ref,
                "project_ref": context.project_ref,
                "task_ref": context.task_ref,
                "purpose": context.purpose,
                "destination_ref": "",
            },
            "outcome": "admit" if refusal is None else "block",
            "reason_code": refusal or "builtin_admission",
            "evidence_refs": [],
            "evaluated_at": evaluated_at,
            "interpretation": {
                "authority_effect": "current_recall_only",
                "prior_admission_authority": "none",
                "memory_mutation": "not_performed",
                "relevance_authority": "none",
                "risk_signal_authority": "none",
            },
        }
        receipts.validate("contextual-recall-admission.schema.json", decision)
        return decision

    def _recall_event(
        self,
        query: str,
        context: RecallContext,
        result: AdmissionResult,
        correlation: str,
        evaluated_at: str,
    ) -> dict:
        """One governance record per governed recall.

        Field placement is dictated by the schema, which sets
        `additionalProperties: False`: only named properties at top level, and
        the rest under `payload` (`additionalProperties: true`).
        `signal_type`/`signal_semantics` are the literals docs/34:136 requires.
        """
        # `receipts.build_audit_event` is the commit-path builder: it requires a
        # single `memory_id` and supports neither `principal`, `signal`, nor
        # `payload`. A recall event legitimately spans many candidates and has no
        # single memory_id -- docs/34 puts `memory_id` on the per-unit decisions,
        # which `_recall_decision` carries. So the document is built here and
        # validated against the same schema, rather than widening the commit
        # builder for a shape it does not model.
        document = {
            "schema_version": "1.0.0",
            "event_id": self._ids.next(),
            "event_type": "memory.recall",
            "event_version": "1.0.0",
            "timestamp": evaluated_at,
            "component": "governed-adapter",
            "correlation_id": correlation,
            "principal": context.principal_ref,
            "policy_version": policy.POLICY_VERSION,
            "signal": {
                "signal_type": "recall_admission",
                "signal_semantics": (
                    f"{len(result.admitted)} of {len(result.candidates)} candidates admitted"
                ),
            },
            "payload": {
                "query": query,
                "target_domain_refs": list(context.target_domain_refs),
                "project_ref": context.project_ref,
                "task_ref": context.task_ref,
                "purpose": context.purpose,
                "candidate_count": len(result.candidates),
                "admitted_count": len(result.admitted),
                "outcomes": {
                    uuid: ("admit" if uuid in result.admitted else result.refusals[uuid])
                    for uuid in result.candidates
                },
            },
        }
        receipts.validate("memory-audit-event.schema.json", document)
        return document

    def _admission_refusal(self, fact: Fact, context: RecallContext) -> str | None:
        if fact.group_id != self._tenant:
            return "out_of_scope"
        if fact.uuid in self._tombstones:
            return "tombstoned"
        if any(source_ref in self._tombstones for source_ref in fact.episode_uuids):
            return "derived_from_tombstoned_source"
        if fact.is_event_invalid:
            return "superseded_not_current"
        if fact.uuid in self._disputed:
            return "disputed"

        scope = self._fact_scope.get(fact.uuid)
        if scope is None:
            # GAP-ARCH-18 (LD1): docs/34:139 -- "candidates that arrive without
            # scope metadata are rejected from admission; unknown scope is
            # treated as out-of-scope, never as local". The string is dictated
            # by the JS runtime, which already refuses this case:
            # integrations/agent-memory-runtime/src/index.mjs:114.
            return "unknown_scope"

        memory_domains = set(scope["domain_refs"])
        required_domains = set(scope.get("required_domain_refs", ()))
        target_domains = set(context.target_domain_refs)
        matching_domains = memory_domains.intersection(target_domains)
        if not target_domains or not matching_domains:
            return "isolation_domain_mismatch"
        if required_domains and not required_domains.issubset(target_domains):
            return "required_isolation_domain_missing"

        # A shared domain is still an isolation boundary. If all matching
        # routes are governed shared spaces, at least one must currently admit
        # the requesting principal as a member. Membership is necessary but
        # not sufficient; project/task/purpose gates continue below.
        shared_matches = {domain for domain in matching_domains if domain in self._shared_domain_members}
        if shared_matches == matching_domains:
            if not context.principal_ref:
                return "shared_space_membership_unresolved"
            if not any(context.principal_ref in self._shared_domain_members[domain] for domain in shared_matches):
                return "shared_space_non_member"

        memory_project = scope.get("project_ref", "")
        if memory_project and context.project_ref != memory_project:
            return "project_scope_mismatch"

        memory_task = scope.get("task_ref", "")
        if memory_task and context.task_ref != memory_task:
            return "task_scope_mismatch"

        return None

    def mark_disputed(self, fact_uuid: str) -> None:
        self._disputed.add(fact_uuid)

    # -- canonical state accessors --------------------------------------

    def state_version(self, memory_id: str) -> int:
        return self._state_version.get(memory_id, 0)

    def current_fact_uuid(self, memory_id: str) -> str | None:
        return self._current_fact_by_memory.get(memory_id)

    def rejected_value_history(self, memory_id: str, fact_text: str) -> tuple[dict, ...]:
        return self._rejected_values.history(memory_id, fact_text)

    def tombstoned_ids(self) -> set[str]:
        return {record["memory_id"] for record in self._tombstones.values()}

    def record_correction(self, memory_id: str) -> int:
        """A correction advances canonical version; dependents become stale by relation."""
        self._state_version[memory_id] = self._state_version.get(memory_id, 0) + 1
        return self._state_version[memory_id]

    # -- deletion -------------------------------------------------------

    def _delete_refusal(self, proposal: policy.Proposal, fact_uuid: str) -> str | None:
        """Authority checks the delete path never performed (GAP-SEC-03).

        One substrate lookup answers existence (D5) and ownership (D4); the
        binding map answers whether the fact belongs to the memory the proposal
        claims (D2), which is also what stops a falsified tombstone (D3).
        """
        fact = self._substrate.get_fact(fact_uuid)
        if fact is None:
            return "fact_not_found"
        if fact.group_id != self._tenant:
            return "cross_tenant_delete"
        bound_memory = self._fact_memory.get(fact_uuid)
        if bound_memory is None:
            # Unknown provenance is not permission -- same stance as Loop 3's
            # unknown_scope on the read path.
            return "target_binding_unknown"
        if bound_memory != proposal.target_reference:
            return "target_binding_mismatch"
        return None

    def governed_delete(
        self,
        proposal: policy.Proposal,
        fact_uuid: str,
        derived_refs: tuple[str, ...] = (),
        external_verification: "policy.ExternalVerification | None" = None,
        evidence: "Sequence[EvidenceItem] | None" = None,
    ) -> CommitResult:
        """Delete through the authority gate, leaving a tombstone the substrate cannot.

        ADR-037 step 4b-2, DoD 20: `evidence` joins `external_verification` for
        the same reason Loop 7 added that one. An irreversible deletion at low
        or medium risk resolves to `require_review`, which no longer discharges
        on assertion -- so without this channel the adapter could not perform a
        legitimate deletion at all, only refuse one. Verifier trust remains the
        adapter's evaluator-owned registry; there is no `verifiers=` here.

        GAP-ARCH-04: `permanent_deletion` at high or critical risk resolves to
        `require_external_verification`, which can no longer be discharged by
        assertion. Supply an attestation to perform one. Discovered during Loop 7
        implementation: without this parameter the adapter could not perform a
        critical permanent deletion at all, which would have removed a legitimate
        operation rather than governing it.
        """
        correlation = self._ids.next()
        if evidence:
            from .evidence_qualification import group_by_dependence

            decision = policy.evaluate_with_qualified_evidence(
                proposal,
                group_by_dependence(
                    evidence, verifiers=self._verifier_registry.as_mapping()
                ),
                attestation=external_verification,
            )
        else:
            decision = (
                policy.evaluate(proposal)
                if external_verification is None
                else policy.evaluate_with_external_verification(
                    proposal, external_verification
                )
            )
        # GAP-SEC-03: deletion is the more destructive path and had the weaker
        # guard. Ordered so a refusal names the real problem (LD4): a nonexistent
        # fact must not report a tenant error, and a foreign fact must not report
        # a binding error.
        refusal = self._delete_refusal(proposal, fact_uuid)
        stale = self._is_stale(proposal)
        selected = self._select_action(decision, proposal, blocked_by_stale=stale)
        committed = refusal is None and selected == proposal.operation
        if refusal is None and stale:
            refusal = "stale_decision"
        before_state = f"v{self._state_version.get(proposal.target_reference, 0)}"

        if committed:
            self._tombstones[fact_uuid] = {
                "memory_id": proposal.target_reference,
                "fact_uuid": fact_uuid,
                "deleted_at": self._clock.now(),
                "declared_derived_refs": list(derived_refs),
                "mode": proposal.operation,
                "reversible": proposal.operation != "permanent_deletion",
            }
            # Pruning removes from active recall and keeps the content recoverable;
            # only permanent deletion reaches the substrate's physical delete.
            if proposal.operation == "permanent_deletion":
                self._substrate.delete_fact(fact_uuid)
            if self._current_fact_by_memory.get(proposal.target_reference) == fact_uuid:
                self._current_fact_by_memory.pop(proposal.target_reference, None)
            self._state_version[proposal.target_reference] = self._state_version.get(proposal.target_reference, 0) + 1

        receipt_id = self._ids.next()
        receipt = receipts.build_receipt(
            receipt_id=receipt_id,
            proposal=proposal,
            decision=decision,
            selected_action=selected,
            selection_mode=self._selector.mode if selected != receipts.NO_ACTION else "none",
            timestamp=self._clock.now(),
            before_state=before_state,
            after_state=f"v{self._state_version.get(proposal.target_reference, 0)}",
        )
        pama_decision = receipts.build_pama_decision(
            proposal, decision, selected, self._selector.mode if selected != receipts.NO_ACTION else None, receipt_id
        )
        event = self._event("memory.delete", proposal.target_reference, correlation, receipt_ref=receipt_id)
        self.events.append(event)
        return CommitResult(
            decision=decision,
            pama_decision=pama_decision,
            receipt=receipt,
            events=[event],
            committed=committed,
            fact_uuid=fact_uuid if committed else None,
            refusal=refusal,
        )

    def undeclared_residue(self, fact_uuid: str) -> list[str]:
        """Substrate remnants referencing a tombstoned fact that were not declared."""
        tombstone = self._tombstones.get(fact_uuid)
        if tombstone is None:
            return []
        declared = set(tombstone["declared_derived_refs"])
        remnants = [
            candidate.uuid
            for candidate in getattr(self._substrate, "all_facts", tuple)()
            if fact_uuid in candidate.episode_uuids and candidate.uuid not in declared
        ]
        return remnants

    def tombstone(self, fact_uuid: str) -> dict | None:
        return self._tombstones.get(fact_uuid)

    # -- helpers --------------------------------------------------------

    def _event(self, event_type: str, memory_id: str, correlation: str, **extra) -> dict:
        return receipts.build_audit_event(
            event_id=self._ids.next(),
            event_type=event_type,
            timestamp=self._clock.now(),
            component="governed-adapter",
            memory_id=memory_id,
            correlation_id=correlation,
            **extra,
        )