# Determinism, Probability, and Governed Uncertainty

## Status

**Canonical doctrine.**

This document defines the current boundary between deterministic, probabilistic, learned, human, and formally bounded behavior in Agent Memory.

The general doctrine is governed by **Accepted ADR-020**. Canonical structural mutation has the additional safeguard defined by **Accepted ADR-032**: structural discovery may be uncertain, but the authority determination that commits a canonical structural consequence must be deterministic and versioned or explicitly human-authorized.

Doctrine maturity does not imply universal implementation conformance. Runtime evidence and implementation maturity remain separately tracked.

## Core question

Agent memory operates on incomplete, noisy, ambiguous, changing, and sometimes adversarial information.

Some memory behavior should therefore remain probabilistic, learned, heuristic, or stochastic.

At the same time, uncertainty must not silently acquire authority to:

- create canonical truth
- cross tenant or user boundaries
- expose sensitive memory
- permanently delete evidence
- mutate policy
- rewrite durable history
- certify its own inference
- create inherited control over successor agents
- redefine canonical memory structure

The useful question is not:

> Should memory be deterministic or probabilistic?

It is:

> **Which parts of memory may reason under uncertainty, and which consequences must remain explicitly bounded, enforceable, and reconstructable?**

## Working thesis

> **Probabilistic discovery may produce beliefs, rankings, hypotheses, candidates, confidence estimates, risk estimates, and proposed actions. Consequential memory behavior must occur inside an explicit governance envelope whose permissions, prohibitions, transitions, and audit consequences are explicit and bounded.**

Short form:

> **Probabilistic epistemics. Governed consequences.**

Operational form:

> **Uncertainty may propose. Authority constrains.**

Structural specialization:

> **Memory shape may adapt. Authority over canonical structural mutation may not be probabilistic.**

The earlier phrase "authority certainty" is deliberately avoided. Governance can be rigorous without claiming epistemic certainty. What the architecture needs is **authority boundedness, explicit policy semantics, and reconstructable consequence**.

## Definitions

### Deterministic

For fixed committed inputs and implementation state, the operation produces a defined reproducible result.

Examples:

- hash verification
- schema validation
- exact tenant ID comparison
- state-version comparison

### Probabilistic

The operation represents uncertainty through probabilities, distributions, confidence estimates, or stochastic behavior.

Examples:

- semantic relevance
- source-reliability estimate
- sensitivity classification
- competing causal hypotheses

### Learned

Behavior is produced by a trained model or policy. Learned behavior may be deterministic or stochastic at runtime and should not be treated as synonymous with probabilistic.

### Heuristic

Behavior follows hand-designed rules or scores whose outputs may not have a probabilistic interpretation.

A value between 0 and 1 is not automatically a probability.

### Formally bounded

Behavior may vary, but a separately specified guarantee restricts the possible outcomes.

Example:

```text
planner may choose any action in permitted_set
planner may never select outside permitted_set
```

### Governed

An operation is governed when its authority, scope, policy, permitted outcomes, and consequential receipts are explicit enough to enforce and audit.

Governed does not mean human-approved. Human approval is one possible authority mechanism.

### Deterministically authorized structural mutation

A canonical structural mutation is deterministically authorized when a versioned, reproducible rule evaluates the exact current structural state and proposal and proves that the consequence lies inside an explicitly delegated autonomous envelope.

The rule may consume probabilistic evidence as evidence. The probabilistic output itself cannot decide that the envelope applies.

## Why the binary is misleading

"Deterministic" can refer to:

1. computational determinism
2. policy determinacy
3. state-transition determinacy
4. replayability
5. exact identity
6. formal safety boundedness

"Probabilistic" can refer to:

1. uncertainty about truth
2. uncertainty about relevance
3. stochastic retrieval
4. learned ranking
5. confidence calibration
6. source trust
7. risk estimation
8. stochastic exploration
9. uncertainty about sensitivity
10. uncertainty about causality
11. structural novelty discovery
12. migration-benefit estimation

A deterministic threshold applied to a noisy estimate is not epistemic certainty.

