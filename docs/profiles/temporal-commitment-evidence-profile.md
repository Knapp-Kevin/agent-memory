# Temporal Commitment Evidence Profile

Status: reference profile under #259. ADR-031 is Accepted (2026-08-13).

## Boundary

Agent Memory separates four claims:

```text
TemporalCommitment
  -> exact content identity
  -> signer attestation
  -> optional external witness evidence
  -> separate currentness/governance evaluation
```

A material temporal change must alter commitment identity. None of these evidence layers independently establishes truth, currentness, authority, approval, or execution.

## Temporal commitment

`schemas/temporal-commitment.schema.json` binds event/payload identity, temporal claims, scope, domain-schema identity, projection profile/version, and any declared ordering relation.

The first optional content-reference profile is the existing UOR-Addr v0.2.0 JSON profile. UOR answers what exact canonical object is referenced. It does not establish signer trust or authority.

## Signer evidence

`schemas/temporal-signer-attestation.schema.json` binds the exact content reference and the content-reference profile to signer evidence. The Python reference uses Ed25519 as an evidence profile, not normative doctrine.

```text
valid signature + untrusted/revoked signer
-> cryptographically valid
-> trusted_signer = false
-> authority_effect = none
```

A valid signature over a claimed event time proves that the signer committed to the claim. It does not establish trusted wall-clock time.

## Linear ordering profile

The first ordering profile commits to:

```text
stream_ref
sequence
predecessor_reference_profile
predecessor_ref
```

The evaluator recomputes predecessor identity and checks reference profile, scope, stream, and sequence. It deliberately reports:

```text
complete_history_proven = false
non_equivocation_proven = false
```

A predecessor chain proves only its declared local relation. Stronger history claims require an appropriate anchor, coordinator receipt, consistency proof, or verifiable-log receipt.

Fork detection verifies each content-ref/commitment binding before reporting sibling descendants. It does not select a canonical branch.

## External witness evidence

`schemas/temporal-external-witness.schema.json` binds both the subject reference and its reference profile. Adapters may represent already-verified timestamp, transparency, inclusion, consistency, or freshness evidence.

The generic profile does not implement those external services.

```text
witnessed existence by T != event occurred at T
```

## Currentness

`schemas/temporal-currentness-evaluation.schema.json` records append-only current applicability without rewriting the signed historical commitment.

```text
historical_commitment_mutated = false
cryptographic_validity_changed = false
authority_effect = none
```

A later correction or supersession can therefore change current applicability while preserving what was historically committed.

## UOR boundary

UOR-Addr remains optional. The address function is injected. The #259 workflow addresses temporal objects with exact `uor-addr==0.2.0`; the independent `UOR Addr Compatibility` workflow proves that release's Python/Rust content-reference contract on the same PR head.

```text
UOR identity != signer identity != trusted time != currentness != PAMA authority
```

## Multi-writer boundary

`linear_stream` is not a universal multi-writer total-order protocol. Concurrent/shared histories may require causal predecessor sets, shared-write coordination, coordinator-issued positions, or verifiable ordered-log receipts in later profiles.

## Evidence

- `docs/research/cryptographic-temporal-commitments.md`
- ADR-031
- `reference/agentmem_ref/temporal_commitment.py`
- `reference/tests/test_temporal_commitment.py`
- `.github/workflows/temporal-commitment-evidence.yml`
- #259
