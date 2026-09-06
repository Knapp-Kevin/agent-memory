# Memory Threat Model

> Canonical requirement: [ADR-008](adr/ADR-008-memory-threat-model-is-required.md)

## Purpose

Persistent memory turns an agent from a session-bound system into a stateful system whose mistakes, compromises, and authority errors can survive the interaction that created them.

This threat model defines the major adversarial and accidental failure classes that Agent Memory implementations should defend against.

The core security rule is:

> Memory content may be uncertain or adversarial. Memory authority must not be inferred from content, confidence, similarity, repetition, or apparent usefulness.

The contracts that enforce that rule live elsewhere; this document names the attacks, those documents own the defenses: mutation authority in [`04-governance-and-pama.md`](04-governance-and-pama.md) and the decision table of [`33-pama-decision-table.md`](33-pama-decision-table.md), evidence weighting in [`16-source-trust-and-reputation.md`](16-source-trust-and-reputation.md), and recall-time admission in [`26-governed-recall-planner.md`](26-governed-recall-planner.md). Probabilistic detectors throughout this threat model estimate risk; they never grant or revoke authority.

## Assets

The memory system may protect:

- user facts and preferences
- credentials and sensitive data
- organizational decisions
- policies and safety constraints
- code and operational knowledge
- source provenance
- audit history
- correction and dispute records
- deletion state and tombstones
- agent procedures and prospective obligations
- scope and tenant boundaries

## Security properties

A conforming architecture should preserve:

```text
INTEGRITY
untrusted content cannot silently become canonical memory

CONFIDENTIALITY
memory cannot cross actor, tenant, sensitivity, or policy boundaries without authority

AUTHORITY INTEGRITY
content cannot manufacture permission to mutate, share, delete, certify, or act

PROVENANCE INTEGRITY
origin and transformation history survive summarization and derivation

TEMPORAL INTEGRITY
stale authorization and superseded policy cannot silently control current state

DELETION FIDELITY
required forgetting propagates through raw, derived, summarized, indexed, and cached forms

RECOVERY
corruption and unsafe mutation have a defined detection, rollback, correction, or containment path
```

## Trust boundaries

Key boundaries include:

1. external content -> observation
2. observation -> memory write candidate
3. candidate -> durable memory
4. memory store -> retrieval candidate
5. retrieval candidate -> active context
6. active context -> agent action
7. agent inference -> memory mutation proposal
8. proposal -> PAMA / policy decision
9. authority envelope -> committed mutation
10. one user/tenant/agent -> another
11. raw memory -> summary / consolidation / semantic memory
12. deletion request -> every derived representation

Each boundary should identify what may be probabilistic and what must remain enforced.

## Threat classes

### 1. Direct memory poisoning

An attacker causes malicious, false, or manipulative content to be persisted so it influences later sessions.

Attack path:

```text
untrusted input
  -> accepted memory
  -> later retrieval
  -> behavior change
```

Controls:

- origin-aware write admission
- source trust as evidence, not authority
- quarantine or ephemeral-only modes
- certification before high-authority durable promotion
- retrieval-time re-evaluation
- correction and dispute paths

### 2. Sleeper memory poisoning

Malicious content remains dormant until a later context triggers retrieval or action.

Controls must therefore operate beyond write time.

Required posture:

```text
write-time safety != lifetime safety
```

Read-time and action-time governance remain necessary.

### 3. Authority laundering

Untrusted content gains apparent authority through transformations such as:

- summarization
- trusted-tool echo
- repeated agent self-citation
- manufactured corroboration
- cross-agent restatement
- consolidation into semantic memory

Controls:

- preserve origin binding through derivation
- distinguish evidence lineage from authority lineage
- require explicit authority elevation
- prevent self-corroboration from counting as independent support

### 4. Recursive self-citation

An agent writes an inference, later retrieves it as evidence, then treats the retrieval as independent corroboration.

Required invariant:

```text
derived_from(self) != independent corroboration
```

### 5. Access-spam reinforcement

Repeated access artificially inflates saturation or permanence.

Controls:

- low raw-read weight
- deduplicated evidence lineage
- diminishing reinforcement for identical evidence
- trap-class conformance

### 6. Hallucination permanence

A confident but false inference becomes durable through repetition or internal reuse.

Controls:

- confidence is not certification
- contradiction and verification paths
- high-consequence promotion requires stronger evidence
- durable state remains correctable

### 7. Provenance stripping

Transformation removes source, scope, uncertainty, tenant, or authority metadata.

Examples:

```text
source memory -> summary without tenant tag
probabilistic claim -> plain text fact
untrusted origin -> trusted aggregate
```

