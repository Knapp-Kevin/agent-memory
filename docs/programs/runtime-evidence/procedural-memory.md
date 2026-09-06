# Governed Procedural Memory Evidence

Status: **reference runtime evidence for ADR-034 and #295**

This evidence slice proves that Agent Memory can retain and reuse a procedure across sessions without converting the remembered procedure into standing execution authority.

## Claim boundary

The proved reference flow is:

```text
component capability resolution
        |
        v
procedural-memory proposal
        |
        v
PAMA / current-state / scope evaluation
        |
        v
governed durable skill commit
        |
        v
later-session retrieval candidate
        |
        v
governed recall admission / activation
        |
        v
plan influence
        |
        v
separate runtime action proposal
        |
        v
separate action-governance decision
        |
        v
separate execution evidence
```

The evidence does **not** claim:

- process-restart durability;
- a universal skill serialization or skill database;
- real external tool execution by the reference harness;
- universal production conformance;
- reference qualification for EvolveAI or CodeGenome;
- that component routing, skill retrieval, prior validation, or prior approval grants action authority.

The procedural reference path uses the existing `GovernedMemoryAdapter` and its PAMA/currentness/isolation/tombstone/receipt behavior. It does not implement a parallel authority system.

## Executable surfaces

- `reference/agentmem_ref/contracts/capabilities.py`
- `schemas/component-capability-profile.schema.json`
- `reference/fixtures/component-capabilities/evolveai.example.json`
- `reference/fixtures/component-capabilities/codegenome.example.json`
- `reference/fixtures/component-capabilities/procedural-reference.json`
- `reference/agentmem_ref/memory/procedural_memory.py`
- `reference/tests/test_component_capabilities.py`
- `reference/tests/test_procedural_memory.py`
- `reference/run_procedural_memory.py`
- `.github/workflows/procedural-memory-evidence.yml`

## Capability-resolution evidence

ADR-033's enabling contract is exercised before the procedural-memory workload.

The reference registry proves:

| Case | Expected result |
|---|---|
| declared capability below required maturity | explicit failure |
| one eligible provider | deterministic resolution |
| several eligible providers without a rule | ambiguity failure |
| explicit preferred eligible provider | deterministic selection |
| preferred provider below required maturity | failure, no silent fallback |
| newer component version with weak capability maturity | still ineligible |
| one component exposing several capabilities | independently resolvable capability maturity |
| several components composing different capabilities | deterministic composition |
| resolved capability | `authority_effect` remains `none` or `proposal_only`, never inferred permission |

The EvolveAI and CodeGenome fixtures deliberately mirror the bounded maturity established by the first-party inventory. They are examples for the declaration contract, not conformance promotions.

## Procedural-memory acceptance matrix

### Proposal without mutation

A `SkillArtifact` is converted into a PAMA proposal without writing the substrate or advancing governed state.

The proposal binds:

- logical skill reference;
- target class `M3_REUSABLE_PROCEDURE_OR_CAPABILITY`;
- state snapshot;
- scope and isolation domains;
- purpose;
- exact `content_sha256` through the proposal evidence set.

### Governed promotion

The initial low-risk promotion traverses the ordinary `GovernedMemoryAdapter.commit_proposal()` path and current PAMA policy. The stored procedure round-trips through its integrity-bound serialization.

Capability resolution happens before the operation, but the selected component has no authority to make the promotion durable.

### Cross-session plan influence

A later reference session begins without conversational memory, performs governed recall, admits the current scoped skill, and produces a different release plan than the no-memory control.

The simple control is deliberate:

```text
no admitted procedural memory
  -> inspect current state only

governed admitted skill
  -> inspect current state
  -> apply the admitted procedure
  -> produce candidate runtime actions
```

The value claim is lifecycle/governance continuity, not that Agent Memory invented Markdown or bullet lists.

### Execution-authority separation

An admitted skill may produce `ActionProposal` objects. Each starts with:

```text
requires_governance = true
governance_decision_ref = empty
execution_status = not_executed
```

The reference harness refuses to record execution until an independently supplied governance decision binds the exact action ID. Execution then receives a separate execution reference.

This proves identity and authority separation. It does not claim a production external-governance integration or real external side effect.

