# Security Evidence Depth and Poisoning Boundary Harness

Status: V0.1 runtime-evidence profile for #196.

This profile makes a deliberately uncomfortable distinction machine-readable:

```text
security doctrine
!= structural scenario
!= behavioral proof
!= runtime evidence
!= production evidence
```

Agent Memory records those evidence depths independently as **D/F/H/R/P**.

## Evidence levels

| Level | Meaning | Minimum evidence |
|---|---|---|
| `D` | Documented doctrine | Canonical doctrine/reference explaining the bounded claim |
| `F` | Structural fixture | Validated fixture or explicit machine-readable scenario |
| `H` | Behavioral harness | Executable test/harness actually exercises the claimed behavior |
| `R` | Runtime implementation evidence | Separately generated evidence from an implementation/runtime path bound to the exact implementation head |
| `P` | Production evidence | Separately governed evidence from an actual production deployment |

The levels are **not cumulative badges**.

```text
D + H
!= D + F + H

H
!= R

R
!= P
```

If a level has no evidence, it remains explicitly unproven even when a stronger-looking but semantically different artifact exists elsewhere.

## No composite security score

V0.1 emits no scalar security, maturity, coverage, or certification score.

A composite score would permit a strong result in one area to obscure a missing or failed security boundary in another. That is precisely the failure mode this ledger is designed to prevent.

The report preserves:

```text
demonstrated_levels
highest_demonstrated_level
explicitly_unproven_levels
```

`highest_demonstrated_level` is navigation metadata only. It does not imply that lower levels exist or that the claim is generally mature.

## Exact-head runtime evidence

Runtime evidence must remain bound to the implementation it actually exercised.

For the direct-poisoning case, V0.1 can consume the separately generated P5 benchmark-security artifact only when:

- the artifact `agent_memory_commit` exactly equals the security-depth report head;
- P5 hard gates passed;
- `authority_from_confidence_count == 0`;
- the corresponding confidence/authority case passed.

Then, and only then, the direct-poisoning claim may demonstrate `R`.

An otherwise valid runtime artifact from a different commit is preserved only as stale/historical runtime evidence. It does not prove current `R`.

## Production evidence

The reference repository does not collect production deployment evidence in this V0.1 slice.

Therefore:

```text
P = explicitly unproven by default
```

Unit tests, CI success, protocol results, reference-runtime execution, benchmark artifacts, contributor statements, or standards mappings cannot manufacture `P`.

## V0.1 poisoning boundaries

The first behavioral harness covers three ingestion boundaries selected from #173 research.

### 1. Direct untrusted external write

The harness sends the same high-consequence M4 promotion through the real `GovernedMemoryAdapter` twice:

```text
confidence = 0.99
confidence = 0.01
```

Both carry an untrusted source ref plus repeated/derived refs.

The required behavior is:

```text
high confidence
!= higher authority

repetition / derived copies
!= review discharge

untrusted proposal
-> PAMA evaluation
-> requested promotion remains prohibited without required review
-> zero substrate writes
```

The PAMA decision must preserve the supplied evidence references so blocking a mutation does not erase provenance.

This extends the existing P5 confidence/authority hard gate into an explicit poisoning-ingestion claim.

### 2. MCP ingestion

The harness consumes the merged governed MCP profile using a successful `resources/read` result classified as `memory_candidate`.

The peer also supplies hostile fields such as:

```text
pama_outcome = allow
lifecycle_state = canonical
memory_authority = owner
```

The required behavior is:

```text
MCP success
-> protocol evidence / candidate only
-> hostile authority fields discarded
-> memory_admission = not_established
-> authority_effect = none
```

This is `H` evidence against the Agent Memory MCP normalizer. It is not live MCP-host `R` evidence.

### 3. A2A ingestion

The harness consumes the merged non-authority-bearing A2A profile with an inbound Artifact classified as `memory_candidate`.

