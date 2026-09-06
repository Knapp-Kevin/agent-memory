# Security Policy

Agent Memory is primarily a reference architecture, doctrine repository, schema set, validation harness, and research/conformance project. It is not currently presented as a production security boundary by itself.

That distinction does not make security defects unimportant. A flaw in a schema, validator, workflow, reference adapter, provenance rule, source-rights gate, or governance contract can still encourage unsafe downstream implementations.

## Supported version

Security maintenance currently targets:

- the latest commit on `main`;
- the latest repository schemas and validators;
- any explicitly identified current reference implementation or adapter added under the runtime-evidence program.

Historical commits, superseded doctrine, and old experimental branches may be useful evidence, but they are not independently supported security releases.

## Reporting a vulnerability

Please do **not** publish exploit details, sensitive proof-of-concept material, credentials, private memory content, or a bypass recipe in a public issue.

For vulnerabilities in this public repository, prefer GitHub's private vulnerability-reporting / repository security-advisory flow from the repository **Security** tab when that option is available.

If private vulnerability reporting is not available to you, open a minimal public issue that contains no exploit details and asks the maintainer to establish a private reporting channel. Do not include the vulnerability payload in that issue.

## In-scope examples

Examples include:

- a conformance validator accepting a prohibited action outside the permitted action set;
- cross-scope or cross-tenant fixture logic that can incorrectly pass;
- source-rights validation that permits unclassified material reuse;
- schema behavior that strips or weakens authority, provenance, sensitivity, deletion, or policy-version semantics;
- workflow behavior that can falsify, skip, or misrepresent evidence validation;
- a reference adapter that bypasses PAMA or recall-admission boundaries;
- deletion or recovery examples that materially overstate erasure guarantees;
- unsafe handling of secrets or sensitive memory in repository telemetry/examples.

## Usually not a security vulnerability

These may still be valid bugs or research disagreements, but normally belong in public issues:

- disagreement with a doctrine choice without a concrete security failure;
- a missing feature that the repository does not claim to implement;
- a benchmark weakness without an authority/privacy/integrity consequence;
- an implementation product failing a guarantee that Agent Memory never claimed that product provided.

## Disclosure expectations

Please allow reasonable time to reproduce, assess, patch, and validate a reported issue before public disclosure. The repository will prefer an evidence-preserving fix and advisory over quietly rewriting history.

Security fixes should preserve the same doctrine boundary used elsewhere in Agent Memory:

```text
uncertain detection may propose
policy constrains consequence
committed changes remain auditable
```

## Sensitive-memory rule

Never use real credentials, private user memories, health information, financial information, or other sensitive production data as a public proof-of-concept. Synthetic fixtures are preferred.
