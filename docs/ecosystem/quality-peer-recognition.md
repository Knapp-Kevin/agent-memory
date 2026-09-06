# Quality-peer ecosystem recognition

Agent Memory should visibly recognize excellent independent technical work even when that work is not a dependency, formal influence, or implementation requirement.

The operating principle is:

> **Good work should be visible. Credit should be generous. Boundaries should remain precise.**

This policy complements [`../40-aligned-projects-and-intellectual-lineage.md`](../40-aligned-projects-and-intellectual-lineage.md). The aligned-project document explains intellectual lineage, interoperability, evidence, enforcement, and implementation relationships. This document adds a separate reason a project may deserve visibility: **it is a genuinely useful, well-executed product, platform, repository, specification, or technical system that practitioners in this ecosystem should know exists.**

## Recognition classes

Use the narrowest accurate classification. More than one may apply.

| Classification | Meaning |
|---|---|
| **Quality peer** | Independent work judged technically useful enough to highlight on its own merits. |
| **Intellectual lineage** | The work materially shaped an Agent Memory question or distinction. |
| **Comparator** | Agent Memory uses the system to challenge or validate a generic contract. |
| **Reference substrate** | Agent Memory has executed bounded doctrine against the system. |
| **Interoperability target** | A defined bidirectional or one-way exchange boundary is useful. |
| **Policy / enforcement peer** | The system evaluates or enforces governance outside canonical Agent Memory semantics. |
| **Evidence / attestation peer** | The system can produce or verify evidence useful to Agent Memory. |
| **Runtime / framework peer** | The system provides execution, lifecycle, checkpoint, orchestration, or integration surfaces. |
| **Research candidate** | Evidence suggests value, but the relationship is not mature enough for a stronger label. |

Recognition is deliberately not binary. A project can move among these classifications as evidence changes.

## Recognition is not adoption

```text
quality recognition
!= dependency
!= endorsement
!= sponsorship
!= formal partnership
!= conformance
!= architectural authority
```

A highlighted project does not gain authority over Agent Memory doctrine. Agent Memory does not gain authority over the highlighted project. A useful external policy decision, identity proof, attestation, trace, framework checkpoint, or security finding still enters through the normal Agent Memory evidence, scope, lifecycle, privacy, and authority boundaries.

## What a highlighted entry must answer

Every quality-peer entry should state, as applicable:

```text
project / product
primary repository or specification
what it does unusually well
why practitioners may care
relationship to Agent Memory
verified implementation / comparator status
version or maturity caveats
license / source-rights posture
what is explicitly not claimed
```

Do not use popularity, social-media attention, or catalog inclusion as a substitute for technical evidence.

## Current highlighted set

### UOR Foundation / UOR Framework

**Classification:** quality peer / intellectual lineage / deterministic-identity comparator

UOR work on deterministic object reference, content-addressed identity, resolution state, and formally described object spaces remains a useful adjacent foundation. Agent Memory carries forward the separation between **exact identity** and **memory governance** while remaining language- and implementation-neutral.

Primary repository: <https://github.com/UOR-Foundation/UOR-Framework>

See the fuller lineage record in [`../40-aligned-projects-and-intellectual-lineage.md`](../40-aligned-projects-and-intellectual-lineage.md).

### DashClaw

**Classification:** quality peer / interoperability target / enforcement peer / comparator

DashClaw is valuable because it treats the pre-execution governance seam as a real runtime concern: interception, risk/policy decision, approval, liveness, and evidence are distinct operational responsibilities. That makes it a useful parallel system for Agent Memory governance projection and execution-evidence boundaries.

Primary repository: <https://github.com/ucsandman/DashClaw>

Recognition does not imply that DashClaw has adopted Agent Memory or that Agent Memory requires DashClaw.

### Microsoft Agent Governance Toolkit

**Classification:** quality peer / policy and enforcement peer / interoperability target

Microsoft Agent Governance Toolkit provides a substantial open governance surface around deterministic policy, identity, audit, and runtime-enforceable controls. Its value to Agent Memory is primarily at the boundary between memory-specific governance and broader agent-runtime governance.

Primary repository: <https://github.com/microsoft/agent-governance-toolkit>

Agent Memory keeps AGT-specific vocabulary outside the canonical memory schema.

### AgentTrust / TRACE

**Classification:** quality peer / evidence and attestation peer / comparator

TRACE is an open specification and implementation ecosystem for cryptographically bound AI-agent governance evidence. Its current public specification describes signed records that bind runtime, policy, environment, data class, and tool information, together with verification and conformance surfaces.

