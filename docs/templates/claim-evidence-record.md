# Claim / Evidence Record Template

Use this template when a claim may materially affect Agent Memory doctrine, contracts, conformance, security, privacy, lifecycle behavior, authority, interoperability, or production guidance.

The template is source-neutral. Native doctrine, maintainer statements, contributor proposals, AI-generated analysis, external research, implementation observations, benchmark results, and production evidence all enter through the same epistemic discipline.

> **Origin establishes provenance, not evidentiary privilege.**

Copy the record below into the relevant research program, issue, ADR evidence section, audit, or experiment record. Delete instructional comments, but preserve the distinctions.

```yaml
claim_id: "stable-local-id"
claim: "falsifiable statement being evaluated"

origin:
  type: "native_doctrine | maintainer | contributor | ai_analysis | practitioner | paper | standard | implementation | benchmark | production | other"
  reference: "URL, repository path, issue/ADR, commit, artifact, or other stable locator"
  producer: "person, project, organization, system, or unknown"

claim_type: "architecture | security | lifecycle | authority | interoperability | implementation | benchmark | empirical | other"

evidence:
  class: "hypothesis | architectural_deduction | implementation_observation | external_empirical_evidence | conformance_evidence | runtime_evidence | benchmark_evidence | production_evidence"
  supporting:
    - ref: "stable evidence reference"
      boundary: "what this evidence actually establishes"
  challenging:
    - ref: "stable evidence reference"
      boundary: "what this evidence challenges or narrows"

reproduction:
  status: "unverified | reproduced | contradicted | bounded | inconclusive | not_applicable"
  environment_or_version: "pinned implementation/runtime/dataset when applicable"
  result_ref: "fixture, test, report, commit, or experiment record"

scope_and_boundaries:
  applies_when:
    - "material condition"
  does_not_establish:
    - "explicit non-claim"
  known_counterexamples:
    - "counterexample or none known"

promotion:
  state: "discovery | under_test | supported | clarified | narrowed | rejected | candidate_change | promoted"
  consequence: "none | documentation | fixture | contract | ADR_candidate | accepted_doctrine | implementation_guidance"
  decision_ref: "issue, PR, ADR, audit, or other decision record"

reviewed_at: "YYYY-MM-DD"
```

## Interpretation rules

- `origin` answers who or what produced the claim. It does not establish truth or authority.
- `evidence.class` describes the kind of evidence, not a universal scalar strength.
- `reproduction.status: reproduced` proves only the pinned scenario actually reproduced.
- `promotion.state: promoted` requires a separate consequence-appropriate governance decision. Repetition, popularity, publication, deployment, or CI success cannot self-promote a claim.
- Challenging evidence and negative results remain part of the record even when the final decision is `supported` or `promoted`.
- A later stronger contradiction may reopen, narrow, supersede, or reject an earlier conclusion, including Accepted doctrine.

## Rights boundary

This template records epistemic status. It does not grant reuse rights. External quotations, code, figures, diagrams, tables, screenshots, or other expressive material remain subject to [`../SOURCE_RIGHTS_POLICY.md`](../SOURCE_RIGHTS_POLICY.md) and the source registry where applicable.
