# Cross-Domain Composition Evidence

## Question

Can two memories that each pass governed recall still be refused when their **combination** violates an explicit policy constraint?

## Doctrine under test

Canonical doc 41 states that individual admission does not prove a combined context is safe. Domain provenance must survive long enough for a composition-risk gate to evaluate the set.

This slice does not create a universal rule that different domains may never compose. That would convert one threat case into architecture law without evidence.

Instead, `reference/agentmem_ref/composition.py` accepts explicit set-level constraints. A constraint names the domain combination that current policy forbids. The composition evaluator then verifies that every proposed memory already passed candidate-level admission, preserves domain provenance across the set, and fails closed when an explicit prohibited combination is present.

## Research support

The implementation direction is consistent with, but not defined by, established access-control and information-flow work:

- NIST SP 800-162 evaluates authorization from attributes of the subject, object, requested operation, and environment against policy rather than treating prior access as universal permission.
- NIST SP 800-207 rejects implicit trust from location and instead requires resource-specific access decisions.
- Decentralized information-flow-control research demonstrates why locally permitted component operations still require enforcement of permitted flows across composed/distributed systems.

References:

- https://doi.org/10.6028/NIST.SP.800-162
- https://doi.org/10.6028/NIST.SP.800-207
- Zeldovich, Boyd-Wickizer, and Mazières, *Securing Distributed Systems with Information Flow Control*, NSDI 2008, https://www.usenix.org/conference/nsdi-08/securing-distributed-systems-information-flow-control

These sources are research inputs. They do not become Agent Memory doctrine by citation.

## Executable evidence

`reference/tests/test_composition_gate.py` proves four boundaries:

1. two memories from different logical project domains can each pass governed recall when the request context is authorized for both;
2. an explicit set-level policy constraint can still block their combined context;
3. absence of such a constraint does not cause the reference path to invent a blanket cross-domain prohibition;
4. the composition stage cannot reintroduce a memory that recall did not admit, and unresolved domain provenance fails closed.

The permanent fixture `fixtures/cross-domain-composition-risk.json` records the adversarial case from issue #68.

## Claim boundary

This is a local executable composition-policy seam, not a universal information-flow proof, noninterference proof, policy language, or full context-assembly subsystem.

It establishes:

```text
individual_recall_admission
!=
composition_permission
```

when explicit policy says the combined set is prohibited.

It does not claim that all cross-domain combinations are unsafe, that domain identity alone is enough to derive every composition policy, or that the reference adapter now satisfies a higher cumulative conformance level.
