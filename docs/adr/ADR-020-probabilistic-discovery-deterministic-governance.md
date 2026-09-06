# ADR-020: Probabilistic Discovery, Governed Consequences

> Filename retained for decision-history continuity. The refined doctrine no longer assumes every governance mechanism must be computationally deterministic.

## Status

Accepted

## Context

Agentic memory operates under uncertainty.

Candidate extraction, semantic retrieval, contradiction detection, source trust, salience, relevance, abstraction, causal inference, sensitivity, future utility, and risk estimation may all depend on learned, heuristic, probabilistic, or stochastic mechanisms.

Memory also contains consequences too important to delegate directly to uncertain inference:

- canonical promotion
- durable mutation
- cross-tenant or cross-user disclosure
- irreversible deletion
- policy mutation
- certification
- inherited-memory propagation
- authority changes
- preservation or destruction of evidence

A binary choice between "deterministic memory" and "probabilistic memory" is therefore insufficient.

## Decision

Adopt a **governed uncertainty** architecture:

```text
probabilistic / learned / heuristic epistemics
        |
        v
explicit policy + authority envelope
        |
        v
permitted / prohibited / deferred actions
        |
        v
optional deterministic or stochastic selection
AMONG PERMITTED ACTIONS ONLY
        |
        v
committed consequence + provenance + receipt
```

Short form:

> **Probabilistic epistemics. Governed consequences.**

Operational form:

> **Uncertainty may propose. Authority constrains.**

The desired property is **authority boundedness and reconstructability**, not fictional certainty.

## Rule 1: estimator output is not authority

Learned, heuristic, or probabilistic components MAY produce:

- beliefs and alternative hypotheses
- confidence or probability estimates
- relevance and trust scores
- sensitivity or risk estimates
- contradiction likelihoods
- rankings
- memory candidates
- proposed mutations
- proposed retrieval sets
- proposed consolidation or forgetting actions

They MUST NOT acquire mutation, promotion, deletion, sharing, certification, or policy authority merely from those outputs.

## Rule 2: governance defines the action envelope

For every consequential operation, a versioned governance process MUST determine permitted, prohibited, review-required, or deferred outcomes using applicable:

- identity
- current state/version
- scope/tenant
- actor authority
- sensitivity
- provenance
- lifecycle state
- risk and reversibility
- certification state
- policy
- estimator uncertainty when relevant

A learned component MUST NOT expand its own permitted action set.

## Rule 3: stochastic behavior may remain inside the envelope

The architecture MAY permit stochastic or learned selection among already-authorized actions.

Required invariant:

```text
selected_action ∈ permitted_action_set
```

Randomness does not create permission.

## Rule 4: consequence strength is proportional

The strongest boundary belongs around operations that:

- create canonical or certified state
- irreversibly erase data or evidence
- cross user, tenant, organization, or trust-domain boundaries
- change policy or authority
- expose sensitive memory
- create inherited behavioral control
- trigger external destructive side effects

High model confidence does not reduce those requirements by itself.

## Rule 5: uncertainty remains visible

Where material, the decision record SHOULD preserve:

- signal semantics
- estimator/model identity and version
- calibration reference and scope
- uncertainty or disagreement
- candidate/proposed action
- policy version
- authority and scope
- permitted and prohibited actions
- selected action and selection mode
- committed result

A 0-to-1 score MUST NOT be assumed to be a calibrated probability unless the estimator defines it that way.

## Rule 6: deterministic does not mean static or correct

Reproducible policy can still be badly designed.

Fixed thresholds MUST NOT be assumed safe merely because they are deterministic.

Thresholds and classifiers influencing consequential transitions SHOULD be calibrated, stress-tested near decision boundaries, and re-evaluated under drift.

## Rule 7: read-path governance is required

A memory safe to store MAY become unsafe when retrieved under a different scope or combined with other memories.

Policy enforcement must therefore exist on both write and read paths, with context/composition checks where consequence warrants them.

## Rule 8: formally bounded probabilistic guarantees are allowed

Absolute deterministic safety may be impossible in environments with hidden parameters or uncertain models.

A formally bounded probabilistic guarantee MAY be used when:

- the guarantee type is explicit
- residual risk is measured
- policy explicitly accepts that residual risk
- stronger exact constraints remain enforced where available
- the guarantee can be independently evaluated

Calling a system "formally bounded" without specifying the bound is not a guarantee.

## Rule 9: learned is not synonymous with probabilistic

A learned component may be deterministic at inference time. A hand-written heuristic may be uncertain without representing probability.

The architecture should classify a component by what its output **means** and what authority it has, not by whether it contains machine learning.