A stochastic planner operating inside an enforced action set is not necessarily ungoverned.

A learned system that proposes an excellent new schema is still not the authority that commits the schema.

## Canonical four-stage model

```text
observation / query / event
        |
        v
1. EPISTEMIC INTERPRETATION
   probabilistic / learned / heuristic
   beliefs, rankings, trust, sensitivity,
   contradiction, utility, causal hypotheses
        |
        v
2. GOVERNANCE ENVELOPE
   policy + authority + scope + state
   -> permitted actions
   -> prohibited actions
   -> review / abstain / verification
        |
        v
3. BOUNDED SELECTION
   optional deterministic, stochastic,
   learned, external, or human choice
   AMONG PERMITTED ACTIONS ONLY
        |
        v
4. COMMITTED CONSEQUENCE
   defined transition + provenance + receipt
```

Required invariant:

```text
selected_action ∈ permitted_actions
```

A second invariant is equally important:

```text
estimator_output != authority
```

For canonical structural mutation there is a third invariant:

```text
probabilistic_structural_proposal != structural_commit_authority
```

## Formal sketch

Let:

```text
s  = current memory state
x  = observation, query, or event
E  = epistemic process
b  = belief / estimate / distribution produced by E
P  = versioned governance policy
A  = authority and scope facts
G  = governance function
S  = permitted action set
π  = optional action selector
T  = committed transition function
r  = decision receipt
```

Then:

```text
b = E(x, s)
S = G(s, b, P, A)
a ~ π(a | b, S)
require a ∈ S
s' = T(s, a)
r = receipt(s, b, P, A, S, a, s')
```

For high-consequence actions policy may require:

```text
S = {}
```

until review or external verification occurs, or:

```text
S = {one explicitly authorized action}
```

The doctrine does not require every `G` implementation to be one static rules engine. It requires the resulting authority semantics to be explicit and bounded.

For canonical structural mutation, `G` has an additional restriction: an autonomous permission result must come from a versioned deterministic structural classifier/policy over the exact current state and proposal. Otherwise the structural action remains review-required or prohibited.

## Zone 1: deterministic substrate

These functions normally need reproducible behavior because ambiguity creates identity, integrity, access-control, or audit failure.

Examples:

- content hashing
- exact identity resolution
- schema validation
- tenant and actor identifier comparison
- explicit ACL/capability checks
- cryptographic signature verification
- policy-version lookup
- lifecycle transition validity
- state-version comparison
- ledger append semantics
- tombstone interpretation
- dependency references used for deletion
- structural compatibility checks used for autonomous schema authority
- structural state/version checks at commit

Do not use a probabilistic model to infer something the system already knows exactly.

## Zone 2: probabilistic epistemics

These functions naturally operate under uncertainty:

- semantic similarity
- retrieval relevance
- source trust
- anomaly/poisoning risk
- contradiction detection
- entity resolution when exact identity is absent
- sensitivity classification
- novelty
- clustering
- abstraction
- procedure induction
- causal hypothesis generation
- predicted staleness
- predicted future utility
- composition risk
- structural novelty discovery
- candidate ontology/schema generation
- predicted migration or retrieval benefit

Outputs should identify their semantics, provenance, and uncertainty when materially consequential.

Structural novelty is useful proposal evidence. It is not structural authority.

## Zone 3: governance envelope

Governance maps current state and uncertain evidence to explicit outcomes such as:

```text
allow
allow_ephemeral_only
allow_with_ledger
allow_inside_scope
require_more_evidence
require_verification
require_review
quarantine
dispute
archive
block
```

A governance receipt should make knowable:

- policy version
- actor and authority
- target scope
- relevant memory state/version
- estimator outputs used
- estimator/calibration versions when material
- uncertainty or disagreement
- permitted action set
- prohibited consequence

If required authority facts are missing, high-consequence permission must not be guessed.

## Zone 4: committed consequence

Consequential operations include:

- durable write
- promotion
- crystallization
- correction
- supersession
- sharing or scope expansion
- pruning
- irreversible deletion
- policy mutation
- domain-schema mutation
- inherited-memory publication

