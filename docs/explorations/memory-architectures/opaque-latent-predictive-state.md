# Opaque Latent Predictive State and JEPA-Style Memory

Status: **active exploratory research** under #137 and parent #67. This document is not canonical doctrine.

## Research posture

This study does **not** assume that current Agent Memory architecture should survive unchanged.

A contributor claim that JEPA-style predictive representation may be materially better than the repository's present explicit/canonical memory approach is treated as a legitimate hypothesis to test, not as a misunderstanding to dismiss.

The question is therefore broader than:

> Can existing governance wrap an opaque latent state?

It is:

> **Where is a JEPA-style predictive representation objectively stronger than the memory representations Agent Memory currently assumes or demonstrates, and what should be replaced, retained, or composed if the evidence favors JEPA?**

`better` is not treated as one scalar. The comparison must name the dimension and evidence.

## Primary research basis

Initial primary sources:

- Assran et al., *Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture* (I-JEPA), arXiv:2301.08243: https://arxiv.org/abs/2301.08243
- Bardes et al., *Revisiting Feature Prediction for Learning Visual Representations from Video* (V-JEPA), 2024: https://ai.meta.com/research/publications/revisiting-feature-prediction-for-learning-visual-representations-from-video/
- Assran et al., *V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning*, 2025: https://arxiv.org/abs/2506.09985
- Meta V-JEPA 2 project and benchmark material: https://ai.meta.com/research/vjepa/

The strongest current evidence is in visual representation, physical-world prediction, action anticipation, and planning. That is already enough to justify serious architectural evaluation. It is not enough to claim universal superiority for durable semantic, episodic, organizational, or governance-sensitive memory.

## What JEPA appears to offer that deserves serious consideration

### 1. Predictive representation instead of literal reconstruction

JEPA learns representations by predicting target representations from context rather than reconstructing all raw observation detail.

Potential advantage:

```text
retain task-relevant structure
without requiring literal reconstruction of every observation detail
```

This is materially different from treating memory primarily as explicit facts, documents, chunks, rows, graph relations, or summaries.

If task performance depends more on latent predictive structure than on proposition-level recall, an explicit-memory-first architecture can be the wrong operational abstraction even when it remains useful for evidence and governance.

Evidence state: `primary_research_supported`.

### 2. Strong learned world-state representations

V-JEPA and V-JEPA 2 report strong frozen-representation performance for motion understanding and visual reasoning. V-JEPA 2 reports state-of-the-art action anticipation and strong video question-answering results at the evaluated scales.

Potential advantage:

```text
memory as learned state useful for anticipating what happens next
rather than memory only as retrievable records about what happened before
```

That distinction matters for agents whose next action depends on dynamics, causal structure, or evolving environment state.

Evidence state: `primary_research_supported`.

### 3. Planning directly in latent predictive space

V-JEPA 2-AC demonstrates model-predictive planning using latent predicted future states and goal-state representations. The reported robot experiments use a relatively small amount of robot interaction data after large-scale self-supervised video pretraining.

Potential advantage:

```text
observed state
-> latent predictive state
-> imagined consequences of candidate actions
-> goal-relative planning
```

This can be substantially more useful than retrieving memories and asking a downstream language model to infer dynamics from them.

Evidence state: `primary_research_supported` for the published physical-world tasks; `not_yet_evaluated` for Agent Memory workloads.

### 4. Reduced dependence on labels and task-specific supervision

The JEPA program is explicitly self-supervised. V-JEPA 2's actionless pretraining learns useful representations before action-conditioned post-training.

Potential advantage:

- better use of abundant unlabeled observation streams;
- less dependence on manually curated memory labels;
- continual representation learning may capture structure that explicit memory extraction misses.

Evidence state: `primary_research_supported` in the reported domains; `open_hypothesis` for general agent memory.

### 5. Operational compression may be a feature, not merely a governance problem

Agent Memory doctrine has correctly treated compression as incapable of erasing scope, provenance, or authority obligations. That remains an important governance hypothesis.

But compression should not be framed only as information loss. A representation that deliberately discards unpredictable or irrelevant detail may be **better** for prediction and planning.

Research must distinguish:

```text
loss of reconstructable detail
from
loss of task-relevant predictive structure
```

A system may rationally want both:

```text
source-addressable governed evidence
+
compressed latent predictive state
```

## Where the JEPA evidence does not yet establish superiority

### Durable source-addressable memory

The current JEPA evidence does not establish a replacement for source-addressable durable records where a system must answer:

- exactly what was retained;
- which source justified it;
- who may change it;
- what was corrected or superseded;
- what must be deleted;
- which scope or principal may use it;
- what evidence supports a later audit.

Evidence state: `not_yet_evaluated` as a replacement capability.

### Proposition-level correction

Opaque learned state does not naturally expose a proposition such as:

```text
customer preference X was wrong; replace it with Y
```

This does not prove JEPA is unsuitable. It means correction may operate through invalidation, source withdrawal, replay, retraining, or rebinding rather than local field edits.

The important question is whether those semantics are operationally sufficient and economically acceptable.

Evidence state: `open_hypothesis`.

### Deletion and derived residue

A learned representation can retain influence after literal source bytes are gone. The inability to reconstruct source text is not evidence that source-derived influence has disappeared.

This is a serious cost for regulated or user-controlled forgetting and must be measured rather than hand-waved.

Evidence state: `architectural_deduction`, with implementation-specific proof still required.

### General semantic/episodic agent memory

The strongest published JEPA results are not a benchmark of long-lived agent facts, preferences, commitments, multi-tenant organizational state, or conversational episodic memory.

A physical-world world model may still inspire a superior general memory architecture, but that extrapolation needs evidence.

Evidence state: `not_yet_evaluated`.

## The three architecture outcomes we must allow

### Outcome A: current explicit memory remains primary; JEPA is optional prediction

```text
canonical governed memory
-> JEPA-style predictive projection
-> proposal/planning
-> PAMA
```

This is the conservative outcome and must not be selected merely because it preserves current architecture.

### Outcome B: hybrid dual-plane memory becomes preferred

```text
                 +-> source-addressable evidence / lifecycle plane
observation -----+
                 +-> learned predictive state / world-model plane

both planes -> governed context + planning + action authority
```

In this outcome, explicit records are not the only meaningful memory. Latent predictive state is a first-class operational memory representation, while evidence/lifecycle state remains separately governed.

This is currently the strongest architecture hypothesis worth testing.

### Outcome C: JEPA-like predictive state displaces part of current operational memory

If comparative experiments show that explicit extracted memories systematically lose predictive structure, create brittle summaries, or underperform latent predictive state on target agent workloads, the repository should be willing to de-emphasize those explicit representations for operational reasoning.

This could mean:

```text
explicit/canonical record = evidence and user-control surface
latent predictive state   = primary operational world-state representation
```

That would be a material architecture change. It is allowed if evidence justifies it.

## Comparison dimensions

A fair comparison must include capability and governance dimensions.

| Dimension | Explicit / record-oriented memory | JEPA-style latent predictive state | Evidence needed |
|---|---|---|---|
| exact source identity | naturally strong | requires external binding | cross-architecture experiment |
| human inspectability | naturally strong | weak by default | implementation observation |
| proposition correction | naturally precise | likely rebuild/invalidate oriented | executable correction experiment |
| predictive dynamics | often delegated downstream | architecture-native strength | matched workload benchmark |
| action consequence simulation | not intrinsic | architecture-native in action-conditioned variants | planning benchmark |
| unlabeled learning | limited unless separate learner exists | core design advantage | primary research + local experiment |
| task-relevant compression | manual/estimator-dependent | learned objective | matched workload benchmark |
| scope enforcement | explicit metadata/policy friendly | requires external binding | adversarial isolation experiment |
| deletion proof | difficult but source-addressable | potentially harder due learned residue | deletion/residue experiment |
| provenance | explicit chain possible | requires derivation/checkpoint/source-basis evidence | provenance reconstruction test |
| planning usefulness | indirect | directly demonstrated in physical domains | workload-specific experiment |
| compute/rebuild cost | typically lower | potentially substantial | measured implementation evidence |

Do not fill this table with universal winners before equivalent experiments exist.

