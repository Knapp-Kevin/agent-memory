# Interoperability Profiles

## Purpose

Conformance levels in [`06-conformance-test-plan.md`](06-conformance-test-plan.md) measure how governed a single implementation is. Interoperability profiles answer a different question: **what may a peer system rely on when it exchanges memory with this implementation?**

Profiles exist so that UOR, EvolveAI, CodeGenome, COREFORGE, and future systems can interoperate without pretending identical implementation details are required. A profile names the smallest set of behaviors, schemas, and adapters a peer may depend on — everything else stays implementation-specific on purpose.

## Profile model

- A profile is a **claim made to peers**, published in the conformance report (`conformance_level` measures maturity; claimed profiles measure reliance surface).
- Profiles are cumulative where stated: each names its prerequisites.
- A system claims a profile only for a declared scope (memory types, tenants, consequence classes). Claims outside the tested scope are not claims.
- Every profile claim must be backed by passing fixtures; a claim without fixture evidence is documentation alignment (Level 0) wearing a costume.

Exchange between systems flows through the adapter contracts of [`34-adapter-contracts.md`](34-adapter-contracts.md). A profile is, concretely, a promise about which adapters a system exposes correctly. System-to-component assignment is tracked in [`05-repo-implementation-map.md`](05-repo-implementation-map.md) and the implementation ownership map ([`39-implementation-ownership-map.md`](39-implementation-ownership-map.md)).

## Profile 1: Identity and provenance

A peer may rely on: stable identity resolution and provenance retention.

**Requirements**

- Memory objects carry stable, non-probabilistic identity where doctrine requires it (ADR-001).
- Provenance survives storage, summarization, and export.
- Similarity is never returned as identity.

**Required schemas and adapters**: `memory-unit.schema.json` (id, provenance, evidence fields); identity adapter and evidence adapter per `34-adapter-contracts.md`.

**Fixture evidence**: `valuable-persistent-memory` (provenance remains attached), plus a summarization-provenance case for peers that exchange summaries.

**Implementation-specific**: hash algorithm and address format, storage layout, resolution service topology — provided the identity contract's determinism guarantee holds at the seam.

## Profile 2: Lifecycle and decay

A peer may rely on: memory it receives carrying a truthful lifecycle state, and transitions being governed.

**Prerequisite**: Profile 1.

**Requirements**

- The 13-state lifecycle of [`02-lifecycle-state-machine.md`](02-lifecycle-state-machine.md) or a declared, mapped subset; proposal and commit remain distinct.
- Decay demotes retrieval priority per policy; pruning leaves tombstones per [`28-retention-deletion-and-tombstones.md`](28-retention-deletion-and-tombstones.md).
- State crossing a seam matches state in the ledger.

**Required schemas and adapters**: `memory-unit.schema.json` (state, decay_profile); lifecycle adapter; `memory-audit-event.schema.json` for transition events.

**Fixture evidence**: `ephemeral-memory`, `pruning-with-audit-preservation`.

**Implementation-specific**: decay curves, timers versus event-driven demotion, storage tiering — provided invalid transitions remain invalid at the seam.

## Profile 3: Calibrated saturation

A peer may rely on: scores it receives meaning what they claim to mean.

**Prerequisite**: Profile 2.

**Requirements**

- Score semantics declared per handoff (`signal_semantics`): probabilistic or ordinal/routing.
- Calibration per [`09-calibration-protocol.md`](09-calibration-protocol.md), with `estimator_version`, `calibration_ref`, and scope of validity attached to consequential scores.
- Trap-class resistance demonstrated; out-of-scope scores flagged, not reused.

**Required schemas and adapters**: `calibration-results.schema.json` and the generated calibration report; scoring adapter.

**Fixture evidence**: `access-spam-junk`, `confidently-wrong-memory`, `threshold-jitter`, `out-of-calibration-scope`, `estimator-disagreement`.

**Implementation-specific**: estimator architecture, feature sets, learning method, score ranges — provided semantics, calibration scope, and uncertainty survive the seam.

## Profile 4: PAMA authority

A peer may rely on: mutations it requests or receives having passed a real authority gate.

**Prerequisite**: Profile 2 (Profile 3 required where scores feed consequential authority).

**Requirements**

- Mutation authority per [`04-governance-and-pama.md`](04-governance-and-pama.md) with outcomes no weaker than the decision table in [`33-pama-decision-table.md`](33-pama-decision-table.md).
- Authority binds to state snapshot and policy version; permitted action sets are closed (blocked actions are absent, and stochastic selection stays inside the set).
- Cross-system requests carry reconstructable actor authority; unresolvable authority fails closed.

**Required schemas and adapters**: `decision-receipt.schema.json`; PAMA adapter; `memory-audit-event.schema.json` for authority decisions.

**Fixture evidence**: `unauthorized-mutation-attempt`, `authority-laundering`, `expired-delegation`, `stochastic-retrieval-policy-envelope`, `concurrent-conflicting-mutation`.

**Implementation-specific**: policy engine, review tooling, approval workflow — provided outcomes, receipts, and closure of the permitted set hold at the seam.

## Profile 5: Certification and crystallization

