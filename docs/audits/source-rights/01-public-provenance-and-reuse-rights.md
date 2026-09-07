# Source Rights Audit 01: Public Provenance and Reuse Rights

Date: 2026-08-10

## Trigger

The source-material index identified several primary systems by name without linking publicly inspectable sources, while the repository did not yet make a hard distinction between public accessibility, provenance, and permission to reuse source expression.

The review also identified a specific authorship/provenance point: UOR Framework issue #2 was opened by Kevin R. Knapp, and the "thermodynamic ground state" framing as used in that thermodynamic memory-lifecycle proposal originated as a Kevin R. Knapp contribution.

## Risks addressed

1. Public source material could be named without a usable locator.
2. A public GitHub repository could be incorrectly treated as if every issue comment or attachment inherited the repository software license.
3. Open-access research could be incorrectly treated as openly licensed for reproduction.
4. Private canonical provenance could be replaced by an adjacent public project and thereby misrepresented.
5. Licensed code, documentation, diagrams, or other material could be reused without recording attribution, NOTICE, or modification obligations.
6. Contributor-originated work could lose provenance when posted to a third-party repository.
7. Unknown rights status could drift into copied or adapted repository content without an explicit decision point.

## Changes

### Public provenance

`docs/08-source-material-index.md` now links the most specific verified public artifact available for:

- UOR Framework issue #2
- the `maurathat` decay-calibration comment
- EvolveAI Autopoietic Memory Theory
- CodeGenome
- FailSafe VerdictArbiter
- GG-CORE as a public successor to private COREFORGE provenance

PAMA and Bicameral remain explicitly unlinked where no appropriate public canonical source has been verified.

### Provenance correction

The UOR section records:

> The "thermodynamic ground state" framing as used in that memory-lifecycle proposal is a Kevin R. Knapp contribution.

The record is deliberately phrased as authorship/provenance rather than as a claim that a short phrase or underlying idea is exclusively protectable under a particular body of law.

Third-party contributions in the same issue thread retain their own source and rights posture.

### Rights policy

Added `docs/SOURCE_RIGHTS_POLICY.md`.

The default rule is:

```text
public accessibility != reuse permission
citation != license
unknown rights -> citation or independent synthesis
```

Material reuse requires a documented basis.

### Machine-readable registry

Added:

- `sources/source-registry.json`
- `schemas/source-record.schema.json`

The initial registry covers primary architecture-provenance sources and distinguishes:

- public source
- private source
- public successor
- no verified public locator
- verified open license
- author-originated provenance
- unknown rights
- citation / synthesis posture

External research in `docs/23-research-bibliography.md` remains citation/synthesis-only by default unless material reuse is explicitly registered.

### Validation

`scripts/validate_schemas.py` now validates source-rights records and rejects, among other cases:

- duplicate source IDs
- `licensed_reuse` without a verified open-license status
- `licensed_reuse` without license identifier and license URL
- `permission_granted` without verified permission status
- author-originated reuse without matching provenance status
- reuse-oriented modes without a documented reuse basis
- unknown rights status attempting a reuse mode beyond citation or independent synthesis

The repository workflow now validates the source-rights policy and source-material index links as well.

## License spot checks

Verified during this pass:

| Source repository | Repository license | Treatment |
|---|---|---|
| UOR-Foundation/UOR-Framework | MIT | Repository license recorded, but not assumed to license third-party issue prose |
| MythologIQ-Labs-LLC/EvolveAI | Apache-2.0 | Independent synthesis preferred; direct reuse must satisfy Apache obligations |
| MythologIQ-Labs-LLC/CodeGenome | MIT | Independent synthesis preferred; copies/substantial portions preserve notice |
| MythologIQ-Labs-LLC/FailSafe | Apache-2.0 | Independent synthesis preferred; direct reuse must satisfy Apache obligations |
| MythologIQ-Labs-LLC/GG-CORE | Apache-2.0 | Public successor context only; not substituted for private COREFORGE provenance |

## Evidence boundary

This pass does **not** certify that every historical sentence in the repository is rights-clean.

It establishes:

1. a conservative reuse policy,
2. explicit primary-source rights records,
3. public provenance links where verified,
4. machine-checkable gates for future material reuse, and
5. a clear path for a deeper historical source-rights audit if evidence suggests copied or adapted expression exists.

No wholesale copying was identified during the targeted review that triggered this pass, but absence of an identified problem is not treated as legal certification.
