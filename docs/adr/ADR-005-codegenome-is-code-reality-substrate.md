# ADR-005: CodeGenome Is the Code Reality Substrate

## Status

Accepted

## Context

CodeGenome models codebases as content-addressed, multi-layer reality graphs. It includes syntax, semantic, flow, process, runtime, SCIP, LSP, provenance, and confidence overlays.

This makes it a domain reality graph for software artifacts, not a general memory runtime by itself.

## Decision

CodeGenome is the canonical code-reality substrate within the current Agent Memory architecture mapping.

It should provide evidence, graph relations, provenance, confidence, and impact traversal for code artifacts consumed by agentic memory systems.

## Consequences

### Positive

- preserves CodeGenome as a strong domain substrate
- allows memory systems to consume code reality without reimplementing code understanding
- separates code confidence from memory durability

### Negative

- requires mapping between code graph nodes and memory units
- requires careful treatment of stale code artifacts

## Required boundary

```text
CodeGenome confidence supports evidence.
It does not automatically grant memory permanence, certification, or authority.
```

Inferred graph relations should preserve their estimator/method provenance and uncertainty when material to downstream decisions.

## Acceptance scope

Accepted means this is the canonical architectural role assigned to CodeGenome. It does not claim every CodeGenome capability is implemented or required by every Agent Memory implementation.

## Doctrine

CodeGenome provides a code-reality substrate.

The memory lifecycle and governance layers decide how its observations persist, are disputed, and affect agents over time.
