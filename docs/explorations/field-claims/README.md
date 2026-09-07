# External Field-Claim Research Registry

Status: **exploratory research intake** under #138 and #67. This directory is not canonical doctrine.

## Purpose

This registry converts recurring community, benchmark, implementation, paper, and field-guide claims into bounded research records instead of leaving them as an indefinitely growing issue thread.

The governing distinction is:

```text
discovery input
!= verified claim
!= reproduced behavior
!= doctrine
```

Origin establishes provenance. It does not establish evidentiary strength or promotion authority.

The machine-readable registry is [`registry.json`](registry.json).

## Intake rule

A new external claim should enter the registry only when it can be stated as a falsifiable or auditable challenge to Agent Memory.

A record should identify, where available:

- exact discovery source;
- claim being made;
- architecture or failure class;
- evidence level;
- current Agent Memory position;
- supporting and challenging evidence;
- reproducible implementation, dataset, or harness;
- proposed experiment;
- result;
- doctrine impact;
- canonical tracking issue.

If the exact source is not yet pinned, the record must say so. A community theme is not upgraded into a sourced claim by paraphrasing it confidently.

## Disposition vocabulary

```text
resolved_existing_contract
active_successor
needs_bounded_successor
parent_research_track
rejected_or_unsubstantiated
```

### `resolved_existing_contract`

The challenge was useful, but current doctrine/evidence already addresses it sufficiently for the claim as stated. This does not mean every implementation has proven the behavior.

### `active_successor`

The claim exposed useful work that now has a finite dedicated issue. Further implementation/research belongs there rather than keeping #138 open as a proxy.

### `needs_bounded_successor`

The claim remains materially unresolved and should receive a finite child issue before #138 is closed.

### `parent_research_track`

The question is properly owned by #67 or another architecture-family parent and does not need duplicate issue state here.

### `rejected_or_unsubstantiated`

The claim was checked and did not earn further work. Preserve the rejection and evidence rather than silently deleting it.

## Current reconciliation

The original #138 feed has already produced concrete work:

- #146 established source-neutral evidence promotion and a reusable claim/evidence record;
- #147 closed fresh-identity re-entry of corrected/rejected values;
- #148 generalized forbidden-hit lifecycle assertions;
- #149 proved repetition/use cannot manufacture corroboration;
- #173 owns the external poisoning-control crosswalk;
- #227 owns autonomous consolidation, background maintenance, and evidence-fusion pressure tests;
- #230 owns matched explicit/retrieval/latent/hybrid operational-memory benchmarking, including hidden-memory attribution requirements;
- #67 remains the architecture-family research parent.

This is the intended lifecycle for a field claim:

```text
discovery
 -> structured record
 -> primary/reproducible evidence
 -> bounded experiment or successor issue when justified
 -> result
 -> doctrine impact: none | clarification | candidate change
```

#138 should not remain open merely because new opinions will continue to appear on the internet. Humanity has solved that particular supply problem.

## Promotion boundary

Before a registry item changes canonical docs, ADRs, schemas, fixtures, profiles, or conformance claims:

1. bind the exact source and claim;
2. identify primary/reproducible evidence;
3. preserve counterevidence and boundary conditions;
4. run an executable test where the claim is testable;
5. state exactly what the result proves and does not prove;
6. promote only through the consequence-appropriate governance path.

A registry row is research bookkeeping, not evidence that the row's claim is true.
