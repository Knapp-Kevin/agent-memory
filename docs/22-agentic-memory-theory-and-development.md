# Agentic Memory Theory and Development

## Purpose

This document turns the broader memory theory into an engineering model for agentic systems.

It defines what should count as agent memory, how memory functions differ, where probabilistic behavior belongs, which operations a capable memory system should expose, how memory is governed, and how implementations should be evaluated.

## Definition

**Agentic memory is retained state that can alter an agent's future interpretation, reasoning, planning, tool use, action, or adaptation across a meaningful persistence boundary.**

That boundary may be:

- token to token
- step to step
- task to task
- session to session
- deployment to deployment
- agent to successor agent
- individual agent to team or organization

Memory is therefore not synonymous with a vector database, transcript, or context window. Those are possible substrates or representations.

## Seven memory functions

A mature architecture should treat these as distinct functions:

```text
encode -> retain -> consolidate -> retrieve -> revise -> forget -> inherit
```

### Encode

Turn observations, actions, outcomes, corrections, and decisions into candidate memory.

### Retain

Keep selected information across the relevant persistence boundary.

### Consolidate

Transform experience into more durable or reusable representations.

### Retrieve

Select retained information appropriate to the task, scope, authority, freshness, and sensitivity constraints.

### Revise

Correct, refine, supersede, split, or dispute memory when new evidence arrives.

### Forget

Suppress, decay, archive, redact, delete, or abstract according to policy.

### Inherit

Provide new agents or agent generations with state they did not personally experience.

## Four stages that must not collapse

Across all seven functions, distinguish:

```text
1. ESTIMATE / PROPOSAL
   what an observer, model, heuristic, or planner suggests

2. GOVERNANCE ENVELOPE
   what policy permits, blocks, defers, quarantines, or requires review for

3. SELECTION
   which permitted action is chosen

4. COMMIT
   what state actually changes and what receipt is emitted
```

Probabilistic components may participate heavily in stage 1 and sometimes stage 3.

They do not define their own stage-2 authority.

## Memory operation surface

An implementation should expose explicit conceptual operations rather than hiding all behavior inside prompts.

```text
observe(input)
propose_memory(observation)
admit(candidate, policy)
store(memory_unit)
retrieve(query, scope, policy)
reinforce(memory_id, evidence)
revise(memory_id, mutation)
consolidate(memory_ids, target_type)
dispute(memory_id, evidence)
supersede(old_id, new_id)
forget(memory_id, mode)
share(memory_id, destination)
inherit(memory_ids, successor_scope)
certify(memory_id, evidence)
explain(memory_id)
audit(memory_id)
```

Each consequential operation should make authority and receipt semantics explicit.

## Multidimensional memory taxonomy

No single taxonomy is sufficient.

### Temporal scope

| Class | Scope | Examples |
|---|---|---|
| Immediate | current model step | intermediate calculation, tool result |
| Working | active reasoning context | scratch state, current plan |
| Session | current task or conversation | local decisions, temporary entities |
| Episodic | prior sessions or trajectories | past interactions, action/outcome traces |
| Long-term | durable reusable state | preferences, facts, procedures |
| Remote | deeply consolidated state | stable policies, mature world knowledge |
| Inherited | predates current agent experience | seed policy, organizational rules, pretrained state |

### Content type

| Type | Role |
|---|---|
| Observation | perceived state |
| Episodic | event in time and context |
| Semantic | generalized fact or concept |
| Procedural | how to perform a task |
| Prospective | intended future action or obligation |
| Preference | actor-specific choice |
| Relationship | relation among actors or entities |
| Policy | authoritative constraint |
| Failure | unsuccessful action, cause, correction |
| Correction | explicit revision |
| Decision | chosen action plus rationale |
| Evidence | support for another claim |
| Model | compact environment representation |

### Representation

Memory may live as:

- exact records
- natural-language notes
- key-value state
- relational tables
- graphs
- embeddings
- event logs
- summaries
- procedures or code
- symbolic rules
- model parameters or adapters
- multimodal artifacts

Embeddings are indexes or representations, not universal memory objects.

### Acquisition mode

Every durable memory should be able to distinguish:

```text
observed
inferred
taught
inherited
imported
synthesized
```

An inherited or inferred memory must not be misrepresented as direct observation.

### Control character

| Class | Typical examples |
|---|---|
| Deterministic substrate | identity, schema validation, policy version, ledger semantics |
| Probabilistic epistemics | relevance, confidence, trust, sensitivity, contradiction, causal hypothesis |
| Governed consequence | admission, mutation, sharing, certification, deletion, scope change |
| Bounded stochastic selection | choosing among already-permitted retrieval or planning actions |

## Write-path architecture

Separate **experience** from **admitted memory**.

```text
raw experience
   |
   v
candidate extraction
   |
   v
provenance + acquisition mode
   |
   v
sensitivity + scope estimation
   |
   v
source trust + evidence assessment
   |
   v
novelty / contradiction analysis
   |
   v
policy admission
   |
   +--> reject
   +--> quarantine
   +--> ephemeral only
   +--> store observation
   +--> request verification
   +--> consolidate under policy
   +--> propose durable promotion
```

Candidate extraction, sensitivity classification, trust estimation, contradiction detection, and novelty may be probabilistic.

The storage class and authority outcome are governed consequences.

## Read-path architecture

Retrieval is also an admission decision.

```text
query / task
   |
   v
requester + scope resolution
   |
   v
candidate generation
(exact + graph + temporal + semantic + procedural)
   |
   v
freshness / contradiction analysis
   |
   v
sensitivity + tenant + policy admission
   |
   v
task-conditioned ranking among allowed candidates
   |
   v
context composition checks
   |
   v
context assembly + recall explanation
```

Similarity alone is insufficient.

A highly relevant memory may be stale, poisoned, disputed, too sensitive, historically valid but superseded, or belong to the wrong tenant.

```text
relevance != permission
```

## Memory as a durable control channel

Persistent memory can alter future interpretation, tool choice, and action.

That makes it a control channel.

Security and governance must therefore exist at:

```text
write time
read time
mutation time
action time
sharing time
deletion time
```

A write-safe system that blindly injects every retrieved memory into context is still unsafe.

## Consolidation

Consolidation may transform:

```text
episodes -> semantic memory
episodes -> procedures
failures -> guardrails
facts + relations -> environment model
repeated preferences -> stable scoped preference
```

Every derived memory should preserve:

- source memory references
- derivation method/model
- estimator version when applicable
- uncertainty
- exceptions that materially affect behavior
- acquisition mode
- scope

Consolidation does not grant additional authority merely because the output is concise or generalized.

## Reflection

Reflection is an inference operation.

```text
reflection output != evidence
reflection output != certification
reflection output != user intent
```

Reflections should carry provenance, synthesis method, uncertainty, contradiction state, scope, and authority status.

## Working and long-term memory cooperate

Treat memory as a control loop:

```text
active context
  <-> retrieval
  <-> retained stores
  <-> consolidation
  <-> revision
  <-> forgetting
```

A capable controller may learn when to retrieve, consolidate, or forget.

Learned memory control is compatible with this doctrine only if policy constrains what it can commit, expose, share, or delete.

## Prospective memory

Agents must remember what should happen later, not only what happened before.

A prospective memory may include:

```yaml
intent: ...
trigger: time | event | state_change | manual
owner: ...
scope: ...
status: pending | satisfied | cancelled | expired
created_at: ...
due_at: ...
dependency_refs: [...]
authority_at_creation: ...
```

Memory records the obligation. Execution remains a separate action that rechecks current authority and current conditions.

## Procedural memory

Procedural memory may store:

- successful action sequences
- runbooks
- tool constraints
- recovery procedures
- diagnostic patterns
- verification methods