## First executable pressure test

The first representation-neutral fixture is intentionally simple:

```text
source A + source B
      -> opaque predictive state L
      -> prediction quality = high
      -> L may influence planning

later:
source B is revoked / deleted / scope-restricted

observation:
L remains equally predictive
```

The test asks two separate questions:

1. **Capability question:** does L remain useful?
2. **Governance question:** may unchanged usefulness preserve currentness, admission, scope, or action authority?

Expected starting hypothesis:

```text
usefulness may remain high
AND
current authorization may still require revalidation
```

That is not a rejection of JEPA. It is the property we need if a superior learned representation is going to coexist safely with source change and user control.

## J0 findings from current contracts

Current derivation evidence already supports several JEPA-relevant requirements without adding a JEPA-specific canonical primitive:

- root source references survive transformations;
- transformer confidence does not create authority;
- probabilistic transformation can be represented;
- output identity can be bound by reference/type/digest;
- scope is preserved unless explicitly narrowed;
- later source currentness is evaluated without rewriting historical derivation evidence;
- source revocation, deletion, tombstoning, dispute, supersession, and scope reduction can require revalidation independently of prediction confidence;
- currentness evaluation explicitly does not establish memory admission or authority.

This is evidence that the **governance envelope can represent an opaque predictive projection**, not evidence that the current operational memory architecture is better than JEPA.

Evidence state: `implementation_observed` once #137 executable tests pass.

## What would falsify current assumptions

The research should actively look for these outcomes:

1. explicit/canonical memory loses task-critical predictive information that JEPA retains;
2. extracting human-readable memories before planning performs worse than planning from learned latent state;
3. lifecycle/source binding requirements make JEPA impractically expensive to refresh, weakening the hybrid hypothesis;
4. latent state cannot be scoped or invalidated with sufficient precision for multi-tenant use;
5. learned state can be independently re-evidenced after source changes, allowing more reuse than current derivation rules assume;
6. proposition-level correction is unnecessary for some memory classes because governed rebuild is measurably superior;
7. current memory-unit ontology forces distinctions that are actively harmful for predictive state.

Any of these is a useful result.

## Next experiments

### J1-A: representation-neutral governance proof

- executable opaque-state fixture;
- high predictive confidence before and after source revocation;
- source revocation/deletion/scope reduction causes currentness revalidation;
- historical derivation remains unchanged;
- planning influence remains separate from action authorization.

### J1-B: matched operational-memory benchmark

Create a workload where the same observation stream is represented as:

```text
A. explicit extracted memories
B. vector/summary retrieval state
C. compact learned predictive state
D. hybrid explicit + predictive state
```

Measure at least:

- next-state / next-event prediction;
- planning success;
- adaptation after changed evidence;
- correction/revocation latency;
- stale-influence rate;
- provenance reconstruction;
- deletion/rebuild cost;
- compute and storage cost.

Retrieval score alone is insufficient.

### J2: pinned JEPA comparator

Only after J1 defines the matched workload:

- select a reproducible JEPA-family implementation/checkpoint;
- pin exact source, version, model/checkpoint, license, and hardware assumptions;
- reproduce only the behaviors relevant to the comparison;
- preserve negative results;
- do not require the comparator to conform to Agent Memory before measuring its capability advantage.

## Promotion decision

No architecture is protected from the result.

Possible conclusions include:

- no doctrine change;
- add latent predictive state as a first-class derived memory family;
- prefer a dual-plane architecture;
- relax an existing assumption that explicit memory should be the primary operational representation;
- add new lifecycle/rebuild semantics if current contracts are genuinely insufficient;
- reject JEPA for a target deployment profile where deletion, scope, cost, or inspectability dominates its capability advantage.

The decision must identify **which deployment profile and which dimension** it applies to.

## Stop lines

Do not:

- convert Meta benchmark claims into Agent Memory benchmark claims;
- call JEPA universally superior without a matched task;
- reject JEPA because latent state is opaque;
- accept JEPA because benchmark numbers are impressive;
- make a JEPA-specific canonical schema before the representation-neutral contract fails;
- require a JEPA comparator to inherit current architecture before testing whether current architecture is the thing that should change.