Controls:

- typed derivation records
- mandatory scope inheritance
- provenance-preserving summaries
- conformance tests for metadata survival

### 8. Scope and tenant leakage

A highly relevant memory from the wrong user, tenant, project, or authorization domain enters context.

Required invariant:

```text
relevance != permission
```

Controls:

- deterministic or formally bounded scope enforcement
- tenant binding on memory identity/metadata
- post-retrieval admission checks
- deny or escalate on ambiguous scope

### 9. Sensitive-memory extraction

Attackers intentionally probe memory to reconstruct private information.

Controls may include:

- least-privilege retrieval
- restricted recall surfaces
- sensitivity-aware summarization
- query and extraction-rate controls
- differential disclosure policies where appropriate
- audit of sensitive memory access

### 10. Deletion residue

A deletion request removes a raw record while derived summaries, embeddings, graph nodes, caches, or consolidated memories retain recoverable content.

Controls:

- dependency-aware deletion graph
- tombstones or redaction propagation
- deletion verification across memory tiers
- retention-policy receipts

### 11. Stale policy retention

A memory is correctly handled under an old policy but later reused after policy changes.

Controls:

- bind consequential decisions to policy version
- invalidate or re-evaluate where policy requires
- distinguish policy change from estimator change

### 12. Stale authorization reuse

PAMA authorizes an action for state snapshot S1, but the memory changes before commit.

Controls:

- bind authorization to state/version
- compare-and-swap or equivalent concurrency control
- require re-authorization after material state change

### 13. Stochastic policy bypass

A planner is given both permitted and prohibited actions and samples the prohibited one.

Required invariant:

```text
randomness does not create permission
```

The planner's selectable set must already exclude prohibited actions.

### 14. Unsafe multi-memory composition

Individual memories are benign alone but dangerous when combined.

Examples:

- two partial secrets reconstruct a credential
- several harmless instructions form an attack chain
- distributed poisoned memories trigger only when retrieved together

Controls:

- context-level admission and composition checks
- information-flow analysis for high-risk domains
- multi-memory conformance fixtures

### 15. Estimator manipulation

An attacker changes inputs specifically to exploit confidence, trust, relevance, sensitivity, or utility estimators.

Controls:

- adversarial calibration tests
- uncertainty and out-of-distribution signals
- multiple independent signals where justified
- no direct authority from estimator output

### 16. Calibration drift exploitation

An estimator remains technically functional but its calibration no longer matches current data or attack conditions.

Controls:

- calibration versioning
- drift monitoring
- scope-of-validity metadata
- conservative fallback for high-consequence decisions

### 17. Malicious or mistaken correction

A correction surface is used to overwrite accurate memory or remove evidence.

Controls:

- correction authority
- prior-state preservation
- conflict handling rather than silent replacement
- audit receipt

### 18. Permanent deletion abuse

A utility or staleness estimate triggers irreversible deletion of valuable or evidentiary memory.

Controls:

- separate prune/archive/delete modes
- retention and legal/policy checks
- dependency checks
- stronger authority as reversibility decreases

### 19. Promotion-queue flooding

The proportional-handling lanes concentrate friction at promotion and review boundaries, which makes those boundaries the highest-value place to attack by volume rather than by quality. An attacker, a compromised estimator, or merely a noisy environment floods the review queue with plausible-looking candidates until reviewer attention degrades, then a bad promotion rides through on fatigue. This is governance-fatigue exploitation, and it is a direct consequence of the architecture's own design choice to make review the gate.

Attack path:

```text
many plausible candidates -> review queue saturates -> reviewer throughput or
scrutiny degrades -> marginal candidate approved under fatigue -> durable authority gained
```

Controls:

- admission cost: candidates must clear evidence-quality floors before consuming review capacity, so flooding pays the evidence cost per candidate, not the reviewer
- pre-adjudication triage separating "needs adjudication" from "worth a look" by consequence, per the review-budget rules of [`37-memory-economics-and-budget-policy.md`](37-memory-economics-and-budget-policy.md)
- per-source and per-estimator rate accounting on promotion proposals; a source whose candidate volume spikes is itself an anomaly signal feeding source trust
- batched review windows with explicit capacity, so saturation becomes a visible queue-depth metric instead of silent scrutiny decay
- fatigue never relaxes the gate: queue pressure produces conservative interim state, never auto-approval; load-shedding only as a versioned policy mutation
- queue-depth, review-latency, and approval-rate-under-load metrics monitored as attack indicators, not just operations telemetry

### 20. Durable decision authority capture

An agent or coalition of agents turns a proposal to revisit an earlier durable decision into a committed reversal without the authority that the earlier decision's scope and consequence require.

