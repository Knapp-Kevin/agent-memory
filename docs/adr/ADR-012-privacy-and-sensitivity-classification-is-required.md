# ADR-012: Privacy and Sensitivity Classification Is Required

## Status

Accepted

## Context

Agentic memory systems may store or recall personal, organizational, security, financial, health, credential, code, policy, or public information.

A memory system that cannot represent sensitivity cannot reliably decide what may be stored, recalled, summarized, exported, shared, corrected, or deleted.

Local-first storage helps, but it is not enough. Sensitive memory can still be recalled into the wrong context, shared with the wrong actor, inferred through composition, or retained after a nominal deletion.

## Decision

Privacy and sensitivity classification are first-class memory-governance concerns.

Classification may be probabilistic or multi-label. Storage, recall, sharing, export, and deletion consequences remain policy-governed.

Required invariant:

```text
classifier_uncertain != non_sensitive
```

Canonical document:

- [`../19-privacy-and-sensitivity-classifier.md`](../19-privacy-and-sensitivity-classifier.md)

## Consequences

### Positive

- prevents overbroad recall and disclosure
- improves consequence-aware PAMA decisions
- supports local-first and encrypted boundaries
- enables conformance tests for cross-user leakage, extraction, composition leakage, and deletion residue

### Negative

- requires sensitivity taxonomy and policy
- may require implementation-specific classifiers and calibration
- may reduce recall convenience when sensitivity is unclear

## Required handling dimensions

At minimum, policy should be able to distinguish:

- storage permission/location
- retrieval permission
- context destination
- sharing/export scope
- encryption
- retention period
- deletion mode
- audit/review requirements

## Acceptance scope

Accepted establishes privacy and sensitivity handling as canonical doctrine. It does not claim one classifier is reliable enough for all domains or consequences.

## Doctrine

Sensitivity can be uncertain.

Permission to expose memory cannot be inferred from that uncertainty.
