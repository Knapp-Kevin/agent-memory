# Governed Uncertainty Audit: Slice 5

## Scope

This slice adversarially evaluates the newer interdisciplinary theory documents:

- `20-memory-foundations-across-scales.md`
- `21-forgetting-consolidation-and-memory-metabolism.md`
- `22-agentic-memory-theory-and-development.md`
- `23-research-bibliography.md`
- `24-determinism-probability-and-governed-uncertainty.md`

Unlike earlier slices, these documents helped create the governed-uncertainty thesis. They are therefore audited for self-consistency rather than presumed compliant.

## Baseline

```text
baseline_main_commit: 4afd27a6aa3c728924bc88cf537acfe28b9058d1
baseline_source: merged PR #36 / governed uncertainty audit slice 4
```

## Baseline scores

`N/A` excludes criteria outside a document's material purpose.

| Document | GU-1 | GU-2 | GU-3 | GU-4 | GU-5 | GU-6 | GU-7 | GU-8 | GU-9 | GU-10 | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `20-memory-foundations-across-scales.md` | 3 | 3 | 4 | 3 | 2 | 3 | 3 | N/A | N/A | 3 | 80% |
| `21-forgetting-consolidation-and-memory-metabolism.md` | 3 | 3 | 4 | 3 | 4 | 4 | 4 | N/A | 3 | 4 | 89% |
| `22-agentic-memory-theory-and-development.md` | 3 | 3 | 4 | 3 | 4 | 4 | 3 | 2 | 3 | 4 | 83% |
| `23-research-bibliography.md` | N/A | 4 | 4 | 3 | N/A | N/A | N/A | N/A | 3 | 4 | 90% |
| `24-determinism-probability-and-governed-uncertainty.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 100% |

The baseline 100% for `24` means it covered the rubric it defined. It does **not** mean its language and assumptions were beyond improvement.

## Findings

### 20: strong cross-scale caution, limited governance detail

Strengths:

- explicitly rejects brain/database equivalence
- labels cross-domain transfer as functional rather than mechanistic
- separates content type, persistence, confidence, trust, relevance, sensitivity, authority, and certification
- treats forgetting and inherited memory carefully

Gaps:

- governed uncertainty is not its primary purpose
- newer threat/trust/privacy docs were not yet linked because they did not exist

Decision: no rewrite required in this slice. It remains a foundations document rather than a governance specification.

### 21: forgetting doctrine already resists utility absolutism

Strengths:

- distinguishes decay, suppression, pruning, archive, compression, semanticization, supersession, deletion, tombstone, and unlearning
- explicitly says utility is not authority
- preserves hard retention constraints and hard deletion constraints
- treats deletion as propagation into derived state

Gap:

- `forget_score` is a signal family and could still be misread by careless implementations as a delete score, but surrounding doctrine already rejects that interpretation

Decision: no rewrite required. Conformance and privacy docs now provide the stronger irreversible-deletion boundary.

### 22: material sequencing flaw

The original development sequence placed governance enforcement at Phase 7 after write admission, retrieval, correction, forgetting, and consolidation.

That is architecturally backwards for a governed-memory reference architecture.

Even if enforcement matures later, authority, scope, sensitivity, policy versioning, receipts, and proposal-versus-commit contracts must exist before implementations stabilize APIs around ungoverned behavior.

Remediation:

- rewrote the engineering doctrine around proposal -> governance -> selection -> commit
- moved governance contracts into Phase 1
- integrated governance into every subsequent phase
- made adaptive/learned control a later phase after boundaries exist
- expanded evaluation to adversarial governed memory

### 23: evidence discipline is good, challenge ledger still distributed

Strengths:

- distinguishes mechanism, analogy, engineering prescription, and open hypothesis
- includes primary biological/cognitive research and agent benchmarks
- explicitly says negative/conflicting evidence should alter doctrine

Gap:

- supporting and challenging research are not yet tracked in one canonical challenge ledger
- the newer 2026 security/privacy papers are distributed across docs 15, 16, 19, and 24 rather than all duplicated into the bibliography

Decision: do not duplicate research merely for bibliography volume. A later research-governance pass should decide whether a dedicated challenge ledger deserves its own document or structured data.

### 24: rubric-complete but language required adversarial refinement

The previous version was already strong, but several improvements were warranted:

1. replace **authority certainty** with **authority boundedness and reconstructability**
2. distinguish learned from probabilistic behavior
3. distinguish heuristic 0-to-1 scores from probabilities
4. make typed uncertainty explicit
5. integrate belief memory under partial observability
6. integrate current poisoning, provenance, privacy, and deletion-residue research
7. list failure modes of the doctrine itself
8. state exact evidence required before ADR-020 can become Accepted

The rewrite preserves the working thesis while reducing deterministic bias.

## Post-remediation scores

| Document | GU-1 | GU-2 | GU-3 | GU-4 | GU-5 | GU-6 | GU-7 | GU-8 | GU-9 | GU-10 | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `20-memory-foundations-across-scales.md` | 3 | 3 | 4 | 3 | 2 | 3 | 3 | N/A | N/A | 3 | 80% |
| `21-forgetting-consolidation-and-memory-metabolism.md` | 3 | 3 | 4 | 3 | 4 | 4 | 4 | N/A | 3 | 4 | 89% |
| `22-agentic-memory-theory-and-development.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 100% |
| `23-research-bibliography.md` | N/A | 4 | 4 | 3 | N/A | N/A | N/A | N/A | 3 | 4 | 90% |
| `24-determinism-probability-and-governed-uncertainty.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 100% |

Scores for 20, 21, and 23 remain unchanged deliberately. Their remaining gaps belong to their narrower purpose or to a future research-governance layer. The audit does not inflate scores merely because a document survived review.

## Doctrine corrections recorded

1. Governance contracts begin at architecture Phase 1, not after memory features are built.
2. Learned behavior is not synonymous with probabilistic behavior.
3. A normalized heuristic score is not automatically a probability.
4. The desired invariant is bounded and reconstructable authority, not certainty.
5. Uncertainty can itself be retained memory state.
6. Formal guarantees may be probabilistic when their guarantee type is explicit.
7. The doctrine must model its own failure modes.

## Verification requirements

- [x] all five theory documents reviewed
- [x] newer theory was not exempted from its own rubric
- [x] material development-sequence flaw corrected
- [x] central governed-uncertainty doctrine rewritten under adversarial review
- [x] docs 20/21/23 left unchanged where rewriting would add duplication rather than clarity
- [x] ADR-020 acceptance evidence is now explicit in doctrine
- [ ] final branch diff reviewed against `main`
- [ ] PR head verified mergeable
- [ ] commit status checked
- [ ] merged using exact verified head SHA

## Next slice

Audit the ADR set, especially ADR-020 and any ADRs governing identity, saturation, PAMA, certification, retention/deletion, observability, recovery, and quality metrics. ADR status must match the current evidence state rather than merely the age of the decision.