A peer may rely on: durable memory it receives having been certified, in scope, by an independent gate.

**Prerequisites**: Profiles 3 and 4.

**Requirements**

- Crystallization requires certification (ADR-003); certificates are scoped and bind evidence, policy version, and estimator context.
- Certification is independent of the proposing estimator; revocation and demotion paths exist per [`31-recovery-rollback-and-replay.md`](31-recovery-rollback-and-replay.md).
- A crystallized memory crossing a seam carries its certificate reference.

**Required schemas and adapters**: `memory-unit.schema.json` (certification field), `decision-receipt.schema.json`; certification adapter.

**Fixture evidence**: `certified-durable-memory`, `high-confidence-false-promotion`, plus a revocation case.

**Implementation-specific**: who certifies (human, service, workflow), certificate format internals — provided scope binding and independence hold.

## Profile 6: Cross-system interoperability

A peer may rely on: full governed exchange — memory can move between systems without losing scope, uncertainty, authority, or auditability.

**Prerequisites**: Profiles 1 through 5, plus scope and sensitivity enforcement per [`29-actor-scope-consent-and-tenancy.md`](29-actor-scope-consent-and-tenancy.md) and [`19-privacy-and-sensitivity-classifier.md`](19-privacy-and-sensitivity-classifier.md).

**Requirements**

- The full handoff record of `34-adapter-contracts.md` at every exchange seam; absence-is-absence honored on receipt.
- Scope, tenancy, sensitivity, and dispute state survive export/import; recall admission is governed on the receiving side (relevance is not access).
- Audit events and receipts are exchangeable and reconstructable across the system boundary; deletion propagates to derived and exported copies per retention policy.

**Required schemas and adapters**: all four evidence schemas; runtime memory, correction/dispute, and conformance adapters in addition to the Profile 1–5 set.

**Fixture evidence**: `cross-tenant-relevance-trap`, `unsafe-multi-memory-composition`, `uncertain-sensitivity-before-export`, `deletion-residue`, `policy-estimator-version-drift`, `sleeper-memory-poisoning`.

**Implementation-specific**: transport, serialization framing, discovery, batching — provided the handoff record's semantic content is preserved bit-for-meaning.

## Authority conflict between systems

Interoperating systems each run their own governance. That creates a failure mode no single-system doctrine covers: two systems, each internally compliant, disagreeing about who holds authority over an exchanged memory — both believing they may correct it, certify it, expand its scope, or delete it.

Rules for any exchange at Profile 4 and above:

- **Authority does not transit seams.** A peer's `allow` is evidence that *the peer's* PAMA authorized *its* actor under *its* policy version. It is never this system's `allow`. Every consequential action on received memory re-resolves against the local authority path — the peer's receipt is an input, not a verdict.
- **Ownership is singular and travels with the memory.** The owner principal (per [`29-actor-scope-consent-and-tenancy.md`](29-actor-scope-consent-and-tenancy.md)) is part of the exchanged record. Receiving a copy grants access within scope; it never grants ownership, correction authority, or deletion authority over the origin's record.
- **Competing authority claims fail closed.** If two systems assert conflicting authority over the same memory — both claim ownership, or their policies authorize incompatible mutations — the contested memory is frozen for consequential use in both systems until a governed resolution lands. Resolution is by ownership record and declared precedence, never by whichever system acted first, holds the higher confidence, or has the faster pipeline.
- **Receipts name the authorizing system.** Cross-system decision receipts identify which system's PAMA, which policy version, and which actor authorized each consequence, so an auditor can reconstruct authority per hop — a chain of receipts, not a blended one.
- **Certification does not transfer by default.** A certificate binds the issuing system's certifier, scope, and policy context. A receiving system may *recognize* a peer's certificate as evidence under its own policy; recognition is a local, revocable policy decision, not an automatic import of certified status.

A dedicated cross-system authority-conflict fixture belongs in the fixture backlog (issue #43) alongside the shared-memory cases of [`future/multi-agent-shared-memory-protocol.md`](future/multi-agent-shared-memory-protocol.md).

## Profile claims in the conformance report

A conformance report claiming profiles should record, per profile: claimed scope, fixtures run and passed, known exemptions with expiry, and the doctrine version tested. Use `metric_extensions` and `known_exemptions` in `conformance-report.schema.json` until profile fields are standardized (tracked with the fixture-versioning work in issue #43).

Claiming rules:

```text
claim without fixture evidence        -> invalid
claim outside tested scope            -> invalid
claim with expired exemption          -> invalid
lower profile broken by higher claim  -> both invalid
```

## What profiles do not promise

- A profile is not a quality guarantee; quality metrics live in [`32-memory-quality-metrics.md`](32-memory-quality-metrics.md).
- A profile does not promise identical behavior — stochastic components remain variable by design; the promise is that invariants hold at the seams.
- Two systems claiming Profile 6 may still refuse specific exchanges by policy. Interoperability is capability, not obligation.

## Doctrine

A profile is a promise about seams, not a description of internals.

Peers integrate against the promise. Implementations keep their freedom behind it. The moment a system needs a peer's internal details to exchange memory safely, the profile — not the peer — has failed.
