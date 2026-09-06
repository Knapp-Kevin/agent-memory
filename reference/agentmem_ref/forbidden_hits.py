"""Explicit forbidden-hit lifecycle assertions for issue #148.

The model keeps four stages distinct even when the current reference adapter
blocks at admission and therefore makes later stages false as a consequence:

candidate discovered != admitted != context surfaced != downstream influence

Expectations live in ``fixtures/forbidden-hit-lifecycle-matrix.json`` so the
coverage claim is inspectable and reusable. This module executes the current
reference scenarios and compares observed stage outcomes to those assertions.

Stdlib only apart from the schema validation already used by the reference
adapter.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import policy
from .pending_verification import PendingVerificationRegistry
from .resumption import CRITERION_GATE, criteria_for
from .adapter import Clock, GovernedMemoryAdapter, RecallContext
from .substrate import Fact, InMemoryTemporalGraph

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "forbidden-hit-lifecycle-matrix.json"
TENANT = "tenant-a"


@dataclass(frozen=True)
class ForbiddenHitAssertion:
    assertion_id: str
    forbidden_class: str
    source_lifecycle_state: str
    source_evidence: str
    candidate_discovered: bool
    admitted: bool
    context_surfaced: bool
    downstream_influence: bool
    expected_refusal: str


@dataclass(frozen=True)
class ForbiddenHitObservation:
    assertion_id: str
    candidate_discovered: bool
    admitted: bool
    context_surfaced: bool
    downstream_influence: bool
    refusal: str


class ForbiddenHitMismatch(ValueError):
    pass


def load_assertions(path: Path = MATRIX) -> tuple[ForbiddenHitAssertion, ...]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return tuple(ForbiddenHitAssertion(**item) for item in document["forbidden_hit_assertions"])


def compare(assertion: ForbiddenHitAssertion, observation: ForbiddenHitObservation) -> None:
    if assertion.assertion_id != observation.assertion_id:
        raise ForbiddenHitMismatch(
            f"assertion identity mismatch: {assertion.assertion_id!r} != {observation.assertion_id!r}"
        )
    fields = (
        "candidate_discovered",
        "admitted",
        "context_surfaced",
        "downstream_influence",
    )
    for field in fields:
        expected = getattr(assertion, field)
        observed = getattr(observation, field)
        if expected != observed:
            raise ForbiddenHitMismatch(
                f"{assertion.assertion_id}: {field} expected {expected!r}, observed {observed!r}"
            )
    if assertion.expected_refusal != observation.refusal:
        raise ForbiddenHitMismatch(
            f"{assertion.assertion_id}: refusal expected {assertion.expected_refusal!r}, "
            f"observed {observation.refusal!r}"
        )


def run() -> dict:
    assertions = load_assertions()
    observed = _observations()
    by_id = {item.assertion_id: item for item in observed}
    failures: list[str] = []
    coverage: list[dict] = []

    for assertion in assertions:
        observation = by_id.get(assertion.assertion_id)
        failure = None
        if observation is None:
            failure = f"{assertion.assertion_id}: no executable observation"
        else:
            try:
                compare(assertion, observation)
            except ForbiddenHitMismatch as exc:
                failure = str(exc)
        if failure:
            failures.append(failure)
        coverage.append(
            {
                "assertion_id": assertion.assertion_id,
                "forbidden_class": assertion.forbidden_class,
                "source_lifecycle_state": assertion.source_lifecycle_state,
                "source_evidence": assertion.source_evidence,
                "candidate_discovered": assertion.candidate_discovered,
                "admitted": assertion.admitted,
                "context_surfaced": assertion.context_surfaced,
                "downstream_influence": assertion.downstream_influence,
                "expected_refusal": assertion.expected_refusal,
                "passed": failure is None,
            }
        )

    extra = sorted(set(by_id) - {item.assertion_id for item in assertions})
    failures.extend(f"{assertion_id}: executable observation lacks declared assertion" for assertion_id in extra)
    return {
        "assertions_run": [item.assertion_id for item in assertions],
        "forbidden_classes": sorted({item.forbidden_class for item in assertions}),
        "coverage": coverage,
        "failures": failures,
    }


def _proposal(**overrides) -> policy.Proposal:
    base = dict(
        proposal_id="fh:proposal",
        actor_id="agent:planner",
        charter_version="charter:forbidden-hit",
        target_reference="mem:forbidden-hit",
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("evidence:forbidden-hit",),
        tenant_ref=TENANT,
        purpose="forbidden-hit-conformance",
    )
    base.update(overrides)
    return policy.Proposal(**base)


def _recall_observation(
    assertion_id: str,
    adapter: GovernedMemoryAdapter,
    query: str,
    fact_uuid: str,
    context: RecallContext | None = None,
) -> ForbiddenHitObservation:
    result = adapter.governed_recall(query, context)
    candidate = fact_uuid in result.candidates
    admitted = fact_uuid in result.admitted
    # The reference runtime does not surface or permit influence from a memory
    # that failed admission. These remain separate report fields so a future
    # runtime with later-stage gates can report a different blocking stage.
    context_surfaced = admitted
    downstream_influence = context_surfaced
    return ForbiddenHitObservation(
        assertion_id=assertion_id,
        candidate_discovered=candidate,
        admitted=admitted,
        context_surfaced=context_surfaced,
        downstream_influence=downstream_influence,
        refusal=result.refusals.get(fact_uuid, ""),
    )


def _write_refusal_observation(assertion_id: str, refusal: str) -> ForbiddenHitObservation:
    return ForbiddenHitObservation(
        assertion_id=assertion_id,
        candidate_discovered=False,
        admitted=False,
        context_surfaced=False,
        downstream_influence=False,
        refusal=refusal,
    )


def _observations() -> tuple[ForbiddenHitObservation, ...]:
    return (
        _superseded(),
        _tombstoned(),
        _derived_residue(),
        _disputed(),
        _project_scope(),
        _shared_membership(),
        _required_compartment(),
        _rejected_reentry(),
        _stale_authorization(),
    )


def _superseded() -> ForbiddenHitObservation:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    committed = adapter.commit_proposal(_proposal(proposal_id="fh:superseded"), "deploy window Thursday")
    substrate.invalidate_fact(committed.fact_uuid, "2026-02-01T00:00:00Z", "2026-02-01T00:00:00Z")
    return _recall_observation(
        "superseded-current-truth", adapter, "deploy window", committed.fact_uuid
    )


def _tombstoned() -> ForbiddenHitObservation:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    committed = adapter.commit_proposal(_proposal(proposal_id="fh:tombstone"), "deploy window Thursday")
    adapter.governed_delete(
        _proposal(proposal_id="fh:prune", operation="pruning", risk_class="low"),
        committed.fact_uuid,
    )
    return _recall_observation(
        "tombstoned-current-use", adapter, "deploy window", committed.fact_uuid
    )


def _derived_residue() -> ForbiddenHitObservation:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    committed = adapter.commit_proposal(_proposal(proposal_id="fh:source"), "deploy window Thursday")
    derived = Fact(
        uuid="fh:derived-residue",
        fact_text="derived summary deploy window Thursday",
        group_id=TENANT,
        episode_uuids=(committed.fact_uuid,),
        created_at="2026-01-01T00:00:00Z",
    )
    substrate.write_fact(derived)
    adapter.governed_delete(
        _proposal(proposal_id="fh:source-prune", operation="pruning", risk_class="low"),
        committed.fact_uuid,
    )
    return _recall_observation(
        "deleted-source-derived-residue", adapter, "derived summary", derived.uuid
    )


def _disputed() -> ForbiddenHitObservation:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    committed = adapter.commit_proposal(_proposal(proposal_id="fh:disputed"), "deploy window Thursday")
    adapter.mark_disputed(committed.fact_uuid)
    return _recall_observation(
        "disputed-current-use", adapter, "deploy window", committed.fact_uuid
    )


def _project_scope() -> ForbiddenHitObservation:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    committed = adapter.commit_proposal(
        _proposal(
            proposal_id="fh:project",
            isolation_domain_refs=("domain:project",),
            project_ref="project-a",
        ),
        "project deployment secret",
    )
    context = RecallContext(target_domain_refs=("domain:project",), project_ref="project-b")
    return _recall_observation(
        "cross-project-admission", adapter, "project deployment", committed.fact_uuid, context
    )


def _shared_membership() -> ForbiddenHitObservation:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    shared = "domain:shared-security"
    committed = adapter.commit_proposal(
        _proposal(proposal_id="fh:shared", isolation_domain_refs=(shared,)),
        "shared security decision",
    )
    adapter.set_shared_domain_members(shared, ("user:alice",))
    context = RecallContext(target_domain_refs=(shared,), principal_ref="user:bob")
    return _recall_observation(
        "revoked-shared-membership", adapter, "shared security", committed.fact_uuid, context
    )


def _required_compartment() -> ForbiddenHitObservation:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    project = "domain:project"
    secret = "compartment:secret"
    committed = adapter.commit_proposal(
        _proposal(
            proposal_id="fh:compartment",
            isolation_domain_refs=(project, secret),
            required_isolation_domain_refs=(secret,),
        ),
        "compartment protected detail",
    )
    context = RecallContext(target_domain_refs=(project,))
    return _recall_observation(
        "missing-required-compartment", adapter, "compartment protected", committed.fact_uuid, context
    )


def _rejected_reentry() -> ForbiddenHitObservation:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    original = adapter.commit_proposal(
        _proposal(proposal_id="fh:original", target_reference="mem:readmission"),
        "deploy window Thursday",
    )
    correction = _proposal(
        proposal_id="fh:correction",
        target_reference="mem:readmission",
        operation="correction",
        current_strength="promoted",
        proposed_strength="promoted",
        approval_refs=("approval:human",),
        review_satisfied=True,
        state_snapshot="v1",
    )
    corrected = adapter.commit_proposal(correction, "deploy window Friday")
    if not original.committed:
        raise RuntimeError("readmission setup did not commit the original")
    if not corrected.committed:
        # ADR-037 step 4b-2 (entry #24), operator ruling 2026-09-05.
        #
        # The correction used to commit on `review_satisfied=True` plus
        # `approval:human`. That route is gone, and this module has nothing that
        # establishes the proposition under review -- that the deploy window is
        # Friday rather than Thursday. Its executable observations and fixture
        # matrix establish forbidden-hit *lifecycle behaviour*, which is a
        # different proposition; reusing them here would be evidence-purpose
        # laundering.
        #
        # So the correction parks, and the re-entry observation it was setup for
        # is **declared blocked** rather than grandfathered through assertion.
        # The row stays in the matrix, carrying the unmet criterion, so the gap
        # is visible instead of silently absent.
        registry = PendingVerificationRegistry()
        record = registry.park(correction, policy.evaluate(correction))
        unmet = next(
            (c.kind for c in criteria_for(record).unmet if c.kind == CRITERION_GATE),
            criteria_for(record).unmet[0].kind,
        )
        return _write_refusal_observation(
            "rejected-value-reentry",
            f"correction_parked_pending_verification:{unmet}",
        )
    reentry = adapter.commit_proposal(
        _proposal(
            proposal_id="fh:reentry",
            target_reference="mem:readmission",
            state_snapshot="v2",
        ),
        "deploy window Thursday",
    )
    return _write_refusal_observation("rejected-value-reentry", reentry.refusal or "")


def _stale_authorization() -> ForbiddenHitObservation:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    adapter.commit_proposal(
        _proposal(proposal_id="fh:stale-base", target_reference="mem:stale"),
        "current state",
    )
    stale = adapter.commit_proposal(
        _proposal(
            proposal_id="fh:stale-write",
            target_reference="mem:stale",
            state_snapshot="v0",
        ),
        "stale replacement",
    )
    return _write_refusal_observation("stale-authorized-write", stale.refusal or "")
