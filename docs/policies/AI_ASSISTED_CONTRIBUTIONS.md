# MythologIQ Labs AI-Assisted Contribution Standard

**Status:** Agent Memory repository policy

## Purpose

MythologIQ Labs builds with coding agents and other AI-assisted development tools. Their use is permitted and encouraged when it improves implementation speed, validation coverage, accessibility, review quality, or evidence quality.

The governing question is not who typed the code. It is who is accountable for the contribution and under what authority repository actions occur.

> **AI-assisted development is allowed. Unbounded autonomous contribution is not accepted by default.**

A responsible human must own the objective, material risk, repository authority, and resulting contribution. A repository may also explicitly authorize a bounded agent workflow when the scope, allowed actions, evidence requirements, and revocation boundary are clear.

This policy is technology-neutral. It applies whether work is produced with a coding agent, IDE assistant, code generator, automated reviewer, or conventional hand-authored development.

## Definitions

### AI-assisted contribution

A contribution is **AI-assisted** when a human contributor uses one or more AI tools to research, design, implement, test, refactor, document, review, or prepare a change while the human remains accountable for the result.

The responsible human does not need to have typed every line.

### Human-directed agent execution

A workflow is **human-directed agent execution** when a responsible human explicitly delegates a bounded task or repository action to an agent and remains accountable for the delegation.

Examples include asking an authenticated coding agent or connector to:

- implement an issue with stated acceptance criteria;
- create a branch or pull request for reviewed work;
- run or inspect validation;
- update an issue with verified results;
- merge an exact validated head when the human has authorized that workflow.

Human-directed agent execution is not treated as unbounded autonomous contribution merely because the agent performs the repository API call.

### Autonomous contribution

A contribution is **autonomous** when an agent acts as the effective contributor without a responsible human, without bounded delegated authority, or beyond the scope that a human or repository policy authorized.

Examples include independently filing speculative issues, opening unsolicited pull requests, claiming work, approving changes, or merging outside a documented or directly delegated authority boundary.

### Responsible human

The **responsible human** owns the repository-facing consequence. That person must be able to explain the objective, material behavior, validation evidence, known limitations, and why the delegated authority was appropriate.

## Allowed uses of AI development tools

AI tools may be used for:

- implementation and refactoring;
- tests, fixtures, and adversarial vectors;
- documentation and diagrams;
- debugging and root-cause analysis;
- code and security review;
- standards and interoperability mapping;
- migration planning;
- dependency analysis;
- benchmark and validation harnesses;
- drafting commit messages, issues, pull-request descriptions, and review responses;
- repository actions explicitly delegated by a responsible human or authorized by repository policy.

Routine AI assistance does not require a disclosure label unless a repository-specific or upstream rule requires one.

## Human accountability requirements

For a substantive contribution, the responsible human must ensure that:

1. **The objective is understood.** Scope, intended consequence, and acceptance boundary are clear.
2. **Material behavior is reviewable.** The actual change and relevant evidence are available for inspection. Agent summaries are aids, not a substitute for repository evidence.
3. **Material choices are defensible.** The responsible human can explain the important design decisions, tradeoffs, and known failure modes.
4. **Evidence is verified.** Tests, validators, benchmarks, or independent checks appropriate to the risk have been run or inspected.
5. **Provenance and rights are resolved.** Generated or reused code, documentation, diagrams, and other material must satisfy repository source-rights rules.
6. **Repository authority is explicit.** An agent action must be directly delegated, permitted by a standing repository authorization, or performed by ordinary human submission.
7. **The contribution is owned.** Bugs, security defects, misleading claims, provenance failures, and policy violations remain attributable to the responsible human and repository governance process.

For security-sensitive or doctrine-changing work, direct inspection of the relevant diff and evidence is expected before final acceptance. Lower-risk mechanical work may use a lighter review path when repository policy permits it.

## Repository-boundary rule

Repository actions require authority, not ritual.

A pull request, issue, review response, approval, or merge may occur through either of these paths:

```text
ordinary human submission

or

bounded human delegation / standing repository authorization
  -> explicit scope
  -> permitted repository actions
  -> required validation
  -> reviewable evidence
  -> revocable authority
```

For Agent Memory, the maintainer may directly delegate repository actions to authenticated AI tools or connectors during an active working session. Such delegation is bounded by the stated task, issue or branch scope, repository governance, and any explicit merge gate such as exact-head CI validation.