A commit should bind to the state and policy snapshot that authorized it.

## Structural mutation specialization

Agent Memory permits structure to adapt, but it distinguishes three kinds of shape:

```text
canonical semantic shape
application / domain ontology
derived / physical representation
```

A lower-layer representation change must not silently reinterpret a higher-layer semantic contract.

ADR-032 classifies structural consequences approximately as:

| Class | Typical change | Default authority posture |
|---|---|---|
| S0 | derived/index/rebuild-only change with preserved semantics | autonomous under deterministic maintenance policy |
| S1 | bounded additive local extension with rollback and no authority widening | autonomous only when deterministic policy proves the bounded envelope |
| S2 | semantic reinterpretation or migration-bearing change | user-visible proposal and authorized human decision by default |
| S3 | destructive, cross-scope, isolation-, policy-, or authority-bearing change | explicit authorized human decision; stricter policy may block |

A probabilistic component may propose any class. It cannot decide that a proposal is safe enough to downgrade itself into S0 or S1 for authority purposes.

The deterministic structural classifier must consider at least the applicable semantic impact, scope, blast radius, migration requirement, dependency impact, reversibility, residue/rebuild obligations, and authority/isolation effect.

Current PAMA 1.2 remains conservatively stricter than this doctrine: `domain_schema_mutation` routes to review or external verification at every risk level. Issue #281 owns the executable evidence required before a narrower autonomous S0/S1 path may be introduced.

## Operation-by-operation boundary

| Operation | Uncertain behavior may estimate/propose | Governance must control |
|---|---|---|
| Observe | extraction, perception confidence | source identity, timestamp/provenance semantics |
| Propose memory | salience, novelty, memory type | candidate schema and acquisition mode |
| Admit | usefulness, trust, sensitivity | scope, storage class, retention restrictions |
| Retrieve | semantic ranking, query expansion | tenant/scope/sensitivity/dispute admission |
| Consolidate | clustering, summary, abstraction | derivation provenance and promotion authority |
| Reinforce | utility, evidence weighting | which signals may affect lifecycle score |
| Revise | contradiction, correction hypothesis | mutation authority and history preservation |
| Crystallize | candidate score | certification and canonical transition |
| Forget | decay, staleness, future utility | retention holds, deletion mode and authority |
| Share | usefulness to recipient | consent, ACL, tenant, sensitivity, destination |
| Inherit | useful seed selection | acquisition mode, scope and inherited authority |
| Execute procedure | procedure selection | tool permission and destructive-action gates |
| Mutate domain structure | structural novelty, candidate schema, predicted benefit | exact class, migration, scope, dependency, rollback, and commit authority |
| Rebuild derived representation | rebuild utility, scheduling priority | semantic invariance, scope, resource limits, residue/currentness |

## Consequence classes

Governance strength should scale with consequence.

### Class 0: ephemeral cognition

Examples:

- temporary ranking
- query expansion
- hypothesis generation

Default:

```text
probabilistic behavior broadly acceptable
no durable mutation
```

### Class 1: reversible operational state

Examples:

- session cache
- provisional note
- temporary summary

Default:

```text
probabilistic proposal allowed
policy admission
rollback or expiry available
```

### Class 2: durable revisable memory

Examples:

- scoped preference
- semantic fact
- procedure
- long-term failure memory

Default:

```text
provenance + authority + correction path required
```

### Class 3: canonical, sensitive, or shared memory

Examples:

- certified decision
- organizational rule
- cross-agent shared memory
- sensitive durable memory

Default:

```text
strong scope + authority + certification/audit requirements
```

### Class 4: irreversible or governance-changing action

Examples:

- permanent deletion
- evidence destruction
- credential exposure
- policy mutation
- authority change
- broad cross-tenant publication
- destructive or authority-bearing structural mutation

Default:

```text
strongest authority
state/version binding
explicit receipt
usually no autonomous ambiguity about permission
```

The class changes the required governance, not whether upstream cognition is allowed to be probabilistic.

## Deterministic thresholds are not safe by definition

This is deterministic:

```text
if trust_score >= 0.80:
    persist_forever()
```