Primary repository: <https://github.com/agentrust-io/trace-spec>

The project currently identifies TRACE v0.2 as a developer-preview specification with a conformance test suite. Agent Memory already uses a pinned TRACE package as a bounded evidence comparator. Verified identity or attestation remains evidence, not Agent Memory authority or semantic correctness.

### Open Policy Agent

**Classification:** quality peer / validated real policy comparator / external decision peer

OPA is a mature general-purpose policy engine and a strong reference host for testing whether Agent Memory can project minimized action context into an external policy decision without importing Rego or OPA-specific ontology into canonical memory semantics.

Primary repository: <https://github.com/open-policy-agent/opa>

Agent Memory has executed its generic monotonic policy-composition contract against pinned OPA v1.19.0. The surviving boundary is intentionally narrow:

```text
OPA decision may tighten an Agent Memory consequence
OPA allow cannot loosen a stricter Agent Memory consequence
OPA decision != execution witness
```

### Cedar

**Classification:** quality peer / validated authorization-policy comparator / external decision peer

Cedar is a purpose-built authorization policy language and engine with explicit principal, action, resource, context, permit, forbid, and determining-policy semantics. That model is materially different from OPA and provides a useful second-host test for Agent Memory's vendor-neutral external-policy seam.

Primary repository: <https://github.com/cedar-policy/cedar>

Agent Memory has now executed the same generic monotonic policy-composition boundary against Cedar v4.12.0, exact source commit `fdcbaed32bdb8c8d13e4eaf2b58db5555e9fb8c5`, through #216 / PR #219.

The proof required no Cedar-specific canonical composition fields. Policy artifact digest, request digest, Cedar source identity, and determining policy IDs remain adapter evidence. Cedar ALLOW/DENY remains policy-decision evidence, not approval, execution, or enforcement evidence.

### Cedarling

**Classification:** quality peer / research candidate / embedded authorization and deployment peer

Cedarling, maintained in the Janssen Project, wraps Cedar in a local authorization service with additional deployment, identity, policy-store, and evidence capabilities.

Primary repository: <https://github.com/JanssenProject/jans/tree/main/jans-cedarling>

Current stable research pin:

- Janssen / Cedarling `v2.3.0`
- release commit `f7c6e34be6ac8d585a9d7b6f7a12921b440b495b`
- Cedarling package version `2.3.0`
- embedded `cedar-policy = 4.11.2`

That embedded Cedar version is **not** the same as Agent Memory's direct Cedar v4.12.0 comparator target, so the two evidence lines remain separate.

Primary v2.3.0 documentation confirms useful Cedarling responsibilities beyond raw Cedar evaluation:

- local, directory, archive, JSON/YAML, HTTPS, and Jans Lock-backed policy-store loading;
- policy-store identity and version metadata;
- trusted-issuer configuration;
- JWT / multi-issuer validation and token-to-Cedar context mapping;
- unsigned authorization for callers that already own authentication;
- Decision/System/Metric logs with request, PDP, policy-store, diagnostics, action/resource, and decision correlation;
- an OPA plugin that performs Cedar-based authorization in OPA workflows;
- AuthZen metadata and access-evaluation endpoints through that OPA/Cedarling integration.

That makes Cedarling particularly interesting as a deployment and identity-rich PDP bridge between policy ecosystems Agent Memory already evaluates independently. It does not need to replace Cedar or OPA to be valuable.

Issue #217 tracks the bounded Cedarling research. Agent Memory has not adopted Cedarling as a dependency or policy store.

## Addition and maintenance rule

A project should enter this list when current primary evidence supports at least one of these:

1. unusually useful technical quality for practitioners in the ecosystem;
2. material intellectual influence;
3. a real comparator or implementation proof;
4. a meaningful interoperability, policy, enforcement, identity, evidence, observability, framework, or security boundary;
5. a concrete challenge that improved Agent Memory doctrine or conformance.

Projects should be updated, reclassified, or removed when evidence changes. A quality-peer page should not become an immortal graveyard of tools that were interesting for six weeks in 2026.

## Source-rights and independence

The default relationship is link + attribution + independent synthesis. External code, prose, diagrams, schemas, screenshots, logos, and brand assets are not copied merely for recognition.

See [`../SOURCE_RIGHTS_POLICY.md`](../SOURCE_RIGHTS_POLICY.md) and [`../40-aligned-projects-and-intellectual-lineage.md`](../40-aligned-projects-and-intellectual-lineage.md).
