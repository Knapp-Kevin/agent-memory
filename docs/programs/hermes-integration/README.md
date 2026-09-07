# Hermes observe/govern integration

Issue: #330

Status: **standalone integration implementation for the exact #317 Hermes profile**

Hermes applicability pin:

```text
NousResearch/hermes-agent@165c889e5b4277b56dadd42949a4112c1e6175a6
license: MIT
```

Package:

```text
integrations/hermes-agent-memory/
package: agent-memory-hermes
integration profile: agent-memory-hermes/1.0.0
```

The package publishes both supported Hermes extension points:

```toml
[project.entry-points."hermes_agent.plugins"]
agent-memory = "agent_memory_hermes.safe_plugin:register"

[project.entry-points."hermes_agent.memory_providers"]
agent-memory = "agent_memory_hermes.provider:register_memory"
```

It does not replace Hermes' built-in memory, skill executor, recursive background review, curator, or human approval UX.

## Installation and shared configuration

Install the package into the same Python environment used by Hermes:

```text
pip install ./integrations/hermes-agent-memory
```

The general plugin and external MemoryProvider share profile-scoped configuration at:

```text
$HERMES_HOME/agent-memory/config.json
```

Default configuration is equivalent to:

```json
{
  "mode": "observe",
  "governor_command": [],
  "governor_required": true,
  "governor_timeout_seconds": 10.0,
  "record_payloads": false,
  "require_exact_profile": true,
  "expected_hermes_revision": "165c889e5b4277b56dadd42949a4112c1e6175a6"
}
```

Hermes' memory-provider setup can persist the provider-visible subset through `AgentMemoryProvider.save_config()`.

Raw memory/skill payloads are **not** persisted by default. Local evidence stores payload digests and operational metadata unless `record_payloads=true` is explicitly selected.

## Exact profile detection

Qualification applicability is commit-bound.

The integration detects the observed Hermes source revision from:

1. `AGENT_MEMORY_HERMES_REVISION`, when explicitly supplied by a packaged/deployment environment; or
2. the imported Hermes `agent` package's containing Git checkout.

If neither yields an exact 40-character revision, the observed revision is `unknown`.

Unknown or changed revision does not inherit #317 coverage by resemblance. With the default `require_exact_profile=true`, doctor reports not ready and govern mode blocks interceptable durable tool mutations until the profile is revalidated.

## Observe mode

Observe mode registers `pre_tool_call` and `post_tool_call` hooks for the two normal model-driven durable-state surfaces available at the pinned Hermes profile:

```text
memory
skill_manage
```

It records:

- proposal operation and target;
- exact Hermes/integration profile identity;
- session/task/turn/tool-call scope supplied by Hermes;
- candidate digest;
- optional provenance/lineage refs when actually available;
- execution receipt/result digest separately from admission/proposal evidence.

The pinned Hermes hook does **not** expose `_memory_write_origin`. Therefore foreground versus `background_review` origin is not invented. The coverage report marks those background surfaces as mechanically observed/intercepted with limited origin precision.

The external `MemoryProvider` additionally observes:

- initialization/session identity;
- prefetch lifecycle calls;
- turn synchronization;
- built-in-memory post-commit mirror callbacks;
- session switch/end;
- shutdown/backup path state.

Version 0.1.0 intentionally does not invent an Agent Memory recall backend. `prefetch()` records the recall lifecycle request and returns no injected context. A future backend transport may add recall without changing the provider's admission authority, which remains none.

## Govern mode

Govern mode sends the full interceptable candidate privately to an external JSON admission command configured by `governor_command`.

Input shape includes:

```text
kind = hermes_durable_state_candidate
Hermes revision/profile
integration profile
memory | skill_manage
operation
target
session/task/turn/tool-call scope
origin hint + origin precision
lineage refs when available
provenance refs when available
full tool args for the private governor process
args digest
authority_effect = none
```

The command reads one JSON object on stdin and returns one JSON object on stdout:

```json
{
  "decision": "allow | reject | stage",
  "reason": "bounded human-readable reason",
  "evidence_refs": ["optional://reference"]
}
```

Current Hermes mapping is truthful:

```text
allow  -> allow tool execution
reject -> return Hermes native {action:block, message:...}
stage  -> block with explicit stage-unsupported explanation
```

`stage` is **not** silently treated as either allow or native Hermes write approval. The generic `pre_tool_call` hook cannot create a native staged durable mutation.

When `governor_required=true`, the following all produce an explicit native block:

- command missing;
- command cannot execute;
- timeout/nonzero exit;
- invalid JSON;
- invalid decision schema;
- exact Hermes profile drift.

