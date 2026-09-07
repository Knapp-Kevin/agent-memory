# Privacy and Sensitivity Classifier

> Canonical requirement: [ADR-012](adr/ADR-012-privacy-and-sensitivity-classification-is-required.md)

## Purpose

Persistent memory changes privacy from a one-response concern into a lifecycle concern.

Sensitive information can be exposed when it is:

- written
- transformed
- summarized
- embedded
- retrieved
- composed with other memory
- exported
- shared across agents
- retained after deletion

The sensitivity classifier helps estimate what handling a memory may require.

It does not grant permission. Permission belongs to PAMA: every storage, sharing, export, or deletion consequence a sensitivity estimate suggests is authorized (or refused) through the mutation-authority path of [`04-governance-and-pama.md`](04-governance-and-pama.md). Classifier output enters that path as one evidence signal — weighted per [`16-source-trust-and-reputation.md`](16-source-trust-and-reputation.md) where source-derived — and sensitivity constraints are enforced at recall time by the governed recall planner of [`26-governed-recall-planner.md`](26-governed-recall-planner.md).

> Sensitivity classification may be probabilistic. Storage, recall, sharing, export, and deletion consequences must remain governed.

## Core rule

```text
classifier uncertain != non-sensitive
```

A classifier's inability to identify sensitivity is not evidence that broad use is safe.

## Sensitivity classes

Implementations may define their own taxonomy, but should be able to represent categories such as:

- public
- internal
- personal
- personally identifying
- confidential
- credential / secret
- security-sensitive
- financial
- health
- legal / compliance
- organizationally restricted
- user-private preference or history
- unknown / unclassified

Multi-label classification may be necessary.

## Handling dimensions

Sensitivity should influence distinct decisions rather than one universal flag:

```text
may_store
storage_location
must_encrypt
may_retrieve
who_may_retrieve
may_enter_model_context
may_summarize
may_export
may_share_cross_agent
may_share_cross_tenant
retention_period
deletion_mode
audit_requirement
human_review_requirement
```

A memory can be permitted for local encrypted storage but prohibited from external model context or cross-agent sharing.

## Classification record

A material classification should preserve:

```text
memory_id
labels
classifier_id
classifier_version
calibration_version
confidence_or_probability
uncertainty
policy_context
scope
source_refs
classified_at
expires_or_recheck_at
```

## Deterministic substrate

Where policy defines them, the following should remain strict:

- tenant identity
- ACL membership
- explicit user restrictions
- credential type when exact schema identifies it
- encryption requirements
- prohibited export rules
- policy version
- deletion request state

Do not replace exact metadata with model classification when exact metadata exists.

## Probabilistic sensitivity classification

Models may identify sensitive content that lacks deterministic labels.

Examples:

- free-text health information
- implicit personal relationships
- secrets embedded in logs
- inferred financial data
- security-relevant operational details

The classifier may output:

```text
labels: [personal, financial]
confidence: 0.78
uncertainty: medium
```

Policy decides the consequence.

## Conservative uncertainty handling

For low-cost reversible actions, policy may tolerate uncertainty.

For high-consequence disclosure, policy should generally become stricter as uncertainty rises.

Example:

```text
local ephemeral use + uncertain sensitivity -> may allow with restricted scope
cross-tenant export + uncertain sensitivity -> block or require review
```

This is consequence proportionality, not a universal rule that uncertain data must always be blocked.

## Privacy across the write path

Before durable storage, evaluate:

- purpose
- source authority
- sensitivity
- user expectations
- retention need
- encryption/storage boundary
- whether a less revealing representation would suffice

Possible outcomes:

```text
do_not_store
store_ephemeral
store_redacted
store_encrypted_local
store_with_expiry
store_durable_with_restricted_scope
require_review
```

## Privacy across retrieval

Retrieval should be a two-stage process:

```text
candidate generation
  -> recall admission
```

Semantic relevance is not enough.

Recall admission should evaluate:

- requester identity
- tenant
- purpose
- sensitivity
- certification/dispute state
- policy
- downstream destination

## Context exposure

A memory allowed in storage is not automatically allowed in every context window.

Destination matters:

```text
local deterministic tool
local model
external model provider
human UI
another agent
external API
```

Policy can authorize different representations for different destinations.

