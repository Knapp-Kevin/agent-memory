# Reference Governed Adapter

A minimal, executable demonstration that the governed path in
[`../docs/programs/runtime-evidence/README.md`](../docs/programs/runtime-evidence/README.md)
can be implemented over a temporal-graph substrate that provides no governance of its own, plus the P4.5 portable evidence, external-checkpoint correlation, TRACE/cMCP action-evidence boundaries, accepted ADR-024 shared-write coordination evidence, proposed ADR-025 durable-decision overwrite evidence, and the first deterministic Governance Context Projection slice.

## What this is not

Read this section before citing anything in this directory.

- **Not a conformance claim.** The emitted report states conformance level 0 and says why. The doctrine fixture corpus is driven through the adapter's authority enforcement, but doc 06 levels are cumulative and this adapter implements neither decay nor calibrated saturation, so levels 2 and 3 are unmet however well enforcement does. Nothing here substantiates a level, a profile, or ADR-020 by itself.
- **Not a reference implementation of Agent Memory.** It implements the narrow slices needed to exercise governance paths, portable evidence, shared-write coordination, durable-decision overwrite authority, and bounded interoperability projections, and nothing else.
- **Not an endorsement of any substrate, trust infrastructure, governance consumer, distributed-lock implementation, or approval service.** The model reproduces one mapped substrate's verified semantics so the tests have something realistic to push against. The Ed25519 profile proves an evidence boundary, not a universal PKI. The ADR-024 coordinator proves a pre-write coordination boundary, not a universal lock algorithm. The ADR-025 slice proves proposal/authority/PAMA/supersession separation, not one universal human-approval workflow. Agent Manifest, TRACE, cMCP, DashClaw, and Microsoft Agent Governance Toolkit are comparators/interoperability surfaces, not doctrine dependencies.

## What it does demonstrate

Several things, at different evidential weight.

**Against a real substrate (runtime evidence).** Seven governance paths execute against `graphiti-core` 0.29.3 backed by an embedded graph database, with no LLM, no embedder, no API key and no server. Facts are written through the substrate's no-LLM direct-write path, superseded, pruned, physically deleted, and refused across partitions, all under the authority gate.

**Against a substrate model (precondition).** Twelve further paths run against an in-memory model, covering cases the live binding does not reach: stale authorization, self-approval, undeclared derived residue, and version-drift separation.

**Against the doctrine fixture corpus.** All repository fixtures are driven through the adapter's own enforcement rule where they declare an authority envelope. This matters because the corpus was authored to describe doctrine, not to satisfy this implementation, so agreement between them is evidence rather than a suite agreeing with itself. The checker is mutation-tested in `tests/test_fixture_corpus.py`: deliberately corrupted envelopes must be detected, because a conformance check that cannot fail is decoration.

**Against accepted ADR-024 shared-write coordination.** A deterministic reference coordinator binds actor, task, scope, target, mutation class, authority basis, state snapshot, and lease validity before a shared durable write may reach the governed adapter. Fixtures and unit tests exercise successful coordination, competing claims, stale state, expired leases, unauthorized claims, claim/proposal mismatch, and the critical negative path where a valid claim still cannot override a PAMA `block`. Successful and failed claim outcomes are emitted as schema-valid audit events.

**Against proposed ADR-025 durable-decision overwrite authority.** An append-oriented reference registry keeps agent proposal, authority grant, PAMA evaluation, and committed supersession as distinct states. A proposal alone does not change current decision state. Prior human-confirmed and high/critical-risk overwrite cases require an exact human-confirmation grant in the current reference profile; low/medium non-human-confirmed decisions have a bounded delegated-policy positive control. Tests reject agent consensus, stale proposals, revoked/expired/not-yet-valid grants, proposal/target/scope/mutation/actor/risk mismatches, self-approval, missing authority linkage on the replacement, and the critical case where a valid human grant still cannot override a PAMA `block`. Successful overwrite preserves the prior decision and appends replacement, receipt, and supersession evidence.

**Against the P4.5a portable-evidence contract.** A content-free projection of a canonical decision receipt is signed with Ed25519 and verified using only the configured public trust key. The verifier independently checks receipt, runtime-action, policy, authority-state, temporal, and isolation-domain bindings while preserving governance disposition, runtime execution, and lifecycle satisfaction as separate outcomes. Adversarial vectors exercise tampering, replay, stale authority, wrong domains, key rotation, revocation timing, detached receipt verification, and valid deletion with residual lifecycle state.