This matters because Hermes intentionally isolates plugin callback exceptions. The published plugin entry point is therefore a fail-closed wrapper: integration/configuration failure while handling `memory` or `skill_manage` becomes an explicit block rather than an exception that Hermes could log and continue past.

## External MemoryProvider is not admission authority

Hermes calls `on_memory_write()` after a built-in memory mutation commits.

The Agent Memory provider records that lifecycle honestly:

```text
canonical_builtin_state = committed
external_projection = observed | failed
settled = true | false
quiescent = true | false
rollback_claimed = false
```

A provider callback failure does not retroactively claim the built-in write rolled back.

The provider is therefore useful for observation/synchronization but structurally remains outside built-in admission authority.

## Strict mode is refused

At the pinned Hermes profile:

```text
strict.supported = false
```

The exact six blockers from #317 remain:

1. `approved_pending_memory_replay`
2. `approved_pending_skill_replay`
3. `deterministic_curator_archive`
4. `journey_memory_edit_delete`
5. `journey_skill_edit_delete`
6. `out_of_band_memory_skill_filesystem_write`

If configuration requests `strict`, doctor returns nonzero and lists those blockers. The plugin also blocks the normal interceptable `memory` / `skill_manage` mutations rather than pretending those blocks somehow cover the six bypass paths.

This is intentionally inconvenient. A false strict badge would be easier to ship and much less useful.

## Doctor / coverage

Installed command:

```text
agent-memory-hermes doctor --json
```

The report contains exactly the 12 #317 mutation families and classifies each as:

```text
observed
intercepted
uncovered
not applicable
```

It also records:

- exact expected/observed Hermes revision;
- integration profile/version;
- mode;
- governor configured/required state;
- strict support and blockers;
- origin-precision limitations;
- five recursive-learning adversarial scenario dispositions;
- `authority_effect = none`.

The coverage file is written to:

```text
$HERMES_HOME/agent-memory/coverage.json
```

## Recursive-learning adversarial scenarios

The package carries executable evidence for all five #317 cases.

### Self-reinforcing skill lineage

When lineage/provenance refs are available, the integration preserves them to the external governor rather than collapsing each recursive artifact into a fresh independent source. The governor can reject a skill/memory proposal whose apparent corroboration is causally descended from the same lineage.

The pinned Hermes hook does not expose complete causal lineage automatically, so the integration records that limitation rather than fabricating independence.

### Corrected value proposed again by background learning

Supersession/rejection evidence supplied to the candidate is preserved to the external governor. A rejected governor decision becomes a native Hermes block.

The integration does not promote an old value merely because background learning encountered it again.

### Stale human approval replay

Still uncovered at the pinned profile. Future strict support must revalidate at least:

```text
reviewed before-state digest
current before-state digest
reviewed candidate digest
current candidate digest
scope
```

immediately before the approved pending payload commits.

### Curator retirement

Deterministic curator archival remains uncovered. Future strict support requires the persistence-adjacent middleware identified by #317 so dependency and residue obligations can be checked before retirement.

### Provider mirror failure after built-in commit

Executable provider tests prove the required lifecycle distinction:

```text
built-in state committed
external projection failed
settled = false
quiescent = false
rollback_claimed = false
```

## Evidence and privacy

Local event evidence is JSONL under:

```text
$HERMES_HOME/agent-memory/events.jsonl
```

Default persisted records use hashes rather than raw memory/skill content. The full candidate is sent to the configured external governor process because admission may require semantic inspection, but local payload persistence remains opt-in.

Evidence identity is not authority. Event records always carry:

```text
authority_effect = none
```

## Upstream strict-mode prerequisite

#317 identified the smallest clean Hermes interoperability primitive as a generic persistence-adjacent durable-state mutation middleware:

```text
before_durable_state_mutation(event)
  -> allow | stage | reject

canonical persistence

after_durable_state_mutation(receipt)
```

That middleware must cover normal model tools, approved pending replay, deterministic curator lifecycle, Journey edits/deletes, and equivalent canonical durable writes.

It should be vendor-neutral. Agent Memory would be one consumer, not a Hermes core dependency.

## Claim boundary

This integration proves useful observe/govern behavior at one exact Hermes source profile. It does not claim:

```text
plugin/provider coverage == strict coverage
MemoryProvider mirror == built-in admission authority
Hermes native Block == Agent Memory policy authority
repetition == independent corroboration
human approval == current execution validity
provider failure == built-in rollback
old Hermes qualification == future Hermes qualification
```

Hermes keeps its recursive loop. Agent Memory governs only the durable consequences it can actually reach, and reports the rest rather than hiding them.