### Correction and exact approval binding

Version 2 of the fixture release skill changes the target branch from `release` to `main`.

Under the current PAMA profile:

1. the correction proposal is `require_review` and does not commit;
2. `approve_skill_proposal()` binds one approval to the exact proposal ID, skill version, content SHA-256, and current state snapshot;
3. only the exactly bound v2 payload may commit;
4. v1 remains reconstructable as historical/superseded state;
5. later recall admits v2 and refuses v1 as `superseded_not_current`.

The adversarial substitution test approves the exact v2 payload targeting `main`, then substitutes a different v2 payload targeting `develop`. Commit fails with:

```text
skill_proposal_content_mismatch
```

A manually forged `review_satisfied=true` plus an approval reference without the exact `SkillApproval` binding also fails.

### Stale replay

After v2 advances the state, replaying the v1 proposal cannot mutate and is refused as:

```text
stale_authorization
```

Prior approval or proposal history therefore does not become standing authority after current state changes.

### Cross-scope refusal

A second project can receive a highly relevant candidate from the permissive substrate. Governed recall still refuses admission because the required isolation/project domain is absent.

```text
candidate presence != admitted influence
```

### Revocation and residue honesty

The reference revocation path uses governed `pruning` and tombstones the current skill.

The reference substrate deliberately retains physical content for recovery, so the evidence reports:

- active influence removed;
- physical content retained;
- undeclared residue list;
- later activation count zero.

The proof therefore distinguishes semantic non-influence from physical erasure rather than claiming complete forgetting from a tombstone.

### Metamemory refusal

A retained metamemory artifact asks to lower capability maturity requirements and change provider precedence.

Ordinary procedural activation refuses it as:

```text
metamemory_requires_configuration_governance
```

The same requested consequence can be projected into a separate PAMA proposal with:

```text
operation = policy_mutation
target_class = M5_GOVERNANCE_SECURITY_OR_AUTONOMOUS_AUTHORITY
downstream_authority = A5_GOVERNANCE_CHANGE
```

Current PAMA returns `require_external_verification`. The learned/retained instruction cannot apply itself.

## Distinct evidence identities

The deterministic harness keeps these separately visible:

```text
skill logical/version reference
skill content digest
memory proposal ID
PAMA decision
exact approval reference when required
memory receipt
retrieval/admission evidence
action proposal ID
action-governance decision reference
execution reference
```

No single `approved skill` identity is accepted as evidence for all stages.

## Deterministic evidence harness

Run:

```bash
python -m pip install -r reference/requirements.txt
python -m unittest discover -s reference/tests -p 'test_component_capabilities.py' -t reference
python -m unittest discover -s reference/tests -p 'test_procedural_memory.py' -t reference
python reference/run_procedural_memory.py --output artifacts/procedural-memory-evidence.json
```

The dedicated `Procedural Memory Evidence` GitHub Actions workflow runs those focused gates and uploads the JSON report. Its path filters include the implementation, ADR, runtime-evidence, reference-documentation, and Wiki status surfaces so a doctrine/status change must re-prove the same executable boundary at the new PR head.

Repository-wide `Validate Doctrine Evidence` is also required before merge. It independently executes the complete reference test suite, source/schema/doctrine validation, deletion evidence, comparator paths, real-substrate governed paths, conformance report, documentation links, and Wiki links.

## Falsification conditions exercised

The reference slice is considered failed if any of these become true:

- proposal writes before governance;
- component selection creates memory authority;
- a retrieved but inadmissible skill changes the plan;
- skill retention/activation grants execution permission;
- approval for X can commit Y;
- a generic review flag can manufacture exact approval;
- stale or superseded skill state becomes current through retrieval ranking;
- stale proposal/approval can mutate after state advancement;
- a foreign-scope skill is admitted without governed crossing;
- revocation leaves a derived/current influence while claiming removal;
- metamemory changes the active profile through ordinary skill activation;
- decision, admission, action governance, and execution evidence collapse into one identity.

## Result

The #295 reference slice satisfies ADR-034's doctrine-promotion evidence boundary while remaining intentionally narrow. It demonstrates reusable procedural continuity with governed authority separation. It does not establish restart-safe production Agent Memory or choose a universal procedural-memory substrate.
