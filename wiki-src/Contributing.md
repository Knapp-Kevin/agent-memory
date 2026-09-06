# Contributing

Agent Memory welcomes contributions that sharpen boundaries, add evidence, expose failure modes, improve machine-readable contracts, or challenge architectural assumptions constructively.

## Choose the right contribution path

| Contribution | Best entry point |
|---|---|
| Concrete bug or documentation defect | **Bug or documentation defect** issue form |
| Doctrine or architecture change | **Doctrine or architecture proposal** issue form |
| Research, benchmark, or external evidence | **Research or evidence submission** issue form |
| Runtime mapping or conformance result | **Implementation or conformance evidence** issue form |
| Security vulnerability | Follow `SECURITY.md`; do not publish exploit details |
| General question or exploratory discussion | GitHub Discussions |

Repository issues: https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/new/choose

## Evidence standard

For consequential changes, identify where possible:

```text
supporting evidence
challenging evidence
boundary conditions
implementation evidence
conformance evidence
known uncertainty
```

A contribution that disproves a favorite assumption can be more valuable than one that confirms it.

## Rights and attribution

Before introducing external text, code, diagrams, tables, figures, screenshots, or other expressive material, read the source-rights policy.

Default rule:

> **Public accessibility does not imply reuse permission. Citation does not imply a license.**

Prefer direct links and independent synthesis unless stronger reuse is necessary and the rights basis is verified.

## Doctrine discipline

Preserve the core separations unless the contribution explicitly proposes changing them:

```text
identity != memory
retrieval != memory
confidence != authority
trust != authority
relevance != permission
saturation != truth
utility != deletion authority
proposal != commit
adaptation != authority
memory != procedure
procedure != permission
permission != governance
```

## Machine-readable changes

Schema and fixture changes should preserve semantic compatibility where intended and make semantic migrations explicit where meaning changes.

A fixture should isolate a meaningful failure mode and clearly distinguish expected behavior from runtime proof.

## Validation

Repository validation currently includes fixture invariants, JSON Schema checks, source-rights validation, doctrine-boundary checks, calibration consistency, and documentation links.

Run the relevant validators before submitting a PR.

## Issue labels are mandatory

Every issue in Agent Memory must carry at least one label. The issue forms apply labels automatically and a repository workflow restores the baseline `agent-memory` label if the last label is removed.

## Governance

The repository is stewarded under MythologIQ Labs. Kevin R. Knapp remains the current maintainer/doctrine owner, and native authorship provenance such as PAMA remains attributed to its actual originator.

Organization stewardship does not rewrite authorship history.

## Canonical sources

- Contributing guide: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/CONTRIBUTING.md
- Governance: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/GOVERNANCE.md
- Security policy: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/SECURITY.md
- Source-rights policy: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/SOURCE_RIGHTS_POLICY.md
