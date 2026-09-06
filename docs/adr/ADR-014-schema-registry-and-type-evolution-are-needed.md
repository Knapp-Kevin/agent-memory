# ADR-014: Schema Registry and Type Evolution Are Needed

## Status

Accepted

## Context

The repository contains doctrine-level schemas used by fixtures and future implementations. As implementations adopt the doctrine, those schemas will evolve.

Without explicit schema governance, implementation-specific fields can leak into doctrine-level objects, uncertainty semantics can be lost across adapters, and migrations can become oral tradition, which is how software projects summon ghosts.

## Decision

Agent Memory defines a schema registry and type-evolution strategy.

The registry governs doctrine-level semantic types while allowing implementation-specific extension under explicit compatibility rules.

It includes representations for:

- memory identity and lifecycle state
- provenance and acquisition mode
- estimator provenance and uncertainty
- policy and authority references
- permitted-action sets
- decision receipts
- audit events
- deletion/tombstone state
- schema version and migration metadata

## Consequences

### Positive

- prevents schema drift and semantic type erasure
- supports cross-repo adoption
- enables versioned conformance fixtures
- makes migrations explicit

### Negative

- adds governance overhead
- requires compatibility and migration rules
- can slow experimentation if extension mechanisms are too rigid

## Acceptance evidence

Canonical contract:

- [`../27-schema-registry-and-type-evolution.md`](../27-schema-registry-and-type-evolution.md)

Machine-readable evidence:

- `schemas/memory-unit.schema.json`
- `schemas/conformance-report.schema.json`
- `schemas/decision-receipt.schema.json`
- `schemas/memory-audit-event.schema.json`
- `scripts/validate_schemas.py`

The memory schema was expanded additively so legacy fixtures remain valid while governed-uncertainty types become representable.

## Acceptance scope

Accepted establishes semantic schema governance as canonical doctrine. Future breaking migrations still require explicit versioning and evidence.

## Doctrine

Schemas are part of memory governance.

A memory object that cannot evolve without losing semantic meaning cannot remain canonical across implementations.
