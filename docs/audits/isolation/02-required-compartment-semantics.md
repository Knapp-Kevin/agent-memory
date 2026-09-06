# Required Compartment Semantics Research and Evidence

## Purpose

Resolve the final semantic question left open by the issue #68 gap reconciliation: when a memory is associated with multiple logical domains, does one matching domain authorize recall, or must every domain be present?

The answer is that **both semantics are legitimate, but they represent different policy meanings and must not be overloaded onto one field**.

This document records research support and the executable reference decision. It clarifies the implementation surface; it does not establish a universal hierarchy of compartments.

## Existing behavior

Before this slice, the reference adapter treated `isolation_domain_refs` as alternative governed routes:

```text
memory_domains ∩ target_domains != empty
=> domain route satisfied
```

Other gates still applied, including shared-space membership, project, task, lifecycle state, and dispute state.

That behavior is appropriate for a memory eligible through multiple governed domains. It is not sufficient to express a memory that requires **all** of several compartment constraints.

## Research pressure

### NIST SP 800-162: Attribute Based Access Control

NIST defines ABAC authorization as evaluation of subject, object, requested-operation, and relevant environment attributes against explicit policy rules or relationships.

Relevant implication for Agent Memory:

- a multi-valued attribute is not inherently OR or AND;
- the policy relationship defines which combinations are required;
- authorization should therefore preserve the distinction between alternative routing attributes and mandatory constraint attributes.

Reference:

- NIST SP 800-162, *Guide to Attribute Based Access Control (ABAC) Definition and Considerations*: https://doi.org/10.6028/NIST.SP.800-162

### NIST mandatory / non-discretionary access control terminology

NIST describes mandatory access control as restricting access based on information sensitivity labels and formal user authorization, with subjects prevented from freely passing protected information or changing security attributes.

Relevant implication for Agent Memory:

- a compartment/sensitivity requirement is an enforced authorization condition, not merely another discoverable namespace;
- satisfying one routing domain cannot erase another explicitly required compartment.

Reference:

- NIST CSRC glossary, non-discretionary / mandatory access control: https://csrc.nist.gov/glossary/term/non_discretionary_access_control

These sources support the distinction. They do not define Agent Memory field names or import a mandatory-access-control hierarchy into the repository.

## Chosen semantics

### `isolation_domain_refs`

These remain ordinary governed domain bindings / routes.

For the reference adapter, at least one bound route must match the active recall context:

```text
intersection(memory.isolation_domain_refs, context.target_domain_refs) != empty
```

This preserves existing behavior and backwards compatibility.

### `required_isolation_domain_refs`

These are explicit conjunctive domain constraints.

Every required ref must be present in the active recall context:

```text
memory.required_isolation_domain_refs <= context.target_domain_refs
```

A missing required ref produces a hard admission refusal:

```text
required_isolation_domain_missing
```

### Coherence rule

A required ref must also be a bound isolation-domain ref for the memory.

```text
required_isolation_domain_refs <= isolation_domain_refs
```

An incoherent proposal fails closed at PAMA evaluation before a substrate mutation can be selected.

## Why this is additive rather than a reinterpretation

Changing all existing `isolation_domain_refs` tuples to conjunctive semantics would silently narrow previously valid memory and would encode a policy meaning that the existing field never promised.

Keeping ordinary routes separate from mandatory constraints preserves:

```text
multiple_routes != all_routes_required
shared_store != shared_authority
same_tenant != same_memory_scope
relevance != permission
```

The distinction also avoids imposing a universal hierarchy such as:

```text
tenant -> project -> task -> compartment
```

Deployments may use required constraints for compartments, legal boundaries, contractual partitions, purpose-specific enclaves, or other policy-defined domains without requiring those concepts to become fixed schema enums.

## Machine-readable representation

The reference `policy.Proposal` now carries `required_isolation_domain_refs` for runtime evidence.

A companion schema, `schemas/isolation-domain-constraints.schema.json`, provides a portable sidecar shape for binding:

- `memory_ref`
- `isolation_domain_refs`
- `required_isolation_domain_refs`
- optional policy / authority references

This deliberately avoids rewriting the existing memory-unit scope schema solely to close a test gap. Implementations may later integrate the companion contract into a canonical scope representation if comparative evidence shows that is superior to a sidecar.

## Executable evidence

`reference/tests/test_isolation_domains.py` proves:

1. an ordinary multi-domain memory is still admissible through one valid route when no conjunctive constraint is declared;
2. a same-tenant, same-project, same-task candidate is blocked when one mandatory compartment is absent;
3. the same memory is admitted when all mandatory compartments and all other gates match.

`reference/tests/test_required_compartment_semantics.py` proves:

1. a required domain not bound to the memory fails closed at PAMA evaluation;
2. a coherent required-domain declaration does not by itself strengthen or weaken the ordinary PAMA operation/risk outcome.

`fixtures/same-tenant-prohibited-compartment.json` preserves the negative path as a permanent hard-gate fixture.

## Claim boundary

This evidence supports:

- explicit separation of alternative domain routes from conjunctive required-domain constraints;
- fail-closed same-tenant compartment admission when an explicitly required domain is absent;
- preservation of existing non-hierarchical domain semantics.

It does **not** claim:

- every multiple-domain memory requires every domain simultaneously;
- universal mandatory-access-control conformance;
- a fixed compartment hierarchy;
- that a domain label alone proves user clearance or membership;
- that compartment satisfaction bypasses project, task, purpose, lifecycle, shared-space membership, crossing, or PAMA gates.

## Closure relevance for #68

The #68 gap reconciliation identified conjunctive compartment semantics as the final research question after the four concrete implementation gaps.

This slice resolves that question without changing the governing doctrine that memory scope is an authority boundary. Once this exact implementation passes repository validation, #68 may proceed to a final closure audit mapping all named negative paths and fixtures to current executable evidence.