Procedures must be versioned because environments and policies change.

Historical success is evidence, not eternal certification.

## Failure memory

Useful failure memory should capture:

```yaml
attempt: ...
context: ...
expected_outcome: ...
actual_outcome: ...
causal_status: observed | inferred | hypothesis
root_cause_or_candidates: ...
correction: ...
verification: ...
applicability: ...
expires_or_recheck: ...
```

Do not force uncertain root-cause analysis into a false deterministic conclusion.

## Shared and multi-agent memory

Shared memory introduces:

- owner
- contributor
- observer
- tenant
- role
- trust domain
- write authority
- read authority
- correction authority
- inheritance rules
- re-sharing rights

Useful scopes include:

```text
private -> team -> organization -> public
```

Promotion between scopes is a governed transition.

Private experience does not become organizational truth because one agent wrote it into a shared store.

## Inherited memory

Inherited state may include:

- model weights
- system policy
- organizational doctrine
- user memory
- environment maps
- runbooks
- source reputation
- prior-agent lessons

Inherited memories should preserve origin and authority so successor agents can distinguish direct experience from prior state.

## Keep these signals separate

At minimum:

```text
confidence    = evidence support
trust         = source reliability within scope
relevance     = current task usefulness
saturation    = persistence pressure
sensitivity   = handling risk/classification
authority     = permission for a consequence
certification = required confirmation gate
```

Also preserve uncertainty about the estimates themselves when it materially affects policy.

One scalar cannot safely replace them.

## Core anti-patterns

1. **Vector database equals memory.** Similarity search is an indexing technique.
2. **Store every turn forever.** Write-path laziness becomes read-path chaos.
3. **Summaries without provenance.** Concision does not create truth.
4. **Retrieval count equals importance.** Popularity loops manufacture salience.
5. **Latest write wins.** Newer is not always more authoritative.
6. **Reflection equals truth.** Synthesis remains inference.
7. **One global profile.** Facts and preferences may be scope-specific.
8. **Silent overwrite.** Durable correction requires history.
9. **No forgetting policy.** Retention becomes accidental permanence.
10. **Recall benchmark equals memory quality.** Memory matters because it changes action.
11. **Governance added after memory works.** Ungoverned interfaces become architectural debt.
12. **Deterministic threshold equals certainty.** A reproducible comparison can still consume a bad estimate.

## Evaluation framework

### Encoding

- useful-memory precision/recall
- sensitive-data rejection
- unsupported-inference admission
- provenance completeness
- acquisition-mode correctness

### Retrieval

- relevant recall
- temporal correctness
- scope/tenant correctness
- stale-memory rate
- contradiction contamination
- policy-admission accuracy
- composition leakage

### Consolidation

- abstraction accuracy
- provenance completeness
- transfer utility
- exception preservation
- compression ratio

### Revision

- correction propagation
- supersession accuracy
- dispute handling
- rollback integrity
- conflict preservation

### Forgetting

- false permanence
- valuable-memory loss
- stale recall
- deletion completeness
- interference reduction
- deletion residue

### Governance

- unauthorized mutation rate
- authority replayability
- blocked-action escape rate
- policy-version correctness
- stochastic action-set violation rate

### Agent outcomes

- task success
- avoided repeated failures
- reduced redundant exploration
- policy compliance
- tool-call quality
- latency and token cost

### Security and privacy

- poisoning success
- sleeper-poisoning activation
- authority laundering
- cross-tenant leakage
- extraction success
- provenance stripping
- deletion residue

## Benchmark levels

```text
Level 1: recall
Can the system retrieve a past fact?

Level 2: temporal/update reasoning
Can it distinguish current, historical, superseded, and conflicting state?

Level 3: memory-guided action
Does retained experience improve future execution?

Level 4: governed memory
Does improvement preserve scope, authority, privacy, provenance, correction, and deletion?

Level 5: adversarial governed memory
Do those invariants survive poisoning, uncertainty, composition, drift, and concurrency?
```