**Against the P4.5b Agent Manifest comparator.** CI installs `agent-manifest==0.11.2`, pinned to release commit `9d26ac84461e829dba8ff97ca35748eeb874debe`, and executes its own v0.2 memory checkpoint/delta implementation. Agent Memory content-addresses the checkpoint tuple and binds it through the canonical receipt and P4.5a state references. The executed upstream log appends a real `DEL`; the resulting accepted checkpoint is exercised once with lifecycle `residual` and once with lifecycle `satisfied`, proving checkpoint integrity does not manufacture forgetting. Because a checkpoint root alone does not disclose the appended operation class, the portable correlation artifact deliberately carries signed Agent Memory `memory_action` rather than an unproven Agent Manifest `operation_kind` claim.

**Against the P4.5c TRACE/cMCP action-evidence surface.** The reference adapter wraps P4.5a evidence in the existing six-field cMCP `external_execution_evidence` envelope, hashes the detached payload with RFC 8785/JCS, and preserves `linked_call_id` as a separate audit identity from Agent Memory `action_ref`. Local vectors exercise TRACE-style receipt outcomes, wrong-call and wrong-action replay, payload/signature tampering, missing trust, domain mismatch, and lifecycle separation. A second CI path creates an isolated environment with `cmcp-runtime==0.4.0` and calls the released `cmcp_verify.verify_audit_bundle()` verifier against the emitted envelope.

**Against the proposed ADR-029 Governance Context Projection boundary.** A deterministic reference builder converts explicit precedent inputs into a vendor-neutral projection containing source-memory references, material conditions, polarity, validity, provenance, outcomes, scope, and derivation metadata. The builder does not emit consumer verdicts, standing permission, or risk scores. Tests exercise material matches, misleading near-matches, negative precedent, unknown conditions, deterministic rebuild, and provenance laundering where a policy-generated outcome tries to impersonate independent human adjudication.

The common point is that the governance layer is load-bearing. The substrate model is deliberately permissive in exactly the ways the mapping verified: identity is opaque rather than content-derived, the partition filter defaults to unfiltered, deletion is physical with no tombstone, and **no operation checks authority**. Several tests assert both halves: that the substrate *would* misbehave, and that the adapter refuses anyway. A test that only checked the adapter would not prove the governance was doing any work.

The shared-write claim boundary adds a related separation: coordination may determine which writer gets to attempt a shared mutation, but PAMA still determines what durable consequence is permitted.

The durable-decision overwrite boundary adds another: an approval record may satisfy a decision-specific authority precondition, but it is not a bypass token. PAMA may remain stricter and the prior decision stays historical after successful supersession.

The Governance Context Projection adds a complementary boundary: remembered context can be useful to an external policy system without becoming permission merely because it crossed an adapter seam.

## Layout

`agentmem_ref` is seven subpackages in dependency order -- a module imports only from its own layer or an earlier one, and `reference/tests/test_package_layout.py` enforces that order as read from `scripts/restructure_package.py`, the script that produced the layout.

```text
reference/
  requirements.txt                   pinned main reference-validation dependencies
  agentmem_ref/
    _paths.py                        PACKAGE_ROOT / REFERENCE_ROOT / REPO_ROOT, computed once
    core/                            PAMA evaluator (policy), receipts + schema validation,
                                     evidence qualification, verification, parking, resumption,
                                     readmission, contextual recall, governance projection,
                                     portable evidence
    state/                           canonical state (substrate, graphiti_driver) and derived
                                     state (projections, residue, visibility)
    contracts/                       capability contract, provider qualification, substitution,
                                     fallback, failure probes
    runtime/                         the governed adapter, restart-safe and configured runtimes,
                                     composition, discovery, doctor, cli, write_claims,
                                     projection_governance, scope/revocation
    memory/                          governed memory kinds and their evidence: cognitive, epistemic,
                                     predictive, procedural, decision_overwrite, structural,
                                     crossing, interchange, temporal, precedent, maintenance,
                                     dashclaw, external/approval/enforcement/telemetry evidence
    crg/                             Agent Memory's Code Reality Graph; CodeGenome is its
                                     first-party implementation profile (ADR-035, ADR-036)
    harness/                         characterization harnesses, depth probes, comparators,
                                     benchmarks -- leaves
    <module>.py                      compatibility alias: `agentmem_ref.policy is
                                     agentmem_ref.core.policy` (every old path still works)
  tests/                              model, claim, decision, projection, real-substrate, and interoperability paths
  run_trace_cmcp_comparator.py        isolated released cMCP verifier execution
  run_conformance.py
```