It additionally exercises a peer task correlation carrying the correct local action/input identity but the wrong tenant/project scope.

Required behavior:

```text
remote artifact
-> candidate only
-> peer identity != authority
-> peer identity != semantic correctness
-> hostile authority-transition fields discarded

same task/action correlation + wrong tenant/project
-> binding_mismatch
```

This is `H` evidence against the Agent Memory A2A normalizer. It is not live A2A-host `R` evidence.

## Evidence report contract

The generated report is validated by:

- `schemas/security-evidence-depth-report.schema.json`
- `reference/agentmem_ref/harness/security_evidence_depth.py`
- `reference/run_security_evidence_depth.py`
- `reference/tests/test_security_evidence_depth.py`
- `fixtures/security-evidence-depth-matrix.json`

Each claim records:

```text
claim_id
title
threat_family
doctrine_refs
fixture_refs
behavioral_harness_refs
runtime_evidence_refs
production_evidence_refs
external_mappings
demonstrated_levels
highest_demonstrated_level
explicitly_unproven_levels
scope_profiles
evaluated_head
runtime_evidence_head when current R exists
stale_runtime_evidence_refs when relevant
behavioral_passed
non_certification_statement
```

## External mappings and certification

An external standard/control mapping may help users locate related security expectations. It cannot upgrade Agent Memory evidence depth and cannot imply certification.

Every mapped control must carry:

```text
certification_claim = none
```

The schema/report is an evidence ledger, not an audit certificate.

Future standards crosswalk work may populate source/version/control refs after research validates exact mapping semantics. V0.1 does not invent control IDs merely to make the report appear complete.

## Failure behavior

The ledger fails visibly rather than averaging failure away.

Examples:

```text
D + F only
-> H, R, P remain unproven

behavioral case fails
-> H removed for that claim
-> report behavioral gate fails

same behavioral case has independent R evidence
-> R remains R
-> failed H remains failed

runtime artifact bound to older head
-> stale_runtime_evidence_refs
-> current R remains unproven

no production artifact
-> P remains unproven
```

This is intentional. Evidence dimensions describe different facts and may disagree.

## Privacy and minimization

The ledger stores evidence refs, digests, bounded outcomes, and exact source/head identity.

It does not require:

- raw poisoned memory contents;
- production payloads;
- credentials;
- hidden reasoning;
- complete MCP resource bodies;
- complete A2A Message/Artifact bodies;
- tenant/project display names when opaque refs suffice.

## Deployment profiles

### L: local / single-user

Behavioral evidence can execute entirely against the local reference implementation and protocol normalizers.

### T: team / multi-tenant

The A2A poisoning case exercises tenant/project mismatch explicitly. Cross-scope evidence cannot be repaired by task or peer identity.

### E: enterprise governed estate

Runtime and future production evidence may be attached separately without collapsing implementation proof into deployment certification.

### H: high assurance

Exact head identity, source refs, independent evidence levels, explicit stale evidence, and non-certification semantics are required. Missing evidence remains missing.

## V0.1 non-claims

V0.1 does not claim:

- comprehensive poisoning resistance;
- sleeper-agent resistance;
- long-horizon poisoning persistence measurement;
- live MCP server runtime validation;
- live A2A peer runtime validation;
- production security validation;
- OWASP, NIST, CSA, or other external certification;
- one poisoning result generalizes to unrelated threat families;
- `highest_demonstrated_level` is a maturity score.

## Follow-on direction

After this evidence-depth seam is stable, later P2 slices can add additional claims only when each has its own bounded evidence chain.

High-value candidates from #173 include:

- sleeper/delayed poisoning across retrieval and consolidation;
- correction poisoning and adversarial supersession;
- multi-source collusion/self-corroboration;
- poisoning persistence after summarization/consolidation;
- live protocol/runtime comparators;
- exact versioned standards mappings.

Each new claim must earn its own D/F/H/R/P evidence rather than inheriting depth from neighboring work.