Attack variants include:

- **agent collusion**: several agents agree that a prior human-confirmed decision should change and treat their agreement as equivalent to human confirmation;
- **stale approval replay**: a real approval is reused after the target decision state, scope, policy, or proposal changed;
- **authority substitution**: a grant for another target, actor, mutation class, scope, or risk ceiling is presented as sufficient for the overwrite;
- **silent reversal**: a replacement becomes current without an explicit `supersedes` relationship and append-only authority evidence;
- **self-approval**: the proposing actor supplies or ratifies its own authority transition;
- **approval stripping**: the runtime validates an authority grant but writes a replacement decision that no longer carries the grant reference needed to reconstruct why it became current.

Required invariant:

```text
proposal evidence
!=
overwrite authority
!=
PAMA permission
```

Controls:

- represent proposal, authority resolution, PAMA decision, and committed supersession as separate events;
- bind overwrite authority to exact proposal, target decision, actor eligibility, scope, mutation class, state snapshot, risk ceiling, issue/expiry window, and revocation state;
- require fresh human confirmation for prior human-confirmed decisions and for the high/critical reference-profile cases defined in [`profiles/durable-decision-memory-profile.md`](profiles/durable-decision-memory-profile.md);
- preserve bounded delegated policy as an explicit authority object rather than inferring delegation from repeated approvals or agent consensus;
- reject stale, expired, revoked, mismatched, self-approved, or unrecorded authority before durable mutation;
- preserve the prior decision as historical evidence and append a supersession record rather than destructively rewriting it;
- evaluate PAMA after decision-specific authority validation so a valid grant cannot override an independent PAMA block;
- retain rejected overwrite proposals and failed authority attempts as audit evidence.

## Probabilistic security components

The threat model does **not** require every defense to be deterministic.

Probabilistic components may legitimately estimate:

- maliciousness
- source trust
- anomaly likelihood
- sensitivity
- contradiction
- semantic relevance
- poisoning risk
- utility
- composition risk

The governance requirement is that these estimates cannot create their own authority.

```text
risk estimate
  -> policy envelope
  -> block / quarantine / review / allow-under-constraints
```

## Deterministic or formally bounded security consequences

Strong invariants should include:

- cross-tenant denial
- invalid transition denial
- policy-version binding
- required provenance fields
- action-set exclusion
- deletion scope semantics
- ledger creation for consequential changes
- certification requirements
- concurrency/version checks
- exact durable-decision overwrite authority binding

## Threat severity

Evaluate threats along at least:

```text
persistence
blast radius
sensitivity
authority gained
reversibility
detectability
cross-session reach
cross-agent reach
evidence destruction
```

A low-probability attack that gains durable authority can be more serious than a frequent ephemeral error.

## Required conformance cases

At minimum:

- direct poisoning
- sleeper poisoning
- recursive self-citation
- provenance stripping
- cross-tenant high-relevance recall
- stochastic policy bypass
- unsafe multi-memory composition
- uncertain sensitivity
- stale authorization
- deletion residue
- permanent deletion from predicted low utility
- estimator drift
- promotion-queue flooding under review-capacity pressure
- durable decision overwrite without current authority
- agent consensus attempting to replace a human-confirmed durable decision
- stale durable-decision overwrite approval

## Research signals

Accessible current work reinforces several threat-model choices:

- [Memory Poisoning Attack and Defense on Memory Based LLM-Agents](https://arxiv.org/abs/2601.05504) evaluates poisoning robustness and shows trust thresholds require careful calibration.
- [Hidden in Memory: Sleeper Memory Poisoning in LLM Agents](https://arxiv.org/abs/2605.15338) studies delayed persistent poisoning across later conversations.
- [AgentSys: Secure and Dynamic LLM Agents Through Explicit Hierarchical Memory Management](https://arxiv.org/abs/2602.07398) demonstrates the value of explicit memory isolation and schema-validated boundary crossing.
- [Securing LLM-Agent Long-Term Memory Against Poisoning](https://arxiv.org/abs/2606.24322) argues for non-malleable origin-bound authority and explicitly studies authority laundering through memory transformations.
- [Toward Secure LLM Agents](https://arxiv.org/abs/2606.10749) frames persistent state, delegated authority, provenance, and compositional weakness as central agent-security concerns.

These sources inform threats and design candidates. They do not make any one defense universal doctrine without implementation evidence.

## Doctrine

Persistent memory is a security boundary because it can turn transient untrusted information into future behavior.

The system must govern not only **what gets remembered**, but what remembered information is ever allowed to **authorize**.