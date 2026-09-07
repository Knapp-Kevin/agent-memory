# Hermes recursive-learning governance research

Issue: #317

Status: **source-bound architecture conclusion; no Hermes adapter implementation in this research slice**

Hermes evidence boundary:

```text
NousResearch/hermes-agent@165c889e5b4277b56dadd42949a4112c1e6175a6
license: MIT
```

Agent Memory starting boundary:

```text
0df4cf3337b3752105e1b5a110f38eee31f46fef
```

The machine-readable research record is [`hermes-mutation-surface.json`](hermes-mutation-surface.json).

## Conclusion

The original architecture hypothesis survives, with one important qualification:

> **Hermes should decide what it learned. Agent Memory should decide what that learning is allowed to become as governed durable state.**

Current Hermes already exposes enough generic machinery to support useful **observe** and **govern** integrations without replacing its recursive loop. However, a `pre_tool_call` plugin alone cannot honestly provide **strict** durable-state governance at the pinned revision.

The reason is not that Hermes' main learning loop is opaque. In fact, the current live tool executor is better than its older documentation suggests: normal foreground and background-review `memory` and `skill_manage` calls run through `resolve_pre_tool_block()` before execution.

The strict-mode gap exists because several legitimate durable mutations do not traverse the tool executor at all.

## What is interceptable today

### Foreground model-driven memory and skill writes

The live executor applies the generic pre-tool block before invoking the agent tool. This covers normal model-driven:

- built-in `memory` writes;
- `skill_manage` creation/edit/patch/delete/supporting-file writes;
- external provider tools that traverse normal tool execution.

This is enough for an Agent Memory governance plugin to evaluate the ordinary proposal before the underlying tool mutates durable state.

### Background recursive review

Hermes background review creates a forked `AIAgent`, shares the parent built-in `MemoryStore`, restricts mutation tools to `memory` and `skill_manage`, and runs through the normal conversation/tool executor.

Therefore the same generic pre-tool governor can intercept ordinary background-review memory and skill proposals.

This is an important positive result: governing recursive learning does **not** require replacing the background learning loop.

## What bypasses the tool-level governor

### Approved pending memory replay

Hermes write approval can stage a memory mutation. Later `/memory approve` or its gateway equivalent calls `apply_memory_pending()` directly against `MemoryStore`.

That replay:

- does not re-enter the normal tool executor;
- deliberately bypasses the write-approval gate;
- does not traverse `pre_tool_call`;
- does not traverse the normal agent-loop `notify_memory_tool_write()` bridge used to mirror successful built-in writes to external providers.

A human approval is evidence of authorization, but it is not proof that the candidate is still current or that execution used the state the human reviewed.

### Approved pending skill replay

`/skills approve` calls `apply_skill_pending()`, which directly invokes `skill_manage()` while a ContextVar explicitly bypasses the skill write-approval gate.

It likewise does not re-enter the outer model tool middleware.

### Deterministic curator archival

Hermes' curator has two materially different paths:

1. optional LLM consolidation through normal agent/tool execution, which is interceptable;
2. deterministic inactivity transitions, which can call `skill_usage.archive_skill()` directly.

The second path is a real procedural-memory lifecycle mutation outside the tool executor. Disabling the curator merely to claim strict governance would make Hermes less capable instead of making its existing capabilities governable.

### Journey edit/delete

Hermes' Journey UI/CLI mutation layer directly edits learned state:

- memory edits/deletes rewrite the memory file through `MemoryStore._write_file()`;
- skill edits call lower-level skill edit logic directly;
- skill deletes/archive call `skill_usage.archive_skill()`.

These operations are explicitly user-initiated, which is useful authority evidence, but they still need an execution/admission boundary if Agent Memory is to claim complete durable-state governance.

### Direct filesystem paths

Hermes' memory and skill implementations explicitly defend against external/drifted files, and the skill implementation notes that equivalent code paths can be reached outside `skill_manage` (for example through terminal/file operations).

A plugin can inspect a `terminal` tool call, but shell-command parsing is not a trustworthy semantic durable-state boundary. The persistence primitive, not the command string, is the right place to make a strict claim.

## Why the external MemoryProvider is additive, not authoritative

Hermes allows one external memory provider in addition to built-in memory.

The provider lifecycle is useful for an Agent Memory integration:

- initialization and scoped provider state;
- system-prompt context;
- prefetch/recall;
- turn synchronization;
- session-end extraction;
- provider tools;
- built-in-memory write mirroring;
- backup paths and session lifecycle hooks.

But the built-in write bridge is post-commit. `MemoryManager.notify_memory_tool_write()` only notifies providers after a successful, non-staged built-in memory write. Provider exceptions are logged rather than rolling back the built-in commit.

The provider therefore cannot be the admission authority for built-in memory.

It is also not a complete observer of recursive learning:

- background review is created with `skip_memory=True` for external-provider setup even though it shares the parent's built-in memory store;
- approved pending replay bypasses the normal memory-write bridge;
- curator/Journey/direct filesystem mutations are outside the provider bridge.

So a provider-only integration is useful but incomplete by construction.

## Integration postures

### Observe

Useful today, but explicitly partial unless supplemented by broader durable-state observation.

Recommended shape:

```text
Hermes built-in memory / skills / learning loop
        |
        +--> Agent Memory external MemoryProvider
        |      recall / prefetch / sync / provider tools
        |
        +--> Agent Memory general plugin
               provenance / tool proposal observations
```

