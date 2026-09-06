# ADR-031: Temporal claims require deterministic content commitments

- **Status:** Accepted
- **Date:** 2026-08-13
- **Accepted:** 2026-08-13
- **Related:** #258, #259, ADR-021, ADR-028, ADR-030

## Decision

Agent Memory adopts a layered temporal-commitment model.

Material temporal claims belong inside a deterministic content commitment when changing those claims must create a different historical identity.

Keep these evidence layers distinct:

1. exact temporal-object identity;
2. signer attestation to that exact object;
3. declared relative-order evidence;
4. optional external time/transparency evidence;
5. separate currentness and Agent Memory governance.

The governing invariant is:

> **Making a temporal claim tamper-evident does not make the claim true, current, trusted, complete, or authorized.**

Therefore:

```text
content identity != signer trust
signed time != trusted event time
predecessor chain != complete or unique history
evidence validity != memory authority
```

## Boundaries

The first optional content-reference profile uses UOR-Addr v0.2.0. UOR identifies the exact canonical temporal object. It does not establish signer trust, wall-clock truth, currentness, completeness, admission, or PAMA authority, and it is not a required core runtime.

The Python reference uses Ed25519 only as an implementation evidence profile. Algorithm and key-management choices are not canonical doctrine.

A linear predecessor profile proves only its declared local relationship. It does not prove complete history or non-equivocation without stronger anchoring/consistency evidence. Fork detection reports competing children but does not choose a canonical branch.

External witness evidence may establish a bounded claim such as existence by a time or inclusion in a verifiable structure. Witness time is not automatically event occurrence time.

Later correction, revocation, dispute, or supersession creates separate currentness evidence. It does not rewrite the historical commitment or retroactively change historical evidence validity.

None of these layers independently establishes factual truth, memory admission, current applicability, human approval, reusable authority, PAMA permission, or execution.

## Acceptance evidence

All sixteen acceptance gates are mapped in:

`docs/audits/temporal-commitments/01-adr-031-acceptance-audit.md`

Pre-acceptance exact head:

`1b02d02ef6b1d96a5c7b04515bac62ae86a15fc0`

That head passed all 25 repository workflows.

Focused artifact:

- id `9198292626`
- digest `sha256:66454918179ce3e0e9e887497d59120b1845494a9a7d62e46d2bc6f4ad15c52f`

Independent same-head UOR artifact:

- id `9198303010`
- digest `sha256:25b067fd2aba43ea1d988e62b767d6c07b2da20c1a13f6cab4dfc56dcf4f8f28`

The first green implementation was not accepted. Review required explicit reference-profile binding, verified fork-node bindings, append-only currentness/supersession evidence, non-null temporal claims, and matching light/dark visual semantics.

The Accepted head must pass the complete validation matrix before merge.

## Canonical detail

- `docs/research/cryptographic-temporal-commitments.md`
- `docs/profiles/temporal-commitment-evidence-profile.md`
- `docs/audits/temporal-commitments/01-adr-031-acceptance-audit.md`
- `reference/agentmem_ref/temporal_commitment.py`
- `reference/tests/test_temporal_commitment.py`
- `wiki-src/Cryptographic-Temporal-Commitments.md`
