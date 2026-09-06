# Security and Privacy

Persistent memory creates attack surfaces that do not exist in a stateless exchange. A memory can look harmless when written and become dangerous later when another context retrieves, combines, trusts, or acts on it.

## Threat model at a glance

Agent Memory explicitly considers:

- direct memory poisoning
- sleeper memory poisoning
- hallucination permanence
- recursive self-citation
- authority laundering through summaries or trusted tools
- provenance stripping
- cross-tenant or cross-scope leakage
- sensitive-memory extraction
- unsafe multi-memory composition
- stale authorization or expired delegation
- stochastic policy bypass
- estimator manipulation and calibration drift
- malicious correction
- irreversible deletion abuse
- deletion residue in derived state

## Write-time safety is not lifetime safety

A retained item can become unsafe when:

- its original scope changes
- a delegation expires
- a new memory creates a dangerous combination
- a summary loses provenance
- a model begins to trust a poisoned source
- an old policy is replayed after policy state changed
- a deletion request fails to propagate into derived artifacts

That is why Agent Memory places security checks across storage, recall, composition, mutation, sharing, and deletion.

## Privacy is contextual

Sensitivity may be explicit or inferred. When inferred, uncertainty must remain visible.

```text
unknown sensitivity != non-sensitive
```

Privacy decisions should consider:

- actor
- tenant
- scope
- purpose
- consent
- delegation
- sensitivity
- downstream disclosure
- derived state

Relevance cannot create access permission.

## Isolation domains and controlled crossing

A physical memory service is not itself the authority boundary. One store may contain many logical isolation domains, and one agent may participate in several domains without gaining permission to move memory among them.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/isolation-domain-crossing.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/isolation-domain-crossing-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/isolation-domain-crossing-light.svg" alt="Agent Memory isolation-domain crossing diagram showing Project A Task 1, Project B Task 2, and a shared security space in one physical store; a cross-domain candidate must resolve current scope, membership, purpose, destination, and policy, pass PAMA governance, use only a permitted representation, and produce a reconstructable crossing receipt" width="100%">
  </picture>
</p>

The visual preserves several hard boundaries: `physical store != isolation domain`, `same agent != same memory scope`, and `relevance != permission to cross`. A semantically perfect Project B memory remains blocked from Project A merely because the same agent found it. Governed use resolves the target domain and current authority first, then PAMA evaluates the consequence of crossing. Shared-space membership is necessary where policy requires it, but membership alone does not grant recall admission, mutation, export, or re-sharing authority.

If a crossing is permitted, the permitted treatment may still be narrower than raw transfer, such as redacted or summary-only representation. The decision is receipted with source and destination domains, actor/principal, purpose, policy/PAMA state, representation, provenance, and outcome. Transformation does not erase inherited restrictions, and later correction, revocation, scope reduction, or purge may create propagation obligations.

**Canonical contract:** https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/41-memory-isolation-domains-and-governed-crossing.md  
**Accepted ADR:** https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-022-memory-isolation-domains-and-controlled-boundary-crossing.md

## Provenance and authority laundering

A summary, trusted tool, or higher-reputation intermediary must not silently transform low-authority content into high-authority content.

The system should preserve origin and derivation so downstream decisions can distinguish:

```text
source reliability
from
source authority
from
derived confidence
from
permission to act
```

## Deletion residue

Deletion is not complete merely because the canonical record disappeared. Controlled derived artifacts may include:

- embeddings
- search indexes
- summaries
- graph edges
- caches
- exported state
- consolidated memories

The system must state what it can actually purge and what remains outside its control. Stating it means sorting every affected artifact into one of four buckets:

| Bucket | Meaning |
|---|---|
| Purged | demonstrated removed |
| Declared residual, controlled | survives, reported, still reachable |
| Declared residual, uncontrollable | survives, reported, out of reach |
| **Undeclared residual** | survives, and nobody said so |

The fourth bucket must be empty. A deletion that leaves recoverable content it never reported is a failed deletion regardless of how much it correctly removed, which makes this a disqualifying gate rather than a metric to average.

Residue is also an authority problem and not only a completeness problem. Automatically rebuilding a stale summary looks like maintenance and is actually a write: if a language model recomputes content whenever a source version changes, an estimator has acquired a durable write channel without ever passing through the authority gate. That is authority laundering with a scheduler in front of it. **[Canonical and Derived State](Canonical-and-Derived-State)** works through both problems.

## Security reporting

Do not publish exploit details or sensitive proof-of-concept memory in public issues. Follow the repository security policy and use private vulnerability reporting when available.

Security policy: https://github.com/MythologIQ-Labs-LLC/agent-memory/security/policy

## Canonical sources

- Threat model: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/15-memory-threat-model.md
- Source trust: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/16-source-trust-and-reputation.md
- Privacy and sensitivity: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/19-privacy-and-sensitivity-classifier.md
- Scope, consent, tenancy: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/29-actor-scope-consent-and-tenancy.md
- Memory isolation domains and governed crossing: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/41-memory-isolation-domains-and-governed-crossing.md
- Retention and deletion: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/28-retention-deletion-and-tombstones.md

## Next

- **[Lifecycle and Forgetting](Lifecycle-and-Forgetting)** for deletion semantics
- **[Conformance and Evidence](Conformance-and-Evidence)** for adversarial proof