This is appropriate for research, provenance collection, and comparative runtime evidence. It must not claim every durable mutation was observed.

### Govern

Useful today for normal model-driven recursive learning.

```text
Hermes foreground/background model proposal
        |
        v
pre_tool_call
        |
        v
Agent Memory admission
   allow | block
        |
        v
Hermes memory / skill tool
```

The deployment must disclose that pending replay, deterministic curator lifecycle, Journey mutations, and direct durable file writes are outside this gate unless separately wrapped or disabled.

Agent Memory governor failure cannot be implemented by throwing an exception and hoping Hermes stops. A required-governor deployment must turn unavailable/invalid admission into an explicit block decision.

### Strict

**Not honestly available at the pinned Hermes revision using plugins/providers alone while preserving all existing durable mutation surfaces.**

Strict mode becomes defensible when every consequential durable mutation routes through one common persistence-adjacent admission boundary.

## Recommended Hermes interoperability primitive

The smallest clean upstream change is not an Agent Memory-specific integration. It is a generic **durable-state mutation middleware** shared by every canonical memory/skill mutation path.

Conceptually:

```text
candidate durable mutation
        |
        v
before_durable_state_mutation(event)
        |
        +--> allow
        +--> stage
        +--> reject
        |
        v
canonical persistence operation
        |
        v
after_durable_state_mutation(receipt)
```

The before event should bind at least:

- stable mutation id;
- subsystem (`memory`, `user_profile`, `skill`, `skill_lifecycle`);
- operation;
- origin (`foreground_model`, `background_review`, `curator`, `human_approval_replay`, `journey`, etc.);
- execution context;
- target identity;
- before-state digest or explicit absence;
- candidate-state digest or explicit absence;
- scope;
- provenance/evidence references;
- human/external approval references where present.

A required governor must be able to fail closed when unavailable or when it does not return a valid decision.

The after receipt should distinguish **admission/approval** from **actual execution** and bind:

- mutation id;
- committed/failed outcome;
- committed digest or absence;
- execution error if any;
- durable receipt/evidence references.

The middleware should cover, at minimum:

- normal built-in memory writes;
- normal `skill_manage` writes;
- approved pending memory replay;
- approved pending skill replay;
- deterministic curator archive/restore transitions;
- Journey memory/skill edits and deletes;
- equivalent agent-originated canonical durable writes.

This is a Hermes interoperability primitive, not Agent Memory ontology. Agent Memory would simply be one consumer.

## Human approval composition

Hermes' existing write-approval UX should remain useful.

Agent Memory does not need to replace `/memory pending`, `/skills pending`, approve/reject UX, or the user's authority to approve a candidate. The required distinction is:

```text
human approved candidate M
!= M is still current
!= M was executed against the reviewed before-state
!= M completed successfully
```

A durable mutation middleware lets approval remain a human authority reference while Agent Memory revalidates currentness/scope/candidate identity immediately before persistence and records the execution receipt afterward.

## Recursive evidence pressure

Hermes is especially valuable as an adversarial runtime because its own learned outputs can feed future learning.

Agent Memory must preserve derivation lineage across sequences such as:

```text
experience A
-> skill B
-> B produces observation C
-> C contributes to generalized skill D
```

B, C, and D are causally related. They cannot be counted as three independent corroborating sources merely because Hermes created three durable artifacts.

Likewise, a corrected value must not silently regain current status because background review encounters the old value again, and an old staged mutation must not remain executable after its before-state changes.

The machine-readable record includes five bounded adversarial scenarios covering self-reinforcement, correction readmission, stale approval replay, curator retirement, and provider-mirror lag.

## Source-neutral capability mapping

Hermes exercises several existing Agent Memory capabilities without requiring new doctrine:

- semantic durable memory;
- user/profile memory;
- procedural memory;
- recursive/background learning origin;
- lifecycle/archive maintenance;
- external memory-provider integration;
- async currentness and quiescence;
- human/external authority composition.

The existing Agent Memory rules remain sufficient:

- origin is provenance, not evidentiary privilege;
- repetition is not corroboration;
- procedural memory is not execution authority;
- correction/supersession and rejected-value protections remain controlling;
- provider/learned outputs do not launder authority;
- approval and execution evidence are distinct;
- committed, current, settled, and quiescent are distinct lifecycle states.

For that reason this research creates **no new ADR**.

## Recommendation

The implementation sequence should be one bounded follow-on, not a fleet of Hermes-specific tickets:

1. build a standalone Agent Memory Hermes integration package using the supported external-provider and plugin surfaces;
2. support `observe` and explicitly bounded `govern` modes first;
3. include exact Hermes version/profile applicability and a `doctor` check that reports uncovered mutation paths rather than advertising false strictness;
4. upstream or collaborate on a generic durable-state mutation middleware in Hermes;
5. expose `strict` only when runtime evidence proves every declared consequential mutation path crosses that boundary;
6. use Hermes as a reference adversarial runtime for recursive-learning lineage, stale approval, background mutation, and currentness/quiescence tests.

No Hermes-specific ontology belongs in Agent Memory core.

## Stopping rule

The source audit stops here because every consequential mutation family identified by #317 now has an explicit classification, and additional examples would reproduce an already-owned obligation rather than reveal a new failure class.

The research result is therefore:

```text
provider only                 -> insufficient
provider + pre-tool plugin    -> useful observe/govern, not strict
strict without disabling UX   -> needs generic durable-state mutation middleware
new Agent Memory doctrine     -> not needed
Hermes recursive loop replace -> not needed
```
