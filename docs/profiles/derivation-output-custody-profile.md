# Derivation Output Custody Profile

Status: V0.1 canonical custody extension for #212.

## Purpose

A derivation may need to prove which transformed artifact was produced without copying that artifact into the provenance envelope.

The canonical `derivation-evidence` transformation block therefore supports an optional typed and digested custody pair:

```text
output_ref
output_type
output_digest
```

`output_ref` remains the backward-compatible minimum. When either `output_type` or `output_digest` is supplied, both are required.

## V0.1 digest contract

`output_digest` uses:

```text
sha256:<64 lowercase hexadecimal characters>
```

The digest establishes bounded byte-custody evidence for the referenced transformed artifact.

It does **not** establish:

```text
integrity match != semantic correctness
integrity match != truth
integrity match != authority
integrity match != certification
integrity match != memory admission
```

A faithfully hashed bad summary is still a faithfully hashed bad summary. Computers are very good at being precisely wrong.

## Privacy and minimization

The provenance envelope records only type/ref/digest metadata.

Caller fields such as:

```text
raw_output
output_payload
prompt
hidden_reasoning
full_transformed_content
```

have no output path through `normalize_derivation(...)` or `derive_from(...)`.

Raw transformed content may be retained elsewhere under normal memory/evidence policy when required. This custody profile does not require it.

## Backward compatibility

Historical V0.1 derivations containing only:

```text
transformation.output_ref
```

remain valid.

Typed/digested custody is additive rather than a schema migration that invalidates earlier evidence.

## Pair completeness

Partial custody claims fail closed:

```text
output_type without output_digest -> reject
output_digest without output_type -> reject
malformed digest -> reject
```

This prevents a record from looking reconstructable while silently omitting one half of the custody claim.

## Identity behavior

The normalized transformation block participates in deterministic `derivation_id` generation.

Therefore:

```text
same source + same transformation + same output type/ref/digest
-> same derivation identity

same source + same transformation + changed output digest
-> different derivation identity
```

A different digest means the transformation evidence refers to different output bytes. It does not mean the later output has more authority.

## Child derivations

`derive_from(...)` carries typed/digested custody for each new transformation independently.

A child derivation still preserves the original root-source lineage from the canonical derivation model.

```text
root source A
 -> derived artifact B(type/ref/digest)
 -> derived artifact C(type/ref/digest)

root origin of C = A
```

B and C do not become independent corroborating origins merely because both have integrity digests.

## Relationship to currentness

Typed/digested output custody does not alter the currentness model from #210.

A derivation whose root source is revoked, superseded, tombstoned, deleted, disputed, or otherwise non-current still requires revalidation regardless of output digest integrity.

Likewise, a complete typed/digested transformation whose sources remain current may evaluate current under the bounded currentness contract, but that result still does not establish memory authority or admission.

## Relationship to #202 / PR #203

Issue #202 requested transformed output type/ref/digest custody. Draft PR #203 implemented that requirement inside a separate `transformation-evidence` ontology.

The canonical implementation path is now:

```text
#204 / PR #205
  -> canonical derivation provenance + authority-laundering containment

#210 / PR #211
  -> append-only source currentness + governed scope propagation + transform mode/status

#212
  -> typed/digested transformed-output custody
```

This preserves the useful requirement without shipping a second overlapping provenance schema.

## Non-claims

V0.1 does not claim:

- output digest proves semantic truth;
- output type is certification;
- content-addressed custody grants authority;
- digested output becomes durable memory automatically;
- one digest format solves all artifact provenance problems;
- production custody or external certification.

## Stop line

Keep custody metadata as evidence. If the transformed artifact is proposed for durable Agent Memory state, the normal admission, source-currentness, scope, and PAMA boundaries still apply.
