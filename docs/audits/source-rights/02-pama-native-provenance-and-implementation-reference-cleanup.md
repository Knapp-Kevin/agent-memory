# Source Rights Audit 02: PAMA Native Provenance and Implementation Reference Cleanup

## Trigger

The repository had incorrectly represented Proportional Adaptive Mutation Authority (PAMA) alongside external and related source systems, including a source-registry record whose rights status was unresolved.

During review, Kevin R. Knapp supplied the full systems-agnostic PAMA conceptual architecture and confirmed that PAMA is his original content and is core to Agent Memory.

The same review challenged whether references to Bicameral added sufficient specific value to justify retaining a private adjacent product in active Agent Memory provenance and implementation surfaces.

## Findings

### PAMA provenance

The prior representation was materially wrong.

PAMA is not an external dependency from which Agent Memory merely synthesizes mutation-governance ideas. It is native Agent Memory doctrine authored by Kevin R. Knapp.

The supplied PAMA framework establishes, among other things:

- adaptation is not authority;
- memory is not procedure;
- procedure is not permission;
- permission is not governance;
- review belongs at promotion and consequence boundaries rather than every observation boundary;
- M0-M5 mutation target classes;
- lifecycle strength from observed through canonical, with decay/demotion paths;
- A0-A5 downstream authority classes;
- proportional handling lanes;
- adaptive charters;
- reusable capability authority ceilings;
- evidence, lineage, correction, revocation, and outcome monitoring.

### Taxonomy drift

Agent Memory's operational PAMA docs had also used the phrase `mutation classes` for operations such as promotion, correction, pruning, and policy mutation.

Those operations are valid Agent Memory policy dimensions, but they are not the same thing as PAMA's foundational M0-M5 mutation target classes.

The correction separates:

```text
PAMA target class
lifecycle strength
requested operation
downstream authority
risk
scope
reversibility
actor / charter
evidence / uncertainty
policy
```

### Adjacent private product references

The reviewed Bicameral references did not provide concrete implementation evidence or a unique architectural dependency that Agent Memory could not express directly.

Decision-continuity concepts are already representable through Agent Memory's durable-decision memory profile. Therefore active references were removed rather than preserving product adjacency as provenance.

Historical audit/governance records are not rewritten; they remain evidence of the repository's actual development history.

## Changes

- Added `docs/pama/README.md` as the canonical native PAMA foundation.
- Reworked `docs/04-governance-and-pama.md` around the native PAMA taxonomy.
- Reworked `docs/33-pama-decision-table.md` so operation/risk lookup is explicitly one projection of PAMA rather than the definition of PAMA.
- Removed PAMA from the external/material source registry.
- Removed Bicameral from the external/material source registry.
- Removed Bicameral from active source and implementation mapping surfaces.
- Reframed `docs/05-repo-implementation-map.md` around native doctrine versus related implementation systems.
- Reframed `docs/39-implementation-ownership-map.md` to separate PAMA doctrine ownership from runtime implementation ownership.
- Updated ADR-004 to record PAMA's native authorship and deployment-independent acceptance scope.
- Updated source-rights policy to distinguish native contributor-authored doctrine from external source material.
- Added CI validation to protect the native PAMA boundary and prevent unreviewed adjacent-product references from drifting back into active doctrine.

## Rights consequence

PAMA itself no longer requires an external source-rights record.

External research, standards, implementations, comments, papers, diagrams, code, or other expression used to support, challenge, align with, or implement PAMA remain governed independently by `SOURCE_RIGHTS_POLICY.md`.

Contributor authorship of PAMA does not erase third-party rights in material PAMA cites or discusses.

## Implementation consequence

PAMA doctrine ownership is resolved:

```text
PAMA doctrine owner: Agent Memory / Kevin R. Knapp
runtime PAMA implementation owner: open until implementation evidence exists
```

A runtime may host the PAMA evaluator inside another codebase, but it must preserve the authority boundary and conformance semantics.

## Audit boundary

This audit records provenance and architecture decisions. It is not a legal determination of copyright scope or an implementation-conformance claim.
