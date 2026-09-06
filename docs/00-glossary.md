# Canonical Glossary

## Agentic memory

Retained state that can alter an agent's future interpretation, reasoning, planning, tool use, action, or adaptation across a meaningful persistence boundary.

## Artifact

Any object that may enter memory: text, code, trace, decision, event, observation, file, relation, failure, correction, or user preference.

## Memory unit

A governed representation of an artifact or relation that carries identity, evidence, state, scope, and lifecycle metadata.

## Working memory

Capacity-limited active state used during current reasoning or action. In agent systems this may include context-window content, scratch state, active plans, and recent tool results. Working memory is not automatically durable.

## Episodic memory

Memory of an event situated in time, context, and usually sequence. Agent examples include interaction histories, incidents, task trajectories, and action/outcome records.

## Semantic memory

Generalized factual or conceptual knowledge that is not primarily represented as one specific event. Semantic memory may be derived from one or more episodic records but should preserve evidence links when consequential.

## Procedural memory

Retained knowledge of how to perform a task, workflow, or skill. Agent examples include runbooks, successful tool sequences, recovery procedures, and environment-specific operating knowledge.

## Prospective memory

Memory of an intended future action, obligation, condition, deadline, or follow-up. Prospective memory records what must happen later; a scheduler or executor may be a separate subsystem.

## Failure memory

Structured memory of an unsuccessful action, its context, cause, correction, verification, and applicability. Failure memory exists to prevent repeated failure without overgeneralizing one incident.

## Inherited memory

Retained information available to an agent that the current agent did not directly experience. Examples include pretrained knowledge, seed policies, organizational doctrine, imported runbooks, and predecessor-agent lessons.

## Collective memory

Memory maintained across multiple actors or beyond one individual's lifetime or process. Agent examples include shared repositories, organizational policies, ledgers, runbooks, and team knowledge stores.

## UOR identity

A deterministic address or identity reference for an object. UOR identity answers what the object is. It does not decide whether the object should persist.

## Observation

A record that some system, tool, agent, user, test, or runtime witnessed an artifact or relation.

## Evidence

The support behind an observation. Evidence may include source files, hashes, traces, test results, user approval, external corroboration, runtime telemetry, or ledger records.

## Provenance

The origin and method history of a memory unit: who or what created it, when, from what source, by what method, under which authority, and whether it was observed, inferred, taught, imported, inherited, or synthesized.

## Source trust

An estimate or policy classification describing the reliability and authority of a source over time. Source trust is distinct from the confidence, relevance, or popularity of an individual memory.

## Scope

The context in which memory is valid, visible, or authoritative. Scope may include user, tenant, project, role, time window, environment, purpose, or policy domain.

## Fiber

A dimension of relation, relevance, durability, or support that may contribute to saturation. A fiber may represent access, corroboration, dependency, verification, cross-reference, user approval, or policy relevance.

## Saturation

A calibrated lifecycle score that estimates whether a memory should persist, decay, route, or become a crystallization candidate. Saturation is not correctness.

## Decay

A reduction in operational weight or retrieval priority over time, pressure, conflict, or lack of reinforcement. Decay need not imply deletion.

## Half-life

The expected time or activity interval over which a memory loses a defined portion of its operational weight.

## Pressure

A contextual factor that may increase or decrease decay, such as resource load, volatility, contradiction rate, active project churn, or user attention constraints.

## Consolidation

A process that transforms retained experience into a more durable or reusable representation. Consolidation may preserve detail, compress it, extract semantic facts, induce procedures, or build higher-level models.

## Reconsolidation

A governed revision process in which retrieved memory is updated, refined, superseded, or otherwise transformed after new evidence or context arrives.

## Generalization

The intentional reduction of event-specific detail in exchange for reusable structure that transfers across related situations. Generalization is useful information loss only when important exceptions and provenance remain available where needed.

## Forgetting

Any governed process that reduces the future influence or accessibility of retained information. Forgetting may include decay, suppression, pruning, archival, compression, supersession, deletion, or other mechanisms. These operations are not interchangeable.

## Suppression

A policy or retrieval decision that makes memory less likely or prohibited from entering active context while the underlying record may remain stored.

## Pruning

Removal of memory from an active store because policy determines that continued operational retention is unnecessary or harmful.

## Archival

Movement of memory out of normal active recall while preserving recoverability for history, audit, compliance, or rare use.

## Supersession

A relation in which newer or higher-authority memory becomes the active representation while older memory remains historically valid or auditable.

## Tombstone

A minimal durable marker recording that content was deleted, revoked, or superseded so removed memory is not silently recreated or treated as merely missing.

## Crystallization

A governed transition where a memory becomes durable, exact-address retrievable, or canonical within a defined scope.

## Certification

A verification or approval record that confirms a memory may cross a permanence or authority boundary.

## Mutation

A controlled change to a memory unit, relation, state, score, policy, or derived representation.

## PAMA

Proportional Adaptive Mutation Authority. PAMA determines what the system is allowed to change, promote, demote, prune, or canonize based on authority, risk, evidence, and adaptive constraints.

## Retrieval admission

A policy decision determining whether a retrieved candidate may enter active agent context. Retrieval admission considers scope, sensitivity, freshness, contradiction, authority, and task relevance in addition to similarity.

## Reflection

A synthesized higher-level interpretation derived from one or more memories. Reflection is an inference and must not be treated as evidence or certification merely because it is concise or repeatedly recalled.

## Neurospace

The operational runtime memory space where agents assemble, traverse, retrieve, and use governed memory.

## Vault

The local or product-level memory container for encrypted storage, graph recall, RAG, and context assembly.

## CodeGenome

A canonical code reality graph that models software artifacts through content addressing, overlays, provenance, confidence fusion, and graph traversal.

## Shadow Genome

A failure-memory substrate that stores negative constraints, failure patterns, and blocked behaviors so agents can avoid repeating known harms.

## Hallucination permanence

A failure mode where a system promotes an incorrect or unsupported memory into durable state because it was repeatedly accessed, confidently stated, or overfit to a weak signal.

## Access-spam

A trap condition where a low-value or false memory is repeatedly accessed, causing naive systems to inflate durability incorrectly.

## Memory poisoning

An attack or failure mode in which malicious, misleading, or unauthorized content becomes persistent memory and later changes agent behavior.

## Dispute

A lifecycle state where new evidence, contradiction, or policy challenge weakens the memory's claim to durability or current use.

## Correction

A governed update that resolves a disputed, stale, incomplete, or incorrect memory while preserving prior provenance and mutation history.

## Canonical memory

A memory treated as durable within a defined scope after identity, provenance, saturation, authority, and certification gates pass.

## Operational memory

A memory that is useful for runtime action but not necessarily durable, certified, or canonical.

## Conformance

The ability of an implementation to demonstrate that it follows this doctrine through tests, traces, evidence bundles, benchmarks, or audit records.
