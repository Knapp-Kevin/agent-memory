# P7 Governed Interchange Evidence

## Purpose

Exercise the Agent Memory Profile 6 seam without defining a transport standard or making any upstream submission.

The local evidence asks three progressively stronger questions:

1. can one governed system export memory to another without losing ownership, provenance, lifecycle, sensitivity, scope provenance, or receiver-local authorization;
2. can later source correction, supersession, revocation, or deletion obligations remain visible without turning the sender into a remote mutation authority over the receiver;
3. can the receiver actually execute those locally authorized consequences against its own store and prove deletion completeness with the existing P4 residue machinery?

External projects are not modified, asked to adopt the contract, or treated as implementation dependencies.

## V1: governed export and import

The reference path under `reference/agentmem_ref/interchange.py` enforces:

1. sender export requires a schema-valid memory and a committed governed boundary-crossing receipt;
2. the crossing receipt must bind the exported memory id;
3. cross-system export requires explicit ownership and source isolation-domain bindings;
4. sender-side authorization travels with the bundle as evidence, not as receiver permission;
5. the receiver evaluates a local `scope_expansion` proposal through its own PAMA path;
6. an ownership conflict fails closed before admission;
7. successful import preserves stable identity, lifecycle state, provenance, sensitivity, and owner;
8. successful import binds the receiving isolation domain while retaining source-domain provenance;
9. the imported memory records the receiver's authority envelope, not the sender's authority refs.

The companion fixture `fixtures/cross-system-authority-conflict.json` makes the authority-conflict case from `docs/35-interoperability-profiles.md` permanent in the conformance corpus.

## V2: lifecycle-obligation continuity

A successful import emits a local `InterchangeLink` binding the imported memory to source system, receiver system, source crossing receipt, source isolation domains, and receiver isolation domain.

A later `SourceLifecycleNotice` may report correction, supersession, revocation, or deletion. The notice is evidence of a source-side lifecycle change, not permission to mutate receiver state. The receiver verifies identity/source linkage, maps the notice to a local consequence, and evaluates that consequence under current receiver PAMA policy and authority. Unresolved review leaves local state untouched.

## V3: two-store correction and deletion propagation

`reference/agentmem_ref/interchange_propagation.py` composes the notice contract with two existing first-party mechanisms rather than creating an interoperability shortcut:

- receiver correction uses `GovernedMemoryAdapter.commit_proposal(operation="correction")`, emits the normal decision receipt, writes replacement state in the receiver's own store, and then marks the prior receiver fact superseded rather than erasing history;
- receiver deletion uses `GovernedMemoryAdapter.governed_delete(operation="permanent_deletion")`, then runs the existing P4 projection purge plan, independent residue sweep, four-way residue partition, and `DeletionCompletenessMeasurement`.

The executable test uses two separate `InMemoryTemporalGraph` stores and two separate governed adapters. A sender-side correction/deletion receipt becomes notice evidence. The receiver still makes and receipts its own local decision.

The deletion path has both a clean case and an adversarial late-projection case. In the adversarial case, a receiver-side content-bearing projection appears after purge traversal. The independent sweep must classify it as `undeclared_residual`; therefore:

```text
valid receiver deletion receipt
        !=
receiver forgetting completeness
```

until the independent sweep reports zero residual state.

## Evidence boundary

This demonstrates local executable interoperability behavior. It does not claim a universal interchange wire format, Profile 6 conformance for the entire reference adapter, automatic trust of imported memory, transfer of ownership/certification/mutation authority, production transport security, or adoption by any external project.

No upstream PR, issue, comment, patch, or submission is part of P7.

## Validation

`reference/tests/test_interchange.py` covers authority and lifecycle-notice boundaries. `reference/tests/test_interchange_propagation.py` covers:

- correction across two concrete local stores with receiver-local PAMA and receipt evidence;
- prior receiver state retained as superseded rather than silently overwritten;
- receiver-local permanent deletion after source deletion evidence;
- clean deletion with zero undeclared residue and satisfied lifecycle measurement;
- late receiver projection detected as undeclared residue, preventing a false forgetting claim.

Repository CI executes these alongside the existing fixture/schema/doctrine, P4 deletion-completeness, comparator, real-substrate, and conformance paths.

## Remaining P7 posture

V1-V3 establish the local reference mechanics for governed import, authority conflict, lifecycle continuity, and actual correction/deletion propagation with residue accounting. This is substantial Profile 6 evidence, but a full Profile 6 claim remains cumulative and must still satisfy the complete profile prerequisites and declared fixture scope rather than being inferred from these slices alone.