## Minimization

Prefer the least revealing memory representation that preserves legitimate utility.

Possible transformations:

- redact identifiers
- replace raw text with structured attributes
- summarize only relevant non-sensitive facts
- tokenize or reference secrets rather than copy them
- store exact secret in dedicated vault while memory stores a capability reference

Minimization should preserve enough provenance to support correction and deletion.

## Derived-memory privacy

Summaries and semantic memories can still contain sensitive information.

Required rule:

```text
transformation does not erase privacy obligations
```

Derived memories should inherit or recompute appropriate sensitivity and retain derivation links.

## Composition leakage

Several non-sensitive memories may combine to reveal sensitive information.

Example:

```text
memory A: travel date
memory B: home address
memory C: household schedule
```

The combination may create a higher-risk disclosure than any one item.

Privacy governance should therefore consider context composition, not only item-level classification.

## Cross-session inference

Persistent memory can allow later inference that was impossible in one session.

This should be considered when evaluating:

- longitudinal behavior
- identity linkage
- health/financial patterns
- relationship inference
- work habits
- location patterns

## Deletion fidelity

Deletion must account for:

- raw records
- summaries
- embeddings/index entries
- graph relations
- caches
- semantic consolidation
- derived preference models
- cross-agent copies where governed by the system

Deletion modes may include:

```text
hide_from_recall
archive
redact
tombstone
cryptographic_delete
full_pipeline_purge
```

The requested privacy outcome determines which mode is sufficient.

## Deletion receipt

A consequential deletion should be able to record:

```text
requester
authority
memory_refs
derived_refs
deletion_mode
policy_version
completed_steps
residual_known_copies
verification_result
timestamp
```

## Extraction resistance

Sensitive memory stores should assume adversarial queries may attempt reconstruction.

Controls may include:

- least-privilege recall
- purpose-aware access
- response minimization
- extraction-rate limits
- anomaly detection
- structured secret isolation
- refusal to expose raw memory state when unnecessary
- sensitive-access audit trails

Probabilistic detection is useful, but explicit ACL and scope rules should not depend on attack detection succeeding.

## Multi-agent privacy

Sharing memory across agents introduces additional questions:

- who owns the memory?
- did the user consent to this agent receiving it?
- may the receiving agent persist it?
- may it re-share it?
- which policy version travels with it?
- how does deletion propagate?

Shared memory should carry scope and handling requirements as data, not tribal knowledge between services.

## Conformance cases

### High-relevance wrong-tenant memory

Expected:

```text
candidate may rank first
admission blocks it
```

### Uncertain sensitivity before export

Expected:

```text
uncertainty does not coerce to public/non-sensitive
```

### Raw deletion with derived summary

Expected:

```text
deletion verification detects residual derived memory
```

### Credential in free text

Expected:

```text
classifier may detect it probabilistically
explicit secret policy controls storage and recall
```

### Composition leakage

Expected:

```text
individually allowed memories can still trigger context-level privacy control
```

### Cross-session extraction probing

Expected:

```text
sensitive data is not released merely because attacker reconstructs a semantically plausible request
```

## Research signals

- [Agents That Know Too Much: A Data-Centric Survey of Privacy in LLM Agents](https://arxiv.org/abs/2606.26627) emphasizes privacy risks across agent data surfaces, persistent memory, delegated permissions, compositional inference, and cross-session leakage.
- [Deployment-Time Memorization in Foundation-Model Agents](https://arxiv.org/abs/2606.10062) studies the privacy-utility tradeoff of persistent agent memory and reports deletion residue in derived memory when only raw records are deleted.
- [Spore: Efficient and Training-Free Privacy Extraction Attack on LLMs via Inference-Time Hybrid Probing](https://arxiv.org/abs/2604.23711) studies inference-time extraction attacks against agent memory, reinforcing that alignment alone is not an access-control mechanism.
- [AgentSys](https://arxiv.org/abs/2602.07398) provides evidence that explicit isolation and schema-validated boundary crossing can reduce prompt-injection risk in agent memory flows.

## Doctrine

Privacy is not a label attached at write time.

It is a lifecycle property governing **where memory may live, who may retrieve it, what representation may be exposed, how it may be combined, and whether forgetting actually removes what it promised to remove**.