It may also be disastrously calibrated.

Thresholds may be:

- domain-specific
- risk-specific
- source-specific
- time-sensitive
- brittle near boundaries
- vulnerable to adversarial optimization
- invalid after estimator drift

Therefore calibrate the estimator **and** test the policy consequence near the boundary.

Use abstention, review bands, hysteresis, or stronger evidence when the cost of a threshold mistake is high.

For structural mutation, a deterministic threshold over a probabilistic utility/confidence score is not sufficient autonomous authority by itself. The deterministic policy must establish bounded structural facts such as scope, migration need, semantic compatibility, dependency state, reversibility, and authority effect.

## Probabilistic action inside a bounded envelope

Stochastic behavior can remain useful for:

- selecting which authorized memory to inspect first
- exploring alternative retrieval queries
- choosing among reversible candidate plans
- sampling memories for offline consolidation
- choosing among equally permitted compression strategies
- generating alternative structural proposals for later deterministic/human evaluation

The safety requirement is not identical output.

It is invariant preservation:

```text
prohibited actions remain unreachable
```

## Uncertainty should be typed

A mature system should distinguish forms of uncertainty rather than emitting one generic `confidence` field.

Useful categories include:

```text
epistemic uncertainty
aleatoric variability
estimator disagreement
out-of-distribution uncertainty
policy uncertainty
authority uncertainty
scope uncertainty
temporal uncertainty
causal uncertainty
sensitivity uncertainty
structural compatibility uncertainty
migration-impact uncertainty
```

Different uncertainty types demand different handling.

For example:

- epistemic uncertainty may permit an ephemeral write
- authority uncertainty should block a high-impact mutation
- scope uncertainty should block cross-tenant sharing
- sensitivity uncertainty may trigger stricter export handling
- structural compatibility uncertainty should prevent autonomous canonical migration

## Belief memory challenges deterministic conclusions

Under partial observability, storing one deterministic conclusion can create self-reinforcing error.