## Development sequence

Governance is not Phase 7. Governance **contracts begin in Phase 1** and are enforced progressively throughout development.

### Phase 1: contracts and boundaries

Define before implementation:

- memory unit schema
- identity
- provenance
- acquisition mode
- scope/tenancy
- lifecycle states
- mutation events
- authority model
- policy versioning
- sensitivity representation
- decision receipts
- proposal-versus-commit boundary

Exit criterion:

```text
no consequential operation lacks an identified authority boundary
```

### Phase 2: safe write admission

Implement:

- candidate extraction
- sensitivity classification
- source classification/trust
- deduplication
- provenance binding
- admission policy
- quarantine/ephemeral modes

Test poisoning and unsupported inference immediately.

### Phase 3: governed retrieval

Implement:

- exact
- semantic
- temporal
- graph
- procedural retrieval

Then enforce:

- scope
- tenant
- sensitivity
- dispute state
- policy admission
- context composition

### Phase 4: revision and conflict

Implement:

- dispute
- supersession
- mutation history
- rollback
- conflict resolution
- concurrency/version controls

### Phase 5: forgetting and deletion

Implement:

- decay
- archive
- suppression
- pruning
- redaction
- deletion
- tombstones
- dependency traversal
- deletion verification

Utility estimates may nominate deletion candidates. They do not authorize irreversible deletion.

### Phase 6: consolidation and learning

Implement:

- summaries
- semantic extraction
- procedure induction
- reflection
- generalization

Require provenance, uncertainty, and admission rules for derived memory.

### Phase 7: adaptive control

Only after the boundaries are enforceable, introduce or expand:

- learned write policies
- learned forgetting
- adaptive retrieval
- probabilistic action selection
- automatic source trust
- automatic conflict interpretation

Adaptive components must operate within existing governance envelopes.

### Phase 8: adversarial lifecycle evaluation

Test:

- high-confidence false memory
- access-spam
- threshold jitter
- estimator disagreement
- sleeper poisoning
- cross-tenant relevance
- unsafe composition
- uncertain sensitivity
- policy/estimator drift
- concurrent mutation
- deletion residue

## Conformance questions

An implementation claiming Agent Memory alignment should answer:

1. What exactly is a memory unit?
2. Which persistence boundary does each memory class cross?
3. What is raw evidence versus synthesis?
4. Which components are probabilistic and what do their outputs mean?
5. Who may create, revise, promote, share, or delete memory?
6. How is source trust represented and scoped?
7. How are contradictions and alternative hypotheses preserved?
8. How does the system distinguish current from historical truth?
9. How does forgetting work and how is deletion verified?
10. How is sensitive memory governed at write, read, and sharing time?
11. How is memory poisoning contained across later sessions?
12. How are procedures and failures versioned?
13. How are prospective commitments represented without conflating memory with execution?
14. How is inherited memory distinguished from direct experience?
15. What evidence demonstrates improved agent behavior rather than simple recall?
16. What prevents an estimator from granting itself authority?
17. Can an auditor reconstruct the policy, estimator context, allowed actions, and committed consequence?

If those answers are missing, the system probably has a retrieval feature, not a governed memory architecture.

## Related documents

- `01-layer-model.md`
- `04-governance-and-pama.md`
- `06-conformance-test-plan.md`
- `09-calibration-protocol.md`
- `11-component-architecture.md`
- `15-memory-threat-model.md`
- `16-source-trust-and-reputation.md`
- `17-conflict-resolution-engine.md`
- `18-temporal-causality-layer.md`
- `19-privacy-and-sensitivity-classifier.md`
- `20-memory-foundations-across-scales.md`
- `21-forgetting-consolidation-and-memory-metabolism.md`
- `23-research-bibliography.md`
- `24-determinism-probability-and-governed-uncertainty.md`