A general instruction to work on Agent Memory does not authorize unrelated upstream submissions, external-project comments, destructive repository administration, or expansion into a different issue or organization.

Unattended or recurring agents require a standing repository authorization that identifies their allowed actions and oversight model.

## Prohibited autonomous behavior by default

Unless explicitly authorized, agents and bots must not:

- open unsolicited pull requests or issues;
- claim issues without a responsible human or standing authorization;
- post unsolicited substantive review feedback to external contributors;
- impersonate a human in maintainer discussions;
- approve pull requests;
- merge outside a delegated or standing merge authority;
- manufacture stars, forks, issues, comments, or other synthetic community activity;
- use AI generation to obscure unattributed derivative work or licensing conflicts;
- treat access to one repository as authority to act in another.

## DCO and contribution provenance

Agent Memory may use the Developer Certificate of Origin as a provenance mechanism for external code or specification contributions if the repository explicitly activates it.

**DCO is not automatically active merely because this policy mentions it.** The repository must explicitly activate the requirement and should add automated enforcement at the same time so contributors are not governed by an invisible manual gate.

Agent Memory does not claim DCO enforcement until that activation is merged and discoverable. Any organization-wide DCO policy is governed outside this repository.

When DCO is active, an agent must never invent or apply a human `Signed-off-by` certification without that person's authorization.

## Security-sensitive changes

AI assistance does not lower the review bar for security-sensitive work.

Changes involving cryptography, authentication, authorization, policy enforcement, sandboxing, supply-chain controls, secrets handling, isolation boundaries, signing, provenance, or destructive lifecycle actions require heightened review.

At minimum:

- avoid self-referential validation where an implementation and its only test oracle share the same assumptions;
- prefer independent vectors, reference implementations, or known-answer tests where available;
- review dependencies and algorithms for invented packages, obsolete primitives, and insecure defaults;
- do not place secrets, credentials, or restricted data into external tools without an approved handling basis;
- state what the validation proves and what remains unproven.

## Prior art, copyright, and licensing

AI assistance does not erase provenance obligations.

Contributors must:

- identify and credit material prior art when work is substantially derived from an external source;
- comply with the repository source-rights and attribution rules;
- avoid copying or laundering incompatible third-party work through model output;
- preserve required notices, licenses, and modification notices;
- disclose uncertainty when origin or reuse rights cannot be established.

When in doubt, prefer independent synthesis and explicit attribution.

## Disclosure

Routine AI assistance does not require disclosure merely because an AI tool participated.

Disclosure is appropriate when:

1. a repository or upstream project explicitly requires it;
2. a standing autonomous agent authorization is material to understanding who exercised repository authority; or
3. material generated content has not received the review required by the applicable repository policy, in which case the contribution is normally not merge-ready.

Disclosure is not a substitute for accountability.

## Authorizing repository agents and bots

A standing authorization should document:

- the bot or agent identity or class of authenticated tool;
- the actions it may perform;
- repository, branch, file, label, issue, or workflow scope where material;
- required validation and review gates;
- the human or governance role accountable for the authorization;
- how the authorization can be revoked.

Authorization is narrow. Permission to run CI does not imply permission to open PRs, review code, answer maintainers, merge changes, or act in external repositories.

## Relationship to local and upstream rules

This document is an Agent Memory repository policy. It does not claim organization-wide inheritance or rollout authority.

A repository may impose stricter requirements for security, regulatory, contractual, release, or standards reasons. Local rules may narrow automation privileges but should not silently weaken the human-accountability baseline.

When contributing to an external project, that project's rules control the upstream submission. MythologIQ Labs policy never grants permission to bypass a stricter external contribution boundary.

## Practical workflow

A compliant agent-first workflow can be:

```text
human defines objective, scope, and acceptance boundary
        |
        v
agent researches / implements / tests / reviews
        |
        v
repository evidence and material diff remain inspectable
        |
        v
human reviews directly or exercises an explicit bounded delegation path
        |
        v
provenance, risk, and repository-specific gates are satisfied
        |
        v
human or authorized agent performs the repository action
        |
        v
exact required checks / approvals gate merge
        |
        v
responsible human remains accountable for the consequence
```

The purpose of this standard is not to recreate manual coding or manual button-clicking as ceremony. It is to preserve accountable authority, reviewability, provenance, and maintainer trust while using modern coding agents as first-class development tools.