## Rule 10: governance begins at contract design

Authority, scope, policy versioning, proposal-versus-commit boundaries, and decision receipts must be defined before implementations stabilize consequential memory APIs.

Governance is not a later hardening phase.

## Consequences

### Positive

- preserves adaptive and learned memory behavior
- prevents confidence from becoming authority
- supports uncertainty-preserving belief memory
- makes consequential decisions auditable
- permits stochastic optimization inside bounded action spaces
- separates policy drift from estimator drift
- supports read-time and composition security

### Negative

- requires richer schemas and receipts
- adds explicit policy and transition semantics
- requires calibration and drift evaluation
- can add latency to high-consequence operations
- formally bounded guarantees can be difficult to specify for complex compositions

### Doctrine risks

- deterministic rules may reproduce a bad assumption perfectly
- estimator and policy may become tightly coupled
- hidden stochasticity may escape receipts
- `require_human_review` may create false assurance if the reviewer lacks evidence or authority
- over-conservative policy can destroy useful adaptation
- flexible policy can become a euphemism for model self-authorization
- correct authorization can become stale before commit
- safe components can compose into unsafe behavior

## Rejected alternatives

### Fully deterministic memory control

Rejected as universal doctrine because relevance, ambiguity, trust, contradiction, sensitivity, abstraction, retrieval, and risk frequently involve uncertainty.

### End-to-end model-directed memory

Rejected for consequential transitions because cognition and authority would collapse into one failure domain.

### Deterministic thresholds as primary governance

Rejected as insufficient because thresholds can be miscalibrated, brittle, domain-specific, attacked, or invalid under drift and composition.

### Human approval for every mutation

Rejected as a default because it creates a human bottleneck and prevents useful autonomous low-risk adaptation.

## Acceptance evidence

ADR-020 was accepted only after the repository accumulated executable evidence for all fourteen required boundaries:

1. high-confidence false memory cannot self-promote
2. high-relevance wrong-tenant memory cannot enter context
3. probabilistic contradiction detection cannot silently overwrite certified state
4. stochastic retrieval/action selection cannot bypass policy filters
5. uncertain sensitivity is handled safely for high-consequence disclosure
6. predicted low utility cannot independently authorize irreversible deletion
7. unsafe multi-memory composition is tested
8. policy-version drift is distinguishable from estimator/model drift
9. concurrent conflicting mutations do not silently become last-writer-wins
10. selected action cannot escape its permitted set across stochastic trials
11. authority and consequence remain reconstructable from receipts
12. derived-memory deletion residue is tested
13. at least one implementation is mapped end-to-end from estimate -> governance -> action set -> commit
14. at least one adversarial challenge causes a documented boundary, correction, or rejection rather than being ignored

The acceptance audit is recorded in [`../audits/governed-uncertainty/09-adr-020-runtime-evidence-acceptance-audit.md`](../audits/governed-uncertainty/09-adr-020-runtime-evidence-acceptance-audit.md). Runtime evidence includes the pinned real-substrate governed adapter, stochastic containment, concurrency conflict evidence, deletion-completeness evidence, the P5 security scorecard, the P6 Mem0 comparator, and portable/external action-evidence negative paths.

Acceptance is a **doctrine-maturity decision**, not a claim that the narrow reference adapter satisfies every cumulative Agent Memory conformance level or that every production implementation conforms.

Canonical evidence locations:

- [`../06-conformance-test-plan.md`](../06-conformance-test-plan.md)
- [`../24-determinism-probability-and-governed-uncertainty.md`](../24-determinism-probability-and-governed-uncertainty.md)
- [`../25-governed-uncertainty-documentation-conformance-audit.md`](../25-governed-uncertainty-documentation-conformance-audit.md)
- [`../audits/governed-uncertainty/`](../audits/governed-uncertainty/)
- [`../programs/runtime-evidence/`](../programs/runtime-evidence/)

## Open questions

- Which checks require strict computational determinism versus explicit bounded semantics?
- When are probabilistic safety guarantees sufficient?
- How should uncertainty propagate through consolidation and derivation?
- Can learned governance itself be certified inside a constrained scope?
- What formal model best represents a permitted action envelope?
- How should policy adapt under drift without becoming hidden self-mutation?
- Which uncertainty representations are useful enough to standardize?

## Research posture

The decision should continue to be challenged using freely inspectable research where practical, implementation evidence, adversarial fixtures, and negative results.

Citation count is not confidence.

## Doctrine

The system may be uncertain about what is true.

It must remain explicit about what that uncertainty is allowed to change.
