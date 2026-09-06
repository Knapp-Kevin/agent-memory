# Concept Segmentation Matrix

## Purpose

This matrix decides whether a concept belongs as:

1. a canonical doctrine concept
2. a component inside the larger architecture
3. an implementation detail inside a specific repo
4. a product or UX surface
5. a conformance concern

This prevents concept drift by forcing every idea to answer where it belongs before it becomes another half-remembered architecture ghost.

The matrix also prevents probabilistic estimation, authority, and committed state change from being collapsed into one concept simply because one implementation happens to place them in the same service.

PAMA is native Agent Memory doctrine. Product or repository implementations may implement PAMA boundaries; they do not become the provenance owner of PAMA by doing so.

## Placement rules

| Placement | Use when | Example |
|---|---|---|
| Doctrine concept | The idea affects all implementations | saturation is not truth |
| Component | The idea has distinct interfaces and failure modes | PAMA, lifecycle engine, certification gate |
| Implementation detail | The idea is repo-specific | EvolveAI REM synthesis implementation |
| Product surface | The idea affects user interaction | memory correction UI |
| Conformance concern | The idea must be tested across systems | access-spam trap class |

## Segmentation matrix

| Concept | Placement | Component | Canonical owner | Notes |
|---|---|---|---|---|
| UOR address | Component | Identity Substrate | UOR Framework | Stable identity, not memory policy |
| BLAKE3 content identity | Implementation plus component | Identity Substrate | UOR / CodeGenome | Used by multiple systems for deterministic identity |
| Memory unit | Doctrine concept | Lifecycle Engine | Agent Memory doctrine | Shared object abstraction |
| Artifact | Doctrine concept | Identity and Evidence | Agent Memory doctrine | Raw thing entering memory |
| Observation | Doctrine concept | Evidence and Provenance | Agent Memory doctrine | Witnessed artifact or relation |
| Evidence bundle | Component | Evidence and Provenance | Agent Memory contract; implementation candidates | Must survive summarization |
| Provenance | Doctrine concept | Evidence and Provenance | Agent Memory doctrine | Required for durable transitions |
| Estimator provenance | Doctrine concept | Evidence and Provenance | Agent Memory doctrine | Identifies model/method/version behind consequential estimates |
| Fiber | Doctrine concept | Saturation and Decay | Agent Memory doctrine | Durability or relevance dimension |
| Saturation sigma | Component | Saturation and Decay | Agent Memory doctrine / lifecycle consumer | Routing signal, not truth or permission |
| Decay | Component | Saturation and Decay | Agent Memory doctrine; EvolveAI candidate | Reduces operational weight |
| CMHL | Implementation detail | Saturation and Decay | EvolveAI | Specific decay implementation |
| MTS | Implementation detail | Lifecycle routing | EvolveAI | Routing heuristic, not universal doctrine |
| Confidence fusion | Component | Reality Graphs / Evidence | CodeGenome implementation candidate | Evidence support, not permanence |
| Noisy-OR fusion | Implementation detail | Reality Graphs | CodeGenome | Specific confidence fusion method |
| Uncertainty representation | Doctrine concept | Evidence / Scoring / Governance handoff | Agent Memory doctrine | Point estimates alone may hide consequential uncertainty |
| Calibration scope | Doctrine concept plus conformance | Conformance and Calibration Harness | Agent Memory doctrine | Defines where an estimator claim is valid |
| Estimator disagreement | Conformance concern plus doctrine concept | Scoring / Evidence | Agent Memory doctrine | Must remain visible when materially consequential |
| Abstention | Doctrine concept | Governance / Lifecycle | Agent Memory doctrine | Legitimate outcome when uncertainty is too high |
| Hysteresis | Implementation pattern plus conformance concern | Lifecycle / Scoring | implementation-specific | Prevents estimator noise from creating state churn |
| Lifecycle state machine | Component | Lifecycle Engine | Agent Memory doctrine | Shared state vocabulary |
| Transition proposal | Doctrine concept | Lifecycle Engine | Agent Memory doctrine | May be probabilistic or learned; does not mutate state |
| Transition commit | Doctrine concept | Lifecycle Engine | Agent Memory doctrine | Governed state mutation with receipt |
| Crystallization | Doctrine concept plus component | Certification and Crystallization Gate | Agent Memory doctrine | Governed transition to durable state |
| Certification | Component | Certification and Crystallization Gate | Agent Memory doctrine / governance implementation | Confirmation record for durable transition |
| **PAMA** | **Native doctrine component** | Governance and Mutation Authority | **Agent Memory / Kevin R. Knapp** | Systems-agnostic authority architecture; not an external source dependency |
| PAMA target class M0-M5 | Doctrine concept | Governance and Mutation Authority | Agent Memory / PAMA | What kind of state is being changed |
| Lifecycle strength | Doctrine concept | Lifecycle / PAMA handoff | Agent Memory doctrine | Observed through canonical; separate from authority |
| Downstream authority A0-A5 | Doctrine concept | Governance and Mutation Authority | Agent Memory / PAMA | Maximum influence from retrieval through governance change |
| Mutation operation | Doctrine concept | Governance and Mutation Authority | Agent Memory specialization | Promotion, correction, pruning, deletion, scope expansion, policy mutation, etc. |
| Mutation authority | Doctrine concept | Governance and Mutation Authority | PAMA | Capability and confidence are not authority |
| Authority envelope | Doctrine concept | Governance and Mutation Authority | Agent Memory doctrine | Finite permitted / blocked / review-required consequence set |
| Permitted action set | Doctrine concept | Governance / planner handoff | Agent Memory doctrine | Stochastic choice may occur only inside this set |
| Selection mode | Audit concept | Governance / planner handoff | Agent Memory doctrine | deterministic, stochastic, human, or external selection |
| Decision receipt | Component contract | Governance / Lifecycle ledger | Agent Memory contract; implementation candidates | Reconstructs estimate, policy, allowed actions, selection, and consequence |
| Policy version | Doctrine concept | Governance | Agent Memory doctrine | Must remain distinguishable from estimator version |
| Estimator version | Doctrine concept | Evidence / Scoring | Agent Memory doctrine | Needed for consequential inference replay and drift analysis |
| Neurospace | Component | Runtime Memory Space | COREFORGE implementation | Operational agent memory space |
| Vault | Implementation plus component | Runtime Memory Space | COREFORGE implementation | Local encrypted memory container |
| Recall admission | Doctrine concept plus component | Context Assembly Surface | Agent Memory doctrine | Retrieval relevance does not override policy or scope |
| CodeGenome | Implementation component | Reality Graphs | CodeGenome | Code reality graph, not general runtime memory |
| Shadow Genome | Implementation component | Correction, Dispute, and Negative Memory | EvolveAI / FailSafe-style systems | Stores failure patterns and negative constraints |
| Durable decision memory | Doctrine concept plus profile | Durable Decision Memory | Agent Memory doctrine | Decision continuity, drift, rationale preservation, supersession |
| FailSafe evidence capture | Product plus component | Evidence and Governance | FailSafe implementation | Enforcement and audit surface |
| Arbiter | Product component | Governance and Mutation Authority | implementation candidate | Runtime policy guardian; does not own PAMA doctrine |
| Context window assembly | Product surface | Context Assembly Surface | runtime implementation | Operational use, not canonical truth |
| Correction workflow | Product surface plus component | Correction and Dispute Surface | runtime implementation | Must preserve prior state |
| Calibration protocol | Conformance concern | Conformance and Calibration Harness | Agent Memory doctrine | Determines estimator and threshold validity |
| Trap classes | Conformance concern | Conformance and Calibration Harness | Agent Memory doctrine | Includes access-spam, confident falsehood, jitter, disagreement, scope traps |
| Composition failure | Conformance concern plus doctrine concept | Cross-component | Agent Memory doctrine | Safe components may compose into unsafe behavior |
| Research challenge ledger | Doctrine maintenance concern | Research / governance | Agent Memory doctrine | Preserves supporting and challenging evidence |