The reference implementation is **not** standard-library only. Its main validation dependency set is declared and pinned in [`requirements.txt`](requirements.txt): `jsonschema`, `cryptography`, `agent-manifest`, `agentrust-trace`, and `rfc8785`. P4.5b uses Agent Manifest as a test-only comparator and does not import it from production reference modules. P4.5c uses TRACE/JCS dependencies in the main reference environment, while `cmcp-runtime==0.4.0` is kept in an isolated comparator environment because its dependency line differs. The shared-write coordinator, durable-decision registry, and Governance Context Projection builder add no dependency beyond the existing reference environment.

The low-cost repository validators intentionally keep a different dependency posture: fixture, doctrine-boundary, link, visual, and calibration tooling stays standard-library only where documented, with `jsonschema` as the explicit schema-validation exception. See [`../CONTRIBUTING.md`](../CONTRIBUTING.md). CI installs the main reference validation environment from the same checked-in manifest used by contributors rather than maintaining a second hidden pin list.

## Running it

```bash
# reference model and interoperability paths
python -m pip install -r reference/requirements.txt
python -m unittest discover -s reference/tests -t reference

# TRACE/cMCP comparator in a dependency-isolated environment
python -m venv /tmp/agent-memory-p45c-cmcp
/tmp/agent-memory-p45c-cmcp/bin/python -m pip install \
  cmcp-runtime==0.4.0 \
  agentrust-trace==0.9.0 \
  agent-manifest==0.11.2 \
  rfc8785==0.1.4
PYTHONPATH=reference \
  /tmp/agent-memory-p45c-cmcp/bin/python reference/run_trace_cmcp_comparator.py

# stochastic containment sweep with an explicit trial count
python reference/run_conformance.py --trials 500

# add the real substrate; the substrate tests skip cleanly without it
pip install graphiti-core kuzu
python -m unittest discover -s reference/tests -t reference
python reference/run_conformance.py
```

Runs are deterministic where the contract requires determinism: identifiers are counter-based and the clock is injected, so repeated governed-adapter runs produce identical receipts and identical reports. Shared-write claim tests inject claim time and exact state versions, so lease/state outcomes reproduce exactly. Durable-decision overwrite tests inject exact decision state and grant time, so stale/expiry/authority outcomes reproduce exactly. The Governance Context Projection builder is deterministic for the same explicit inputs and source snapshot. Stochastic selection is seeded per trial, so it varies across trials and reproduces exactly for a given seed. Ed25519 signatures are deterministic for a fixed private key and canonical payload. P4.5b and P4.5c pin external package versions and upstream release commits so comparator drift is explicit rather than accidental.

## The governed path

```text
evidence -> proposal -> authority envelope -> permitted action set
         -> selected action -> substrate mutation -> decision receipt
         -> retrieval candidate -> governed admission -> active context
```

The adapter supplies what the substrate cannot: an authority gate before every write, always-explicit scope filtering, external lifecycle state, tombstones, and receipts. Artifacts are emitted against schemas already canonical in this repository rather than shapes invented beside the implementation: `pama-decision`, `decision-receipt`, `memory-audit-event`, `conformance-report`, P4.5a `portable-governance-evidence`, P4.5b `agent-manifest-memory-correlation`, P4.5c `trace-action-evidence-bundle`, and proposed ADR-029 `governance-context-projection`.

The accepted ADR-024 shared-write path is an additional precondition for shared durable mutation:

```text
shared write intent
  -> pre-write claim / lease
  -> conflict / expiry / state / binding validation
  -> ordinary governed adapter / PAMA
  -> durable mutation or refusal
  -> claim + decision audit evidence
```

The reference coordinator implements one exact-scope lease mechanism. It does not replace the ordinary governed path or make the lease itself authoritative.

The proposed ADR-025 durable-decision path is separate from ordinary record correction:

```text
overwrite proposal
  -> exact decision-specific authority validation
  -> PAMA
  -> append replacement + supersession evidence
     OR refusal with current decision unchanged
```

