# Issue #68 Isolation Evidence Gap Reconciliation

## Purpose

Reconcile the broader isolation-domain backlog in issue #68 against the repository state after ADR-022 acceptance, the runtime-evidence program, and P7 governed interchange work.

This audit does not reopen ADR-022 or treat Accepted doctrine as universal conformance. Its job is narrower: identify which #68 follow-up claims are already executable, which are only partially evidenced, and which still require implementation.

## Research pressure

Two external access-control principles reinforce the existing Agent Memory boundary without changing doctrine:

- NIST SP 800-207 treats resource access as a policy decision that must not inherit implicit trust from network or physical location. Agent Memory applies the same architectural separation to logical memory domains: a shared substrate or same runtime identity is not authority to cross a memory boundary.
- NIST SP 800-162 defines authorization as evaluation of subject, object, requested operation, and relevant environmental attributes against policy. Agent Memory's target domain, principal, project/task, purpose, representation, sensitivity, destination, and requested crossing consequence are compatible with that model while remaining memory-specific.

These sources support continued separation of storage topology from authorization and support request-specific evaluation. They do not define Agent Memory doctrine and are not imported as normative schemas.

References:

- NIST SP 800-207, *Zero Trust Architecture*, https://doi.org/10.6028/NIST.SP.800-207
- NIST SP 800-162, *Guide to Attribute Based Access Control (ABAC) Definition and Considerations*, https://doi.org/10.6028/NIST.SP.800-162

## Current accepted foundation

The following #68 acceptance prerequisites are already present on `main`:

- canonical isolation-domain contract in `docs/41-memory-isolation-domains-and-governed-crossing.md`;
- explicit non-duplicative relationship to ADR-016;
- additive isolation-domain state in the memory scope representation;
- target-domain, project, and task context for governed recall;
- boundary-crossing receipt schema and executable crossing evaluator;
- derived-scope intersection/union behavior and governed scope-promotion path;
- shared-domain membership enforcement;
- shared-memory protocol reconciliation;
- Accepted ADR-022 with its own evidence record.

The remaining question is the broader #68 negative-path and fixture wishlist.

## Named fixture / behavior reconciliation

| #68 named behavior | Existing evidence | Verdict |
|---|---|---|
| `same-agent-cross-project-relevance-trap` | `reference/tests/test_isolation_domains.py::test_same_agent_same_tenant_wrong_project_is_blocked` keeps agent, tenant, store, and semantic match constant while changing the logical target domain/project | executable behavior satisfied; exact named fixture file absent |
| `same-agent-cross-task-relevance-trap` | `test_same_agent_same_project_wrong_task_is_blocked` | executable behavior satisfied; exact named fixture file absent |
| `shared-store-wrong-domain` | isolation-domain tests use one physical store; shared-domain tests also prove membership does not override a wrong target domain | executable behavior satisfied |
| `shared-space-non-member-recall` | `reference/tests/test_shared_domain_membership.py::test_non_member_is_candidate_but_blocked` plus unresolved-membership fail-closed path | executable behavior satisfied |
| `scope-promotion-without-authority` | `fixtures/unauthorized-scope-promotion.json` plus `test_scope_governance.py` review-required and self-approval-block paths | satisfied |
| `derived-summary-scope-widening` | `test_summary_does_not_erase_source_restrictions` and disguised-broadening block path | executable behavior satisfied |
| `multi-source-derived-scope-intersection` | `test_multi_source_derivation_intersects_authority_and_unions_restrictions`; incompatible source scopes fail closed | satisfied |
| `cross-domain-composition-risk` | canonical doctrine states individual admission does not prove combined-context safety; no dedicated executable composition gate was found | **missing** |
| `task-switch-context-bleed` | `test_task_switch_does_not_carry_prior_context_authority` | executable behavior satisfied |
| `authorized-redacted-export` | boundary-crossing tests prove privacy minimization does not self-authorize export and separately prove reviewed crossing can commit; no test combines approved redacted representation with authorized external export | **partial** |
| `scope-reduction-propagates-to-derived-state` | P4 proves correction/deletion propagation and derived-state freshness; derived-scope code proves inheritance/broadening rules. No dedicated isolation-scope reduction propagation path was found | **missing** |
| `shared-memory-revocation-propagation` | shared-domain membership revocation immediately blocks later recall without rewriting memory; P7 proves source lifecycle notices can drive receiver-local consequences. No dedicated shared-space revocation propagation into already-derived/shared downstream state was found | **partial** |

## Additional issue-body follow-ups

### Same-tenant prohibited compartment

The repository can express separate logical domain refs inside one tenant, and same-agent cross-project/task tests prove that a same-tenant candidate is not automatically admitted. There is not yet a distinct compartment policy primitive beyond domain identity and membership. A new primitive should not be invented merely to satisfy wording in the issue. The next evidence should first test whether multiple required domain/compartment attributes need conjunctive enforcement rather than the current "any matching domain" admission rule.

### Export / destination restrictions

Boundary crossings require explicit destination domains and a scope-expansion PAMA decision. The privacy-minimized negative case correctly shows redaction is not authority. The missing positive case is an explicitly reviewed, redacted export whose receipt preserves the representation and destination evidence.

## Gap priority

The remaining gaps are ordered by governance value, not by ease of producing more files:

1. **Cross-domain composition gate.** Current candidate-level admission can be correct while the assembled set is prohibited as a combination. This is the clearest unimplemented doctrine boundary.
2. **Scope-reduction propagation into derived state.** Scope inheritance exists at creation time; the repository still needs direct evidence that a later narrowing cannot leave a broader derived representation active.
3. **Shared-memory revocation propagation.** Current membership revocation protects future recall, but downstream copies/derivations need explicit obligation behavior where policy requires it.
4. **Authorized redacted export positive path.** This is small but important evidence that privacy minimization can participate in an authorized crossing without becoming the authorizer.
5. **Conjunctive compartment semantics research.** Before changing recall semantics, determine whether a memory bound to multiple isolation domains means "any authorized route" or "all required compartments". The current tuple is deliberately non-hierarchical, so this distinction must be explicit before implementation.

## Development rule

Each subsequent #68 slice must:

1. identify the exact doctrine claim it exercises;
2. distinguish architectural deduction from external research support and executable repository evidence;
3. add negative paths before claiming a boundary is enforced;
4. avoid adding a new schema or policy primitive when the existing representation can express the requirement;
5. preserve `relevance != permission`, `same agent != same memory scope`, and `valid crossing receipt != later lifecycle satisfaction`;
6. pass exact-head `Validate Doctrine Evidence` and CodeQL before merge.

## Closure posture

Issue #68 is **not yet eligible for closure**.

Most of the original acceptance gate has been satisfied and ADR-022 is Accepted, but the broader issue explicitly retained follow-up evidence work. The remaining load-bearing gaps are composition safety, scope-reduction propagation, downstream revocation behavior, and a positive authorized-redacted-export path. Once those are executed and the issue body is reconciled to current truth, #68 can receive a separate closure audit rather than being closed by implication.
