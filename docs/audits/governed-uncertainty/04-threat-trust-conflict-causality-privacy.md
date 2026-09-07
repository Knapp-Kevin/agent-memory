# Governed Uncertainty Audit: Slice 4

## Scope

This slice evaluates the reserved foundational slots:

- `15-memory-threat-model.md`
- `16-source-trust-and-reputation.md`
- `17-conflict-resolution-engine.md`
- `18-temporal-causality-layer.md`
- `19-privacy-and-sensitivity-classifier.md`

## Baseline

```text
baseline_main_commit: 2a073e01d820905de2e1bedf363c46c88469fbad
baseline_source: merged PR #35 / governed uncertainty audit slice 3
```

## Baseline finding: documents absent

All five filenames were explicitly reserved by the architecture roadmap but did not yet exist on `main`.

This is recorded as **ABSENT**, not assigned a misleading percentage score.

Related concepts existed elsewhere in the doctrine, but no dedicated documents owned the complete boundaries, interfaces, threat cases, or conformance requirements.

| Document | Baseline | Material doctrine already scattered elsewhere |
|---|---|---|
| `15-memory-threat-model.md` | ABSENT | poisoning traps, PAMA, provenance, scope, forgetting |
| `16-source-trust-and-reputation.md` | ABSENT | evidence quality, provenance, source authority |
| `17-conflict-resolution-engine.md` | ABSENT | dispute/correction lifecycle, contradiction pressure |
| `18-temporal-causality-layer.md` | ABSENT | stale/superseded memory, prospective memory, lifecycle time |
| `19-privacy-and-sensitivity-classifier.md` | ABSENT | scope, Vault privacy, deletion, retrieval admission |

## Research posture

This slice used freely inspectable research to challenge and refine the architecture, including current open work on:

- memory poisoning and sleeper poisoning
- origin/authority laundering
- explicit memory isolation
- latent source preferences
- belief memory under partial observability
- provenance and execution tracing
- persistent-agent privacy and extraction
- deletion residue across derived memory

Research is cited inside the relevant doctrine documents as evidence or challenge material. It does not automatically create doctrine.

## Documents created

### 15 memory threat model

Adds:

- integrity, confidentiality, authority integrity, provenance integrity, temporal integrity, deletion fidelity, and recovery properties
- twelve major trust boundaries across write, read, action, sharing, derivation, and deletion paths
- direct and sleeper poisoning
- authority laundering
- recursive self-citation
- provenance stripping
- scope leakage
- extraction attacks
- deletion residue
- stale policy/authorization
- stochastic policy bypass
- unsafe memory composition
- estimator manipulation and calibration drift
- malicious correction and deletion abuse

### 16 source trust and reputation

Adds:

- source classes
- multidimensional trust
- estimator provenance and calibration scope
- latent model source preference as a hidden trust channel
- independent-corroboration requirements
- domain-specific reputation
- trust decay and rehabilitation
- explicit rule that trust is evidence, not authority

### 17 conflict resolution engine

Adds:

- factual, temporal, scope, source, policy, correction, estimator, representation, and procedure-version conflict
- multiple-hypothesis conflict interpretation
- finite governed resolution outcomes
- historical truth versus current truth
- correction versus supersession
- scope splitting
- conflict handling under uncertainty and consequence proportionality

### 18 temporal causality layer

Adds:

- event, observation, valid, transaction, decision, supersession, and expiry time
- deterministic chronology versus probabilistic causal attribution
- causal relation epistemic status
- stale versus false
- supersession and historical preservation
- temporal retrieval
- causally grounded retrieval
- prospective memory and action-time authority revalidation
- procedural drift

### 19 privacy and sensitivity classifier

Adds:

- sensitivity taxonomy and handling dimensions
- explicit unknown/uncertain state
- write-path privacy
- candidate retrieval versus recall admission
- destination-aware context exposure
- minimization
- derived-memory privacy
- composition and cross-session leakage
- deletion fidelity and receipts
- extraction resistance
- multi-agent privacy

## Post-creation governed-uncertainty scores

| Document | GU-1 | GU-2 | GU-3 | GU-4 | GU-5 | GU-6 | GU-7 | GU-8 | GU-9 | GU-10 | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `15-memory-threat-model.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 100% |
| `16-source-trust-and-reputation.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | N/A | 4 | 4 | 100% |
| `17-conflict-resolution-engine.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 100% |
| `18-temporal-causality-layer.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | N/A | 4 | 4 | 100% |
| `19-privacy-and-sensitivity-classifier.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | N/A | 4 | 4 | 100% |

`N/A` is used where bounded stochastic action is not materially owned by the document.

## Important doctrine refinements

1. **Conflict resolution is not globally deterministic.** Conflict interpretation may remain probabilistic; resolution consequences are governed.
2. **Trust is not authority.** Source reliability influences evidence weighting, not permission.
3. **Time is not causality.** Exact chronology may coexist with uncertain causal inference.
4. **Unknown sensitivity is not non-sensitive.** Consequence policy must handle classification uncertainty explicitly.
5. **Threat detection is not the security boundary.** Probabilistic attack detection can improve defense, but ACL, scope, authority, and action-set controls must remain enforceable even when detection fails.
6. **Deletion is a graph problem.** Raw-record deletion is insufficient when derived memory remains recoverable.

## Verification requirements

- [x] confirmed docs 15-19 did not exist at baseline
- [x] created all five reserved foundation documents
- [x] each document explicitly separates probabilistic interpretation from authority
- [x] each document defines deterministic/formally bounded consequences where material
- [x] each document includes falsifiable conformance cases
- [x] open research is used as support/challenge material rather than proof by citation volume
- [ ] final branch diff reviewed against `main`
- [ ] PR head verified mergeable
- [ ] commit status checked
- [ ] merged using exact verified head SHA

## Next slice

Audit the newer interdisciplinary theory documents `20` through `24`. Because those documents introduced the governed-uncertainty thesis, the audit should be adversarial: look for internal contradictions, overclaimed biological analogy, missing challenge evidence, or places where the newer theory itself fails the rubric it created.