The reference registry demonstrates this boundary in memory. It does not implement a production approval service, distributed decision store, identity provider, or user interface.

The governance-consumer path is separate:

```text
canonical memory / precedent
  -> governed selection
  -> Governance Context Projection
  -> consumer-specific adapter
  -> external governance decision
```

The reference module currently implements only the deterministic projection builder. It does not implement a DashClaw or AGT/ACS adapter and does not claim those integrations exist.

## Paths exercised

| Path | Holds |
|---|---|
| positive commit and reconstruction | full chain executes; receipt reconstructs estimate, authority, selection, consequence; events causally linked |
| shared-write valid claim | current authorized claim acquires coordination and reaches ordinary PAMA before one durable write commits |
| shared-write conflict | a second active claim for the same scope/target is rejected before durable mutation |
| shared-write stale/expired/unauthorized | stale state, expired lease, or unresolved claim authority fails closed with no substrate write |
| shared-write PAMA non-override | a valid coordination claim cannot loosen a later PAMA `block`; no durable write occurs |
| durable-decision proposal only | agent proposal is retained as evidence while the current durable decision remains active |
| durable-decision human confirmation | exact current human grant plus PAMA appends replacement and supersession evidence while preserving prior history |
| durable-decision bounded delegation | low-risk non-human-confirmed decision may be superseded only inside the exact delegated grant bounds |
| durable-decision collusion/stale/authority failures | agent consensus, stale state, revoked/expired/mismatched/self-approved authority all fail without supersession |
| durable-decision PAMA non-override | a valid human grant cannot loosen an independent PAMA `block` |
| PAMA decision operation versioning | existing operation records stay 1.0.0; `decision_overwrite` emits 1.1.0 because it expands a closed enum |
| high-confidence false promotion | confidence 0.99 and 0.01 produce an identical envelope; confidence has no route to authority |
| cross-tenant relevance | substrate returns the foreign record unfiltered; adapter never reaches that default |
| prohibited action selectability | a governance-class mutation is absent from the permitted set and cannot be selected |
| stale authorization | authority resolved against an older state does not commit |
| self-approval of authority | blocked, with no permitted actions at all |
| unresolved actor authority | fails closed |
| superseded memory | remains a candidate, refused for current use, not erased |
| irreversible deletion | cannot commit autonomously; the substrate would have executed it |
| pruning | tombstones and removes from recall while content stays recoverable |
| undeclared derived residue | a projection nobody declared is detected after removal |
| version drift | policy version and estimator versions stay separable in the receipt |
| fixture corpus | doctrine fixtures pass envelope enforcement where applicable; the checker is mutation-tested |
| stochastic containment | hundreds of sampled trials never escape the permitted set, and the selector demonstrably varies |
| hostile selector | a selector returning a prohibited action is contained by the adapter and the violation recorded |
| derived-state freshness | stale and residual are computed from a recorded basis, never set by a flag |
| correction propagation | dependents go stale; content-bearing projections supersede without erasing the prior version |
| transitive purge | the whole derivation closure is reached, and a deliberate one-hop purge is caught by the sweep |
| undeclared residue | the four-way partition holds, with the undeclared cell empty as a hard gate |
| rebuild authority | estimator-mediated rebuild is refused without an authority decision; deterministic reproducible rebuild is categorical |
| portable receipt binding | Ed25519 evidence binds the canonical receipt reference, action, policy, authority state, time, and optional isolation domains |
| portable negative outcomes | authentic denial, unauthorized execution, and residual lifecycle state remain distinct machine-readable outcomes |
| portable replay and trust failures | wrong action/domain/state, signature tampering, unknown issuer, rotation, and revocation timing are exercised |
| Agent Manifest normative root | the pinned upstream implementation reproduces the v0.2 KV memory-root vector |
| Agent Manifest deletion-vector correlation | the upstream verifier accepts an RFC 9162 checkpoint built from a log whose appended test operation is `DEL`; canonical receipt and portable state refs bind the checkpoint |
| DEL versus forgetting | that accepted checkpoint remains compatible with either residual or satisfied Agent Memory lifecycle evidence |
| external negative checkpoint outcome | invalid consistency proof yields upstream `drift` while the correlation remains a valid record of a rejected delta |
| TRACE/cMCP envelope compatibility | emitted evidence uses the existing six-field external-execution envelope and the released cMCP verifier accepts it |
| TRACE call replay | released cMCP verifier rejects a receipt whose `linked_call_id` does not match the audit call |
| Agent Memory action replay | local verifier separately rejects a detached action reference that does not match the P4.5a signed `action_ref` |
| TRACE negative action outcome | a correctly bound external `rejected` receipt remains valid negative evidence rather than malformed evidence |
| TRACE versus lifecycle | accepted action evidence remains compatible with both residual and satisfied Agent Memory lifecycle evidence |
| TRACE trust failure | local TRACE-style classification reports unknown issuer as unverified; configured cMCP external-key verification fails closed on the same missing trust anchor |
| governance precedent material match | prior human decision context is projected with explicit matching material conditions but no final permission |
| governance precedent near-match | superficially similar positive precedent remains a material mismatch when protected target, force, or CI conditions differ |
| negative governance precedent | cautionary/contradictory precedent remains separately addressable rather than being erased by positive frequency |
| adjudication provenance | policy/runtime-derived outcomes cannot claim independent human adjudication |
| governance projection rebuild | identical deterministic inputs produce identical derived projection output |