[Belief Memory: Agent Memory Under Partial Observability](https://arxiv.org/abs/2605.05583) explores retaining multiple candidate conclusions with probabilities rather than collapsing ambiguous observations into one memory.

Engineering implication:

> uncertainty itself may be valuable durable state.

This supports storing alternatives and disagreement where the cost of premature certainty is high.

## Security research challenges static governance

Current memory-security work reinforces the need for explicit authority while also challenging simplistic deterministic filters.

- [Memory Poisoning Attack and Defense on Memory Based LLM-Agents](https://arxiv.org/abs/2601.05504) reports that trust thresholds need careful calibration to avoid both over-rejection and missed attacks.
- [Hidden in Memory: Sleeper Memory Poisoning in LLM Agents](https://arxiv.org/abs/2605.15338) shows why write-time checks alone are insufficient for persistent memory.
- [AgentSys](https://arxiv.org/abs/2602.07398) provides evidence for explicit memory isolation and schema-validated boundary crossing.
- [Securing LLM-Agent Long-Term Memory Against Poisoning](https://arxiv.org/abs/2606.24322) argues that content and lineage signals can be laundered and motivates origin-bound authority.
- [Toward Secure LLM Agents](https://arxiv.org/abs/2606.10749) identifies persistent state, delegated authority, provenance, and weak composition as important security surfaces.

The lesson is not "make everything deterministic."

It is:

> keep trust, risk, content interpretation, and structural discovery adaptive where necessary, but prevent them from minting authority.

## Privacy challenges item-level classification

Persistent memory can leak through composition, cross-session inference, derived summaries, and incomplete deletion.

- [Agents That Know Too Much](https://arxiv.org/abs/2606.26627) surveys privacy across agent data surfaces and highlights compositional and cross-session risks.
- [Deployment-Time Memorization in Foundation-Model Agents](https://arxiv.org/abs/2606.10062) studies privacy/utility tradeoffs and deletion residue in derived memory.

Engineering implication:

> privacy governance cannot be one deterministic sensitivity flag assigned once at write time.

Classification may evolve. Scope and disclosure consequences remain governed throughout the lifecycle.

Structural changes that alter scope, isolation, disclosure, or retention interpretation are therefore not ordinary schema maintenance. They are authority-bearing structural consequences under ADR-032.

## Evidence supporting uncertainty-preserving memory

Open cognitive research provides functional inspiration, not mechanistic equivalence:

- stochastic selective retrieval can influence later decisions: https://pmc.ncbi.nlm.nih.gov/articles/PMC3651451/
- humans can incorporate working-memory uncertainty into later choices: https://pmc.ncbi.nlm.nih.gov/articles/PMC7165478/

Agentic implication:

- retrieval is not an infallible read
- memory should sometimes preserve alternatives, confidence, and disagreement

Do not infer from this that a specific neural or Bayesian mechanism is required in software.

## Adjacent precedent: runtime assurance

Learning-enabled systems have long explored architectures where high-performance uncertain controllers operate under separately enforced safety constraints.

Relevant open work includes:

- https://arxiv.org/abs/2109.13446
- https://arxiv.org/abs/2102.12981
- https://arxiv.org/abs/2506.11033

This is a **functional architectural precedent**, not proof that one runtime-assurance algorithm is correct for memory.

## Failure modes of the doctrine itself

This doctrine can fail if implemented naively.

### Policy brittleness

A deterministic policy may encode a bad assumption and reproduce it perfectly.

### Estimator-policy coupling

An estimator and policy may be tuned together so tightly that changing the model invalidates the policy boundary.

### Hidden stochasticity

External tools, concurrency, model providers, or retrieval stores may introduce variability not represented in the receipt.

### False formalism

Calling a boundary "formally bounded" without specifying the guarantee or evidence is decoration, not assurance.

### Human-review laundering

`require_human_review` is not automatically safe if the reviewer lacks evidence, context, or real authority.

### Over-conservatism

Governance can reject so much useful memory that the agent stops adapting.

### Under-conservatism

Flexible policy can become a euphemism for permitting whatever the model wanted.

### State races

A correct authorization can become stale before commit.

### Composition gaps

Individually governed components can combine into an unsafe system.

### Structural self-authorization

A learned or probabilistic component may discover a genuinely useful new shape and then incorrectly treat that usefulness as authority to change canonical interpretation.

### Structural classification laundering

An implementation may call a semantic migration a harmless rebuild or additive change to fit an autonomous S0/S1 envelope.

### Retirement without residue proof

A schema version may be declared retired while retained state, projections, consumers, or learned representations still depend on its interpretation.

These are conformance targets, not footnotes.

## Required decision receipt

For consequential transitions, preserve where applicable:

```text
memory_id
actor
requested_action
state_snapshot
estimator_refs
estimator_versions
calibration_refs
uncertainty_summary
policy_refs
policy_version
authority_refs
permitted_actions
prohibited_actions
selected_action
selection_mode
before_state
after_state
rollback_or_recovery_path
evidence_refs
timestamp
```

For canonical structural transitions also preserve, where applicable:

```text
current_structure_ref
proposed_structure_ref
structural_class
semantic_diff_ref
scope_impact
migration_impact
dependency_impact
reversibility / rollback_ref
residue_or_rebuild_obligations
structural_classifier_ref/version
human_authority_ref when required
```

Exact stochastic replay is not always required.

Reconstruction of **what was believed, what was permitted, what was prohibited, and what changed** is required.

## Conformance requirements

A governed-uncertainty implementation should test at least:

1. high-confidence false promotion
2. threshold jitter
3. estimator disagreement
4. cross-tenant high relevance
5. stochastic retrieval with prohibited candidates
6. unsafe multi-memory composition
7. uncertain sensitivity before disclosure
8. concurrent conflicting mutation
9. permanent deletion under uncertain utility
10. policy-versus-estimator version drift
11. missing authority state during replay
12. sleeper poisoning
13. authority laundering
14. deletion residue
15. out-of-calibration estimator input
16. high-confidence structural proposal cannot self-authorize
17. bounded additive structural change requires deterministic envelope evidence
18. semantic migration requires human authority unless a future accepted exact delegation says otherwise
19. destructive or cross-scope structural change cannot be downgraded by estimator confidence
20. stale structural impact analysis cannot authorize commit
21. schema retirement cannot claim completion while declared dependencies/residue remain

## ADR-020 acceptance evidence

ADR-020 is **Accepted**. Its stronger doctrine-maturity gate was satisfied only after executable evidence existed for the required estimate -> governance -> bounded action -> commit boundaries and adversarial negative paths.

The acceptance evidence includes:

```text
[x] executable governed-uncertainty fixtures
[x] end-to-end implementation mapping estimate -> policy -> action set -> commit
[x] blocked actions remaining blocked across stochastic trials
[x] high-confidence false memory unable to self-promote
[x] cross-scope relevance unable to bypass admission
[x] irreversible deletion not authorized by utility score alone
[x] policy and estimator versions reconstructable
[x] concurrent mutation prevented from silently becoming last-writer-wins
[x] derived-memory deletion residue tested
[x] adversarial doctrine challenges producing documented boundaries/revisions
```

The canonical audit is `audits/governed-uncertainty/09-adr-020-runtime-evidence-acceptance-audit.md`.

ADR-032 is an Accepted structural specialization. Its implementation follow-up does not retroactively weaken ADR-020 or current PAMA. Until #281 proves a narrower autonomous structural envelope, current PAMA 1.2 remains the executable posture for `domain_schema_mutation`.

## Research posture

Prefer freely inspectable research when practical:

- open-access journals
- PubMed Central
- lawful preprints
- open proceedings
- public technical reports
- open benchmark/data repositories

For consequential doctrine:

```text
record support
record challenge
record boundary conditions
record implementation evidence
record conformance evidence
```

Citation count is not confidence.

## Canonical principles

1. **Identity should be exact where exact identity exists.**
2. **Uncertain interpretation should preserve uncertainty.**
3. **Scores and confidence are not authority.**
4. **Governance should bound consequence, not pretend to eliminate uncertainty.**
5. **Stochastic choice may operate inside a permitted set.**
6. **Consequence strength should scale with irreversibility, scope, sensitivity, and authority.**
7. **A deterministic error is not inherently safer than a probabilistic error.**
8. **A probabilistic component is not inherently ungovernable.**
9. **Policy and estimator versions must remain distinguishable.**
10. **Authority must be reconstructable even when cognition cannot be replayed exactly.**
11. **Read-time governance matters as much as write-time governance.**
12. **Composition must be tested, not assumed safe from component-level correctness.**
13. **Memory structure may adapt without making representation technology canonical.**
14. **Probabilistic systems may discover and propose canonical structural change, but may not be the authority that commits it.**
15. **Bounded autonomous structural change requires a deterministic versioned authority envelope; larger semantic, destructive, cross-scope, or authority-bearing changes require explicit human authority unless an Accepted exact delegation says otherwise.**
16. **Schema and domain structure have lifecycle, migration, dependency, supersession, rollback, and residue obligations.**
17. **The doctrine itself remains revisable.**

## Related documents

- `01-layer-model.md`
- `02-lifecycle-state-machine.md`
- `03-scoring-and-decay.md`
- `04-governance-and-pama.md`
- `06-conformance-test-plan.md`
- `09-calibration-protocol.md`
- `11-component-architecture.md`
- `13-system-composition-boundaries.md`
- `15-memory-threat-model.md`
- `16-source-trust-and-reputation.md`
- `17-conflict-resolution-engine.md`
- `18-temporal-causality-layer.md`
- `19-privacy-and-sensitivity-classifier.md`
- `20-memory-foundations-across-scales.md`
- `21-forgetting-consolidation-and-memory-metabolism.md`
- `22-agentic-memory-theory-and-development.md`
- `23-research-bibliography.md`
- `27-schema-registry-and-type-evolution.md`
- `42-governed-mutable-memory-fabric.md`
- `profiles/pama-1-2-domain-schema-compatibility.md`
- `adr/ADR-020-probabilistic-discovery-deterministic-governance.md`
- `adr/ADR-032-governed-mutable-memory-structure.md`
