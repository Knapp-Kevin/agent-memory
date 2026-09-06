# ADR-015: Retention, Deletion, and Tombstones Are Required

## Status

Accepted

## Context

A governed memory system must distinguish pruning, archival, suppression, redaction, correction, tombstoning, cryptographic deletion, and full deletion propagation.

A memory system that can remember but cannot explain deletion is not governed. It is a hoarder with APIs.

## Decision

Agent Memory defines explicit retention, deletion, redaction, archival, and tombstone semantics.

Deletion is not pruning. Predicted low utility is not deletion authority. Removing the raw record is not complete deletion if summaries, embeddings, graphs, caches, or consolidated memories still retain recoverable content.

## Required distinctions

- active recall removal
- suppression
- archival retention
- tombstone retention
- redacted retention
- cryptographic deletion
- source deletion
- derived-memory deletion
- exported-memory deletion
- certification revocation
- verified full-pipeline purge

## Consequences

### Positive

- prevents silent disappearance and incomplete deletion
- supports privacy, consent, retention, and audit policy
- preserves accountability where appropriate
- makes forgetting modes explicit

### Negative

- creates tension between deletion and evidence retention
- requires dependency traversal across derived memory
- requires policy-specific verification

## Acceptance evidence

Canonical contract:

- [`../28-retention-deletion-and-tombstones.md`](../28-retention-deletion-and-tombstones.md)

Repository fixtures include:

- `deletion-residue.json`
- `irreversible-deletion-under-uncertain-utility.json`

The memory-unit schema now represents retention/tombstone state, and the conformance schema includes deletion-residue metrics.

## Acceptance scope

Accepted establishes the forgetting/deletion mode distinctions as canonical doctrine. It does not claim current runtimes can guarantee full deletion from every derived or external system.

## Doctrine

Forgetting is a governed family of operations.

Irreversible deletion requires stronger authority than reversible pruning or archival.
