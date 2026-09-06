# Aligned Projects and Intellectual Lineage

Agent Memory is independent, but it is not intellectually isolated.

Good technical work should make it easy to see **who influenced what**, which ideas were challenged or strengthened by other developers, and where an external project provides a real implementation, benchmark, enforcement, evidence, or interoperability surface.

The rule is simple:

> **Be generous with credit and precise about boundaries.**

## What recognition means

Agent Memory uses explicit relationship labels instead of a generic “partners” wall.

| Relationship | What it means |
|---|---|
| **Informed by / intellectual lineage** | A project materially shaped a question, distinction, mechanism, or design direction. |
| **Conceptually aligned** | Independent projects share a useful architectural principle. |
| **Reference substrate** | Agent Memory has mapped or executed doctrine against the system. |
| **Implementation mapping** | Inspected evidence supports a bounded Agent Memory implementation role. |
| **Comparator** | The project provides a useful architecture or behavior to test adversarially. |
| **Interoperability target** | The projects may exchange evidence, state, policy signals, or contracts across a defined boundary. |
| **Enforcement peer** | A separate runtime may further restrict Agent Memory-permitted consequences. |
| **Evidence peer** | A separate system can attest to or verify evidence of Agent Memory decisions. |
| **Formal partner** | A documented organizational partnership actually exists. |

Recognition does **not** automatically imply dependency, endorsement, sponsorship, joint authorship, or transfer of intellectual-property ownership.

## Licensing posture

The default acknowledgement pattern is:

```text
link
+ attribution
+ independent synthesis
```

Agent Memory does not copy another project's prose, diagrams, code, schemas, screenshots, or brand assets merely to celebrate the work.

When reuse is actually valuable, the applicable license or permission must be verified and its obligations preserved. A repository license also does not automatically apply to third-party issue comments, discussion posts, uploaded attachments, logos, or linked papers.

The canonical policy is **[Aligned Projects and Intellectual Lineage](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/40-aligned-projects-and-intellectual-lineage.md)** together with the **[Source Rights and Reuse Policy](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/SOURCE_RIGHTS_POLICY.md)**.

---

## UOR Foundation

**Relationship:** intellectual lineage / conceptually aligned foundation / optional identity interoperability profile

