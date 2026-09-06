# Human Correction UX Contract

## Purpose

Correction is a doctrine concept ([`02-lifecycle-state-machine.md`](02-lifecycle-state-machine.md), [`17-conflict-resolution-engine.md`](17-conflict-resolution-engine.md)). This document defines the minimum user-facing contract a product must honor when it exposes governed memory to humans.

The contract exists because a governed memory system that users cannot inspect, dispute, or correct is only governed on the inside. The user is a first-class correction authority — for memory about themselves, often the *highest* correction authority — and the interface is where that authority is either honored or quietly lost.

This is a contract, not a design. It constrains what any interface must make possible; it does not prescribe screens, flows, or visual language.

## What memory evidence must be visible

For any memory surfaced to a user, or used in a way the user can see the effects of, the interface must be able to answer, in user-comprehensible terms:

| Question | Backing doctrine |
|---|---|
| **Why does this memory exist?** — origin, source, when it was formed | provenance, `16-source-trust-and-reputation.md` |
| **Why was it recalled now?** — what admitted it into this context | recall explanations, [`26-governed-recall-planner.md`](26-governed-recall-planner.md) |
| **What supports it?** — the evidence, at least by kind and source | evidence records |
| **How settled is it?** — certified, candidate, disputed, corrected, historical | lifecycle state |
| **Who can see it?** — scope: which contexts, agents, or people | [`29-actor-scope-consent-and-tenancy.md`](29-actor-scope-consent-and-tenancy.md) |
| **What can I do about it?** — correct, dispute, restrict, or request deletion | this contract |

Visibility rules:

- Evidence display is itself scope- and sensitivity-filtered per [`19-privacy-and-sensitivity-classifier.md`](19-privacy-and-sensitivity-classifier.md) — explaining one memory must not leak another, or expose a third party's data as "supporting evidence."
- Absence of evidence is shown as absence. An interface must not decorate an uncorroborated inference to look as settled as a certified fact.
- Uncertainty survives presentation: an estimate presented to a user keeps being an estimate. Rounding "probably" up to a flat assertion in the UI is the presentation-layer version of confidence-becomes-truth.

## Correction flow requirements

- **Reachable**: correction is available wherever memory is visible or visibly acted on — not buried in a settings page the memory never links to.
- **Scoped**: the user corrects a specific memory unit or a specific field, not a vague "that's wrong" into the void. The interface resolves the target before submitting.
- **Authoritative but governed**: a user correcting memory about themselves (their preferences, their statements, their data) is a high-authority evidence source; the correction still flows through the correction path of `17-conflict-resolution-engine.md` — supersession, not overwrite, per [`18-temporal-causality-layer.md`](18-temporal-causality-layer.md).
- **Acknowledged with consequence**: the user learns what the correction did — accepted, applied from when, what it superseded — not merely "feedback received."
- **Never silently dropped**: a correction that cannot be applied (out of the user's authority scope, conflicts with policy) is declined *visibly*, with the reason and the escalation path.

## Dispute flow requirements

Dispute is for "this is contested" where correction is for "this is wrong, here is the fix":

- The user can dispute without supplying a replacement value.
- Dispute transitions the memory per the lifecycle: disputed memory is blocked from canonical use while contested — which means the *product behavior changes immediately*, not after eventual review.
- The dispute is visible on the memory everywhere it surfaces (see indicators below), including to other users within scope where multi-user memory is involved.
- Resolution — reconciled, corrected, upheld — is reported back to the disputant, with the reasoning at least summarized.
- Dispute cannot be weaponized invisibly: repeated bad-faith disputes are a governance matter with an audit trail, not a silent ranking signal.

## How corrections affect future recall

The contract's teeth are in what happens *after*:

```text
corrected memory  -> corrected value is what recall returns; superseded value
                     is historical, marked as such, never silently resurrected
disputed memory   -> excluded from canonical use in recall admission until resolved
restricted memory -> scope reduction applies to all future assembly immediately
deleted memory    -> deletion propagates to derived artifacts per doc 28;
                     recall does not reconstruct the deleted content from residue
```

- Derived memory is included: summaries, inferences, and consolidations built on a corrected memory are re-evaluated or flagged per the dependency rules of [`28-retention-deletion-and-tombstones.md`](28-retention-deletion-and-tombstones.md). Correcting the source while the stale summary keeps getting recalled is a contract violation, and exactly the deletion-residue failure the fixture set traps ([`../fixtures/deletion-residue.json`](../fixtures/deletion-residue.json)).
- A correction's effect is durable across sessions. Re-inferring the corrected-away value from the same old evidence, without new evidence, is a regression — the correction is itself high-authority evidence against that inference.
- Correction latency is measured (`correction_latency`, [`32-memory-quality-metrics.md`](32-memory-quality-metrics.md)): the gap between user correction and recall reflecting it.

## User-visible certification and dispute indicators

Minimum indicator vocabulary — products choose the presentation, the distinctions are non-negotiable:

| State | The user can tell |
|---|---|
| Certified | this has passed verification, and within what scope |
| Uncertified / candidate | the system holds this, but it has not been verified |
| Disputed | this is contested and is not being treated as settled |
| Corrected | this replaced something; history exists |
| Historical / superseded | true then, not current now |
| Restricted | visibility is narrowed; acting user may not see everything |

Rules: certified and uncertified memory are never visually indistinguishable; an open dispute is never hidden from users within scope; indicators derive from actual lifecycle state — an interface must not display "verified" as a styling choice on unverified memory.

## Accessibility and audit expectations

**Accessibility**

- Correction and dispute flows meet the product's accessibility baseline (assistive-technology operable, not colour-only indicators, plain-language descriptions of memory state).
- Explanations are comprehensible to the affected user, not only to the system's operators. "Blocked by policy p-14 §3" needs a human rendering.
- The flows are available to users of all technical levels; correction authority is not gated on expertise.

**Audit**

- Every user correction, dispute, restriction, and deletion request is a ledgered event per [`30-memory-observability-and-audit-events.md`](30-memory-observability-and-audit-events.md), with the user as recorded actor and the receipt reconstructable per [`31-recovery-rollback-and-replay.md`](31-recovery-rollback-and-replay.md).
- The user can see the status and history of their own corrections and disputes — an audit trail that excludes the person who triggered it is half an audit trail.
- Audit records of corrections are themselves sensitivity-handled: the record that a user corrected their medical preference is as sensitive as the preference.

## Conformance fixture recommendations

| Case | Expectation |
|---|---|
| User corrects own preference | applied via supersession; acknowledged; future recall returns corrected value — the example 4 pattern of [`33-pama-decision-table.md`](33-pama-decision-table.md) |
| User disputes without replacement | memory blocked from canonical use immediately; resolution reported |
| Correction with stale derived summary | derived artifacts re-evaluated; stale summary not recalled as current |
| Correction re-inferred away | corrected-away value does not return without new evidence |
| Out-of-authority correction attempt | declined visibly with reason and escalation path; ledgered |
| Indicator honesty | no interface state renders unverified memory as certified |

## Doctrine

The interface is an enforcement point.

Everything this architecture promises — governed mutation, honest uncertainty, blocked disputed memory, durable correction — is either upheld at the surface where a human meets their memory, or it is upheld nowhere the user can trust.