## Control-character classification

New concepts that influence memory should also be classified by control character:

```text
DETERMINISTIC_SUBSTRATE
exact identity, schema validity, committed ledger semantics

PROBABILISTIC_EPISTEMICS
confidence, relevance, trust, contradiction, classification, utility, prediction

GOVERNANCE_ENVELOPE
policy mapping from observations/estimates to permitted consequences

BOUNDED_SELECTION
choice among already-permitted actions

COMMITTED_CONSEQUENCE
actual state mutation, sharing, certification, archival, deletion, or scope change
```

A concept can span more than one class only when its internal boundaries remain explicit.

## Decision tree

Use this decision tree for new concepts.

```text
Is it native contributor-authored doctrine that affects implementations broadly?
  yes -> doctrine concept / component in Agent Memory
  no -> continue

Does it have its own failure mode and interface?
  yes -> component
  no -> continue

Is it specific to one repo or runtime?
  yes -> implementation detail
  no -> continue

Is it visible to users or agents during operation?
  yes -> product surface
  no -> continue

Is it mainly used to prove behavior?
  yes -> conformance concern
  no -> open a doctrine issue before implementing
```

Then ask:

```text
Is this a target class, lifecycle strength, operation, estimate, authority decision, action selection, or committed consequence?
```

If the answer is unclear, the concept is under-segmented.

## Boundary examples

### Saturation

Saturation is a component-level concept because it has its own failure modes:

- access-spam inflation
- false permanence
- overfit durability dimensions
- poor threshold calibration
- boundary instability
- out-of-scope calibration reuse

It is also a doctrine concept because every implementation must understand that saturation is routing, not truth or permission.

### PAMA

PAMA is native doctrine and a component because it owns a bounded decision:

```text
What consequences are allowed for this proposed adaptive mutation under this policy and state snapshot?
```

PAMA also requires separate representation of:

```text
M0-M5 target class
lifecycle strength
requested operation
A0-A5 downstream authority
```

It should not be embedded as an untyped helper inside each memory implementation. That would duplicate authority logic and make policy drift inevitable, because humans apparently enjoy creating three versions of the same mistake.

### Conflict classification versus conflict consequence

Conflict detection and ranking may be probabilistic:

```text
claim A likely contradicts claim B
source A appears more reliable
```

The consequence remains governed:

```text
dispute
split scope
request verification
correct
retain both
block canonical use
```

Do not require uncertain conflict interpretation to become deterministic merely to make the system easier to describe.

### Durable decision memory

Decision continuity is a doctrine capability, not a product-owned concept.

The durable-decision profile defines the contract. A specific implementation may later earn an implementation-map entry by demonstrating conformance to that profile.

### CodeGenome

CodeGenome is an implementation component inside the larger system, not the whole memory system.

It provides code reality evidence. Agent Memory decides how that evidence becomes operational memory or durable memory.

### Neurospace

Neurospace is a runtime memory-space implementation concept.

It should consume canonical doctrine and enforce runtime boundaries, but it should not redefine identity, certification, or PAMA rules locally.

## Segmentation rule

If a concept controls a transition, it should be a component or explicit governance contract.

If a concept explains a cross-system boundary, it should be doctrine.

If a concept proves behavior, it should be conformance.

If a concept only exists inside one repo, keep it there until it proves it deserves promotion.

If a concept is native contributor-authored doctrine, keep it in the Agent Memory doctrine tree rather than manufacturing an external dependency record.

If a concept is probabilistic, do not make it authoritative by renaming the output.