Agent Memory is an independent project, but work from the **[UOR Foundation](https://github.com/UOR-Foundation/UOR-Framework)** on deterministic object reference, content-addressed identity, explicit resolution state, formally described object spaces, and replayable derivation materially informed parts of Agent Memory's architectural thinking.

The most useful inherited distinction is not a package dependency. It is a boundary:

```text
IDENTITY
What object is this?
Can it be referred to exactly?

        !=

MEMORY GOVERNANCE
Should it persist?
Who may recall it?
What may it influence?
When may it change or disappear?
```

Agent Memory carries that distinction forward as architecture while remaining implementation-neutral about the exact identity mechanism.

When UOR is used, it is a strong candidate for deterministic identity and exact addressability. Another exact-identity mechanism may be used if it preserves the same separation.

### Temporal evolution of the relationship

ADR-031 gives that identity boundary a concrete temporal use.

An Agent Memory temporal commitment can use an optional UOR-Addr content reference so different runtimes can agree on the **exact temporal object** being attested or projected.

```text
TemporalCommitment
  -> exact canonical content
  -> optional UOR-Addr reference
  -> signer / witness / currentness evidence remain separate
```

This is stronger than merely saying “UOR inspired identity.” It is now an executable interoperability profile for exact temporal-object addressing.

The boundary remains strict:

```text
UOR identity
!= truth
!= signer trust
!= witnessed time
!= currentness
!= PAMA authority
```

Current UOR `DerivationTrace` concepts are also useful comparison material for ordered replayable derivation, but Agent Memory does not infer a signing or trust authority from those concepts.

See **[Temporal Memory Architecture](Temporal-Memory-Architecture)** and **[Cryptographic Temporal Commitments](Cryptographic-Temporal-Commitments)**.

### Research lineage

**[UOR Framework issue #2](https://github.com/UOR-Foundation/UOR-Framework/issues/2)**, opened by Kevin R. Knapp, explored whether UOR resolution and saturation primitives could inform memory decay, crystallization, conflict-driven reheating, and exact-address transitions.

That public discussion became part of the research lineage behind Agent Memory's treatment of saturation, decay, crystallization, calibration, and the separation between identity and lifecycle. The issue also contains material third-party contributions, which retain their own provenance and rights posture.

### License boundary

The UOR Framework repository is MIT-licensed. Agent Memory is Apache-2.0 licensed.

This acknowledgement is citation and independent synthesis. It does not incorporate UOR code, generated ontology artifacts, diagrams, or distinctive documentation expression into Agent Memory.

> **Independence:** Agent Memory is not affiliated with, endorsed by, sponsored by, or formally partnered with the UOR Foundation unless a separate public agreement says otherwise.

---

## Dogwood

**Relationship:** temporal-policy peer / interoperability target / exact-source comparator

**[Dogwood](https://github.com/dogwood-policy/dogwood)** is a Cedar-derived governance language for evaluating temporal policy over bounded event history.

Dogwood materially sharpened an architectural question that ordinary authorization comparators do not answer:

> **What may policy conclude from a bounded history of prior events?**

The resulting Agent Memory relationship is compositional rather than adoptive:

```text
Agent Memory canonical history/currentness
  -> versioned governed temporal projection
  -> compatibility/currentness gate
  -> Dogwood event trace + temporal policy
  -> policy-decision evidence
  -> Agent Memory evidence boundary
```

Agent Memory can enrich the projected temporal view with exact historical identity, lifecycle currentness, scope, schema version, and bounded external evidence without requiring Dogwood to become the canonical memory system.

Dogwood contributes specialized temporal-policy semantics without requiring Agent Memory core to become a temporal-policy language.

The relationship is intentionally bidirectional: Dogwood can consume governed memory context, and Dogwood's resulting policy decision can later become evidence inside Agent Memory through normal provenance and governance.

The boundaries remain strict:

```text
Agent Memory canonical history != Dogwood temporal trace
Dogwood temporal match != current memory truth
Dogwood ALLOW != human approval
Dogwood policy result != execution evidence
```

Dogwood's temporal horizons, event schemas, provider/context semantics, and pin/partition behavior also provide useful failure cases for Agent Memory's versioned compatibility gate.

The current public comparator is pinned to source commit `c6237c88099b3f492ecc5fcee42df06a19224b97`. The public repository is treated as a reference interpreter evidence surface, not as a production dependency.

See **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)** and **[Temporal Memory Architecture](Temporal-Memory-Architecture)**.

> **Independence:** Dogwood and Agent Memory are independent projects. This recognition does not imply adoption, sponsorship, endorsement, or a formal partnership.

---

## Cedar and Cedarling

**Relationship:** authorization comparator / embedded policy peer / interoperability target

**[Cedar](https://github.com/cedar-policy/cedar)** provides a typed authorization model centered on principal, action, resource, context, policies, and an application schema.

**[Cedarling](https://github.com/JanssenProject/jans/tree/main/jans-cedarling)** provides a deployable embedded Cedar policy-decision surface with identity handling, policy-store context, dynamic context data, and decision logging.

These systems helped make another Agent Memory distinction explicit:

```text
memory-derived context can be validly serialized
!=
that context is semantically current for the policy consumer
```

Accepted ADR-030 therefore requires a versioned compatibility/currentness evaluation before a memory-derived projection is treated as current policy input.

Cedar and Cedarling can consume current Agent Memory-derived context without becoming the memory lifecycle authority. Their policy decisions can tighten downstream behavior but cannot silently widen a PAMA consequence Agent Memory denied.

See **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)**.

> **Independence:** Cedar, Cedarling, and Agent Memory remain independent projects unless a separate public agreement states otherwise.

---

## DashClaw

**Relationship:** interoperability target / enforcement peer / comparator

**[DashClaw](https://github.com/ucsandman/DashClaw)** is an independent governance runtime focused on intercepting agent tool actions before execution, evaluating risk/policy, routing dangerous actions through approval, and preserving execution/governance evidence.

That makes it adjacent to Agent Memory rather than an alternative memory architecture.

DashClaw helped sharpen several Agent Memory questions:

- a governance decision is not automatically proof that the decision was enforced;
- enforcement posture should be explicit rather than implied;
- approval fatigue is itself a governance failure mode;
- liveness of the enforcement seam matters;
- prior approval history is more useful when the system remembers **why** the action was acceptable and what conditions bounded the decision.

The potential composition is:

```text
Agent Memory core
  -> Governance Context Projection
  -> DashClaw-specific adapter
  -> DashClaw guard / approval / enforcement
```

Agent Memory owns the remembered context. The projection remains vendor-neutral. A DashClaw adapter would own translation into DashClaw-specific risk, verdict, approval, and API semantics.

A public opportunity proposal is recorded in **[DashClaw issue #219](https://github.com/ucsandman/DashClaw/issues/219)**. That issue is a suggestion, not evidence that DashClaw has adopted the architecture.

DashClaw is MIT-licensed. The current relationship is citation, comparison, and independent synthesis.

> **Independence:** DashClaw and Agent Memory are independent projects. This recognition does not imply endorsement, adoption, sponsorship, or formal partnership.

---

## Microsoft Agent Governance Toolkit

**Relationship:** enforcement peer / interoperability target / policy-runtime comparator

Microsoft's **[Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)** is an independent open-source governance project focused on runtime-enforceable policy, deterministic policy evaluation, identity verification, audit logging, and related governance controls.

Its useful relationship to Agent Memory is responsibility separation:

```text
memory-specific semantics
        !=
general agent policy decision
        !=
runtime enforcement
```

Agent Memory remains authoritative for memory lifecycle, PAMA, recall admission, correction, supersession, deletion/forgetting semantics, and canonical memory evidence.

A general governance runtime may further restrict execution. It should not silently widen a memory-specific consequence that Agent Memory has denied.

The Governance Context Projection creates a clean interoperability seam:

```text
Agent Memory core
  -> Governance Context Projection
  -> AGT/ACS-style adapter
  -> policy decision / enforcement host
```

The adapter may translate precedent, material conditions, validity, scope, authority context, and outcomes into the governance runtime's own input vocabulary. The final policy decision remains downstream.

The Agent Governance Toolkit repository is MIT-licensed. Its charter also identifies Agent Governance Toolkit and AGT as Microsoft trademarks, so names are used descriptively and no Microsoft marks are incorporated here.

> **Independence:** Agent Memory is not endorsed by, sponsored by, or formally partnered with Microsoft or the Agent Governance Toolkit project by virtue of this recognition.

---

## Governance Projection connects the boundary

The architecture joining these governance peers to Agent Memory is explained in **[Governance Projection](Governance-Projection)**.

For temporal peers, the fuller evidence and projection composition is explained in **[Temporal Memory Architecture](Temporal-Memory-Architecture)**.

The core rule remains:

> **Core owns memory semantics. Governance Projection owns vendor-neutral remembered context. Consumer adapters own consumer-specific interpretation.**

This lets Agent Memory intentionally support governance as a use-case class without turning the canonical memory schema into a DashClaw, AGT, Dogwood, Cedar, Cedarling, or other policy-engine schema.

---

## How future projects are highlighted

A project earns a dedicated entry when it materially influences doctrine, supplies implementation evidence, acts as a real reference substrate or comparator, creates an interoperability/enforcement/evidence boundary, or its contributors materially improve Agent Memory through challenge and review.

Mere conceptual adjacency is not enough. Acknowledgements should follow evidence, not networking enthusiasm.