## Known limitations

Stated rather than left to be discovered:

1. Corpus coverage is envelope enforcement, not full scenario execution: decay, calibrated saturation, retrieval ranking, and most lifecycle transitions are outside this adapter and are declared as exemptions in the report rather than silently skipped.
2. Retrieval ranking is lexical overlap, not the substrate's hybrid search, because hybrid ranking needs an embedder. Recall quality is not measured.
3. The policy implements the subset of the decision table these paths need, not the whole table.
4. The substrate binding uses an embedded backend that is deprecated upstream, chosen because it needs no server. No governance behavior under test depends on the backend choice.
5. Node topology is simplified to one edge per fact. This exercises governance invariants, not knowledge modelling.
6. Derived-state governance operates on an adapter-owned sidecar. The design spike names this as the obvious home for substrates that cannot store a projection declaration, and notes that it reintroduces the consistency problem one level up. That trade is accepted here rather than solved.
7. Residue is measured over declared projections. State that was never declared is outside the sweep's reach by construction, which is why the declaration surface is the load-bearing part rather than the traversal.
8. The P4.5a trust profile assumes configured Ed25519 public trust keys. Production key custody, trust discovery, certificates, and external revocation infrastructure remain outside this slice.
9. P4.5b intentionally imports Agent Manifest private checkpoint modules only in its pinned comparator tests because the upstream implementation issue and specification surface those exact functions. This is not a stable production API commitment and is isolated from Agent Memory runtime code.
10. An Agent Manifest checkpoint root proves the bound log state but does not independently reveal the semantic class of a new operation. P4.5b demonstrates a real upstream `DEL` through executed test input; a compact content-free third-party proof of operation class would require additional upstream operation/inclusion evidence and is not invented here.
11. P4.5c binds Agent Memory action evidence into TRACE/cMCP receipt infrastructure; it does not prove a physical or business outcome occurred and does not make TRACE a PAMA interpreter.
12. The released cMCP 0.4.0 dependency graph is intentionally isolated from the main evidence environment because its AGT dependency line resolves a lower cryptography range. This is comparator containment, not a production dependency recommendation.
13. P4.5c does not demonstrate hardware attestation of the Agent Memory process, production trust-anchor discovery, or upstream Community/Verified integration acceptance.
14. Governance Context Projection V0.1 uses explicit deterministic material-condition comparison. It does not implement semantic similarity, learned precedent ranking, approval suppression, standing grants, DashClaw integration, AGT/ACS integration, or evidence that reduced approval friction is safe in production.
15. The ADR-024 `SharedWriteCoordinator` is an in-process exact-scope reference lease. It does not prove distributed serializability, consensus, deadlock freedom, cross-process lock durability, or one normative coordination algorithm. Those remain implementation-specific obligations.
16. The proposed ADR-025 `DurableDecisionRegistry` is an in-memory evidence harness. It does not prove a production human-approval channel, identity proofing, distributed consistency, approval UX, or that every implementation must use the reference profile's exact low/medium versus high/critical authority split. The slice proves the authority-separation invariants and named negative paths while ADR-025 remains Proposed pending a separate maturity decision.