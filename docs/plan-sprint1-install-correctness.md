# Plan: Sprint 1 install correctness (Loop 1, ADR-035 program)

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: the wheel becomes self-contained for the commit/delete hot path only; the 14 emitter-only path-relative loaders and the two `data-files` fallbacks stay as they are until Sprint 3
- non_goals: no authority-path change (PAMA, recall, delete); no relocation of `schemas/`; no CLI subcommand additions; no ruleset or GitHub issue mutation
- exclusions: comparator packages (`agent-manifest`, `agentrust-trace`) are not made hard dependencies; Graphiti/Kuzu remain CI-only

**session**: 2026-09-02T0158-2a109f
**iteration**: 4 (amended per AUDIT_REPORT 2026-09-01T22:40 V1-V7, 2026-09-01T23:15 V1-V4, and 2026-09-01T23:45 V1-V3)
**research**: `docs/research-brief-sprint1-install-correctness-2026-09-01.md`
**workspace fragility at plan time**: high, recommended action `hardening_only`; this plan adds no new product surface, only install correctness, determinism, and CI acceptance, which is the hardening class

## Open Questions

None. Every locked decision below carries grep-evidence from `HEAD` (8b676f4).

## Locked Decisions

- **LD1** `receipts.py` gains a `schema_dir()` resolver that prefers the source tree and falls back to packaged `_schemas`. Evidence: `git show HEAD:reference/agentmem_ref/receipts.py | grep -nE 'SCHEMA_DIR =|SCHEMA_DIR / schema_name'` -> `28:SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"` and `44:    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))`.
- **LD2** Schemas are copied into the package at build time by a `setup.py` `build_py` override; root `schemas/` stays the source of truth; `data-files` entries stay until Sprint 3. Evidence: `git show HEAD:pyproject.toml | grep -nE 'data-files|schemas/'` -> `26:[tool.setuptools.data-files]`, `28:  "schemas/runtime-configuration.schema.json"`, `29:  "schemas/provider-probes.schema.json"`. Mechanism proven in research (prototype wheel contained `_schemas/*.json`; installed `resources.files` resolved).
- **LD3** `cryptography` and `rfc8785` become hard dependencies; comparators become an extra. Evidence: `git show HEAD:pyproject.toml | grep -nE '^dependencies|jsonschema'` -> `12:dependencies = [`, `13:  "jsonschema>=4.20,<5",`; `reference/requirements.txt:4,7` pin `cryptography==50.0.0`, `rfc8785==0.1.4`.
- **LD4** Cedar digest normalizes CRLF to LF before hashing; the pin value is unchanged. Evidence: `git show HEAD:reference/agentmem_ref/cedar_policy_comparator.py | grep -nE 'CEDAR_POLICY_SHA256 =|read_bytes'` -> `41:CEDAR_POLICY_SHA256 = "sha256:a369c1423d48b6656e5e19f2589cc4660e00695e3b084c0a732b3f7f7ba6e18f"` and `141:    return _sha256_bytes(policy_path.read_bytes())`. LF-normalized digest equals the pin (research F3).
- **LD5** `.gitattributes` declares `* text=auto eol=lf` plus binary rules for `png`; the index is already 100 percent LF so no committed blob changes. Evidence: `git ls-files --eol` -> 843 `i/lf w/crlf`, 0 `i/crlf`.
- **LD6** The two pin-identity tests skip unless the installed version equals the pinned constant; behavioural tests keep their existing guards. Evidence: `git show HEAD:reference/tests/test_agent_manifest_correlation.py | grep -nE 'skipIf|metadata.version\("agent-manifest"\)'` -> `56:@unittest.skipIf(MemoryCheckpoint is None, ...)`, `151:        self.assertEqual(importlib.metadata.version("agent-manifest"), AGENT_MANIFEST_SDK_VERSION)`; `test_trace_action_evidence.py:118` has the same shape with no class guard. Tests run under `python -m unittest discover -s reference/tests -t reference` (`validate-doctrine-evidence.yml:38,153`), and `reference/tests/__init__.py` exists, so helpers import as `tests.<module>`.
- **LD7** A wheel-install job is added to `cli-doctor.yml`. The existing `validate` job already installs the distribution, but no step exercises the installed package's schema loader: the installed `receipts` lives in `site-packages`, so `receipts.py:28` resolves `<prefix>/Lib/schemas` (absent) from any working directory; the job's receipts-exercising steps import the source tree instead (`cli-doctor.yml:64` runs the suite with `-t reference`; `:70` runs `python reference/run_cli_doctor.py`), and the installed console command imports `receipts` only transitively via `agentmem_ref/__init__.py:9` (`from . import adapter, governance_projection, policy, receipts, substrate`) but never calls `_validator`, which is `lru_cache`-lazy, so `SCHEMA_DIR` is never dereferenced by `agent-memory --help`. The new job builds a wheel and exercises `receipts.validate` from `/tmp`. Evidence: `git show HEAD:.github/workflows/cli-doctor.yml | grep -nE 'pip install --disable-pip-version-check \.$|^permissions|contents: read'` -> `7:permissions:`, `8:  contents: read`, `26:        run: python -m pip install --disable-pip-version-check .`; `git show HEAD:.github/workflows/provider-discovery.yml | grep -nE 'pip install --disable-pip-version-check \.$'` -> `26:        run: python -m pip install --disable-pip-version-check .`.
- **LD8** README Conformance badge is reworded to a spec-scoped phrase and linked to `docs/06-conformance-test-plan.md`, following the ADRs badge pattern. Evidence: `git show HEAD:README.md | grep -nE 'Conformance-Level|ADRs-Canonical'` -> `17:[![ADRs](https://img.shields.io/badge/ADRs-Canonical%20Index-2563eb)](docs/adr/README.md)`, `18:![Conformance](https://img.shields.io/badge/Conformance-Level%206%20Spec-7c3aed)`.
- **LD9** `docs/CONFIGURATION.md` command sketch gains `agent-memory discover`; the existing disclaimer at line 326 stays. Evidence: `git show HEAD:docs/CONFIGURATION.md | grep -nE 'agent-memory doctor|not implemented by this configuration slice'` -> `322:agent-memory doctor`, `326:These commands are not implemented by this configuration slice and are not yet public CLI commitments.`

## Phase 1: Wheel-safe receipts loader and dependency truth

### Affected Files

- `reference/tests/test_receipts_schema_location.py` - new; behaviour tests for the resolver and the validator through it
- `reference/agentmem_ref/receipts.py` - replace `SCHEMA_DIR` constant with `schema_dir()`; `_validator` reads through it
- `setup.py` - new; `build_py` subclass copies `schemas/*.json` into `reference/agentmem_ref/_schemas/` before build and fails the build when nothing was copied
- `MANIFEST.in` - new; `recursive-include schemas *.json` so the sdist carries the source schemas
- `pyproject.toml` - dependencies, optional-dependencies, package-data
- `.gitignore` - add `reference/agentmem_ref/_schemas/` (only `build/` and `dist/` are present at `.gitignore:16-17`)
- `docs/ARCHITECTURE_PLAN.md` - Dependencies table row correction

### Changes

`receipts.py`:

```python
from importlib import resources

_SOURCE_SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"


def _packaged_schemas() -> Path:
    return Path(str(resources.files(__package__) / "_schemas"))


def schema_dir() -> Path:
    """Canonical schemas: source tree when present, packaged copy when installed."""
    if _SOURCE_SCHEMAS.is_dir():
        return _SOURCE_SCHEMAS
    packaged = _packaged_schemas()
    if packaged.is_dir():
        return packaged
    raise FileNotFoundError("canonical schemas are unavailable; install the distribution with its packaged schema data")

@lru_cache(maxsize=None)
def _validator(schema_name: str) -> jsonschema.Draft202012Validator:
    schema = json.loads((schema_dir() / schema_name).read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)
```

Remove the module-level `SCHEMA_DIR` constant. Callers: `grep -rn 'receipts.SCHEMA_DIR\|SCHEMA_DIR' reference/ scripts/ integrations/` returns only `receipts.py:28,44` at HEAD, so no cross-file update.

`setup.py` (new, about 24 lines): subclass `setuptools.command.build_py.build_py`; in `run()`, copy every `schemas/*.json` into `reference/agentmem_ref/_schemas/` (create dir; overwrite), raise `RuntimeError("no schema files found under schemas/; refusing to build an empty _schemas package")` when the copied count is zero, then call `super().run()`. `setup(cmdclass={"build_py": build_py})`.

`MANIFEST.in` (new, 1 line): `recursive-include schemas *.json`, so an sdist-built wheel sees the same source files.

`pyproject.toml`:

```toml
dependencies = [
  "jsonschema>=4.20,<5",
  "cryptography>=50,<51",
  "rfc8785>=0.1,<0.2",
]

[project.optional-dependencies]
comparators = [
  "agent-manifest==0.11.0",
  "agentrust-trace==0.8.0",
]

[tool.setuptools.package-data]
agentmem_ref = ["_schemas/*.json"]
```

`data-files` block unchanged. `.gitignore`: add `reference/agentmem_ref/_schemas/`. `docs/ARCHITECTURE_PLAN.md:76`: replace the jsonschema row with three rows (jsonschema; cryptography for Ed25519 evidence signing; rfc8785 for canonical JSON) and one extras row for comparators.

### Unit Tests

- `reference/tests/test_receipts_schema_location.py`
  - `test_schema_dir_prefers_source_tree`: in the checkout, `schema_dir()` returns a directory containing `decision-receipt.schema.json` and equals `<repo>/schemas`.
  - `test_schema_dir_falls_back_to_packaged_copy`: `unittest.mock.patch.object(receipts, "_SOURCE_SCHEMAS", tmp / "missing")` and `patch.object(receipts, "_packaged_schemas", return_value=tmp / "pkg")` where `tmp / "pkg"` holds one schema file; `schema_dir()` returns `tmp / "pkg"`.
  - `test_schema_dir_raises_when_neither_exists`: both patched to nonexistent paths; `schema_dir()` raises `FileNotFoundError` whose message contains "install the distribution".
  - `test_validator_loads_through_schema_dir`: clear `_validator.cache_clear()`, point `schema_dir` at a temp dir containing a minimal `{"type":"object","required":["x"]}` named `t.schema.json`; `validate("t.schema.json", {})` raises `ValueError` mentioning `x`; `validate("t.schema.json", {"x": 1})` returns None.

## Phase 2: Deterministic digests and environment-tolerant tests

### Affected Files

- `reference/tests/test_cedar_policy_comparator.py` - add EOL-independence test
- `reference/tests/pin_support.py` - new helper (not collected: name does not match `test*.py`)
- `reference/tests/test_pin_support.py` - new; behaviour tests for the helper
- `reference/tests/test_agent_manifest_correlation.py` - guard the pin-identity test
- `reference/tests/test_trace_action_evidence.py` - guard the pin-identity test
- `reference/agentmem_ref/cedar_policy_comparator.py` - normalize in `policy_sha256`
- `.gitattributes` - new

### Changes

`cedar_policy_comparator.py`:

```python
def policy_sha256(policy_path: Path = CEDAR_POLICY_PATH) -> str:
    data = policy_path.read_bytes().replace(b"\r\n", b"\n")
    return _sha256_bytes(data)
```

Pin at line 41 unchanged.

`.gitattributes`:

```
* text=auto eol=lf
*.png binary
*.jpg binary
*.ico binary
*.pdf binary
*.woff binary
*.woff2 binary
```

`reference/tests/pin_support.py`:

```python
import importlib.metadata

def installed_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None

def pinned(distribution: str, expected: str) -> bool:
    return installed_version(distribution) == expected
```

`test_agent_manifest_correlation.py:150`: decorate `test_pinned_release_and_repository_identity_are_explicit` with `@unittest.skipUnless(pin_support.pinned("agent-manifest", AGENT_MANIFEST_SDK_VERSION), "agent-manifest is not installed at the pinned version")`. `test_trace_action_evidence.py:117`: same with `("agentrust-trace", TRACE_SDK_VERSION)`. Import as `from tests import pin_support`.

### Unit Tests

- `reference/tests/test_cedar_policy_comparator.py`
  - `test_policy_digest_is_eol_independent`: write the same policy text to two temp files, one LF and one CRLF; `policy_sha256(lf) == policy_sha256(crlf)`; the existing `test_policy_digest_is_pinned` then passes on Windows checkouts because the repo file digest equals the pin regardless of `core.autocrlf`.
- `reference/tests/test_pin_support.py` (new, collected)
  - `test_installed_version_returns_none_for_missing_distribution`: `installed_version("definitely-not-installed-xyz")` is `None`.
  - `test_pinned_true_only_on_exact_match`: `pinned("jsonschema", importlib.metadata.version("jsonschema"))` is True and `pinned("jsonschema", "0.0.0")` is False.

## Phase 3: CI acceptance and documentation truth

### Affected Files

- `.github/workflows/cli-doctor.yml` - new job `wheel-install`
- `.github/dependabot.yml` - new
- `README.md` - line 18 badge
- `docs/CONFIGURATION.md` - line 322 area, add `discover`
- `docs/future/multi-agent-shared-memory-protocol.md` - line 5
- `docs/profiles/policy-projection-compatibility-profile.md` - line 3
- `docs/profiles/temporal-commitment-evidence-profile.md` - line 3
- `docs/programs/runtime-evidence/cognitive-mesh.md` - lines 3, 190
- `docs/programs/runtime-evidence/evolveai-cognitive-mesh.md` - line 3
- `wiki-src/Runtime-Evidence.md` - lines 73, 75
- `wiki-src/Canonical-and-Derived-State.md` - line 123

### Changes

`cli-doctor.yml` new job (same trigger, `timeout-minutes: 15`, top-level `permissions: contents: read` already applies):

```yaml
  wheel-install:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m pip install --disable-pip-version-check build
      - run: python -m build --outdir dist .
      - run: python -m venv /tmp/wheel-venv && /tmp/wheel-venv/bin/python -m pip install --disable-pip-version-check dist/*.whl
      - name: Installed package resolves canonical schemas
        working-directory: /tmp
        run: |
          /tmp/wheel-venv/bin/python - <<'PY'
          import sys
          import agentmem_ref.receipts as receipts
          try:
              receipts.validate("decision-receipt.schema.json", {})
          except ValueError as exc:
              if "decision-receipt.schema.json at" in str(exc):
                  print("schema resolved from wheel:", exc)
                  sys.exit(0)
              print("unexpected ValueError:", exc)
              sys.exit(1)
          except FileNotFoundError as exc:
              print("schema NOT resolved from wheel:", exc)
              sys.exit(1)
          print("validate returned without error; empty receipt should not validate")
          sys.exit(1)
          PY
      - name: Installed evidence modules import
        working-directory: /tmp
        run: /tmp/wheel-venv/bin/python -c "import agentmem_ref.portable_evidence"
      - name: Installed console command
        working-directory: /tmp
        run: /tmp/wheel-venv/bin/agent-memory --help
```

The first smoke exits 0 only when `validate` reached schema evaluation from a directory that is not the repo; a `FileNotFoundError`, a foreign `ValueError`, or a silent pass each exit 1, so the step cannot pass while the defect it guards against is present.

`.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /reference
    schedule:
      interval: weekly
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    groups:
      actions:
        patterns: ["*"]
```

`README.md:18`: `[![Conformance](https://img.shields.io/badge/Conformance-Levels%201--6%20Defined-7c3aed)](docs/06-conformance-test-plan.md)`.

`docs/CONFIGURATION.md`: insert `agent-memory discover` after line 318 (`agent-memory config validate`); line 326 disclaimer unchanged.

Stale "Proposed" sites, nine, each with its exact replacement (ADR-020, ADR-022, ADR-035 headers carry `Accepted` with no date; ADR-030 and ADR-031 carry `Accepted: 2026-08-13`):

| Site | Current text (fragment) | Replacement |
|---|---|---|
| `docs/future/multi-agent-shared-memory-protocol.md:5` | "reconciliation with **Proposed ADR-022**, not promotion of this future subsystem and not acceptance of ADR-022" | "reconciliation with **ADR-022 (Accepted)**, not promotion of this future subsystem" |
| `docs/profiles/policy-projection-compatibility-profile.md:3` | "ADR-030 remains Proposed until its executable evidence gates pass." | "ADR-030 is Accepted (2026-08-13)." |
| `docs/profiles/temporal-commitment-evidence-profile.md:3` | "ADR-031 remains Proposed until final exact-head evidence passes." | "ADR-031 is Accepted (2026-08-13)." |
| `docs/programs/runtime-evidence/cognitive-mesh.md:3` | "reference slice implemented; ADR-035 remains Proposed" | "reference slice implemented; ADR-035 is Accepted" |
| `docs/programs/runtime-evidence/cognitive-mesh.md:190` | "ADR-035 remains **Proposed** until its full acceptance boundary is reviewed against repository-wide doctrine and evidence." | "ADR-035 is **Accepted**; the bounded evidence satisfying its acceptance requirements is recorded in `adr-035-acceptance-matrix.md`." |
| `docs/programs/runtime-evidence/evolveai-cognitive-mesh.md:3` | "implementation/evidence slice under validation; ADR-035 remains Proposed" | "implementation/evidence slice under validation; ADR-035 is Accepted" |
| `wiki-src/Runtime-Evidence.md:73` | "**ADR-020 remains Proposed.** P4 executes a substantial deletion-completeness evidence bar, but the ADR's independent acceptance process governs its status." | "**ADR-020 is Accepted.** P4 executes a substantial deletion-completeness evidence bar." |
| `wiki-src/Runtime-Evidence.md:75` | "**ADR-022 remains Proposed.** Isolation-domain implementation issue #68 remains open, so a finalized isolation-domain diagram would outrun the contract and its critical fixtures." | "**ADR-022 is Accepted.** Isolation-domain evidence is recorded under `docs/audits/isolation/` (issue #68 gap reconciliation)." |
| `wiki-src/Canonical-and-Derived-State.md:123` | final sentence "ADR-020 remains Proposed: it has further validation items, and clearing one bar is not acceptance." | final sentence "ADR-020 is now Accepted; clearing this one bar was one of its validation items, not the whole acceptance." |

Sites that correctly say "remains Proposed" and are NOT edited: `wiki-src/Runtime-Evidence.md:74` and `wiki-src/Home.md:186,189` (ADR-021, ADR-029 are Proposed), `docs/adr/README.md` (canonical index), and `docs/audits/governed-uncertainty/*` (dated audit snapshots).

Same-class stale sites explicitly DEFERRED to Sprint 9 (documentation reconciliation, GAP-DOC-04/05 pass), because each sits inside doctrine prose whose surrounding paragraphs also need rework rather than a one-sentence swap: `docs/07-integration-roadmap.md:383` and `wiki-src/Conformance-and-Evidence.md:101` (ADR-020 "should remain Proposed until"), `docs/13-system-composition-boundaries.md:65`, `docs/01-layer-model.md:17`, `docs/11-component-architecture.md:21` (ADR-035 "until accepted" / "Proposed by"), and `docs/research/temporal-policy-semantic-mediation.md:400` ("Proposed ADR-030"). GAP-DOC-09 therefore closes only for the nine sites in the table; the six deferred sites are recorded against GAP-DOC-09 in `docs/RESEARCH_BRIEF.md` at seal time.

### Unit Tests

- CI job `wheel-install` in `cli-doctor.yml` is the empirical test for Phase 1's packaging (D4 below).
- `python scripts/validate_markdown_links.py README.md docs/CONFIGURATION.md docs/future/multi-agent-shared-memory-protocol.md docs/profiles/policy-projection-compatibility-profile.md docs/profiles/temporal-commitment-evidence-profile.md docs/programs/runtime-evidence/cognitive-mesh.md docs/programs/runtime-evidence/evolveai-cognitive-mesh.md` and `python scripts/validate_wiki_links.py` confirm the edited links resolve.

## Feature Inventory Touches

| entry_id | operation | test_path | test_descriptor |
|---|---|---|---|
| FX001 | NEW | `.github/workflows/cli-doctor.yml` (job `wheel-install`) | Installed wheel resolves canonical schemas: `receipts.validate('decision-receipt.schema.json', {})` raises a schema `ValueError`, not `FileNotFoundError`, from outside the repo; `agent-memory --help` exits 0 |
| FX002 | NEW | `reference/tests/test_receipts_schema_location.py` | With `receipts._SOURCE_SCHEMAS` and `receipts._packaged_schemas` patched, `schema_dir()` returns the source tree when present, the packaged dir when only it exists, and raises `FileNotFoundError` with an install hint when neither exists; `validate` loads a schema through `schema_dir()` |
| FX003 | NEW | `reference/tests/test_cedar_policy_comparator.py::test_policy_digest_is_eol_independent` | `policy_sha256` yields the same digest for LF and CRLF copies of the policy, so the pin holds on any checkout |

FEATURE_INDEX.md has zero entries at genesis, so every touch is NEW; `/qor-implement` Step 12.5 appends these three rows.

## Definition of Done

### Deliverable: wheel-safe receipts loader

- **D1**: An installed `agent-memory-reference` wheel can validate governance receipts without the source checkout (RESEARCH_BRIEF GAP-RT-01 hot slice).
- **D2**: `agentmem_ref.receipts.schema_dir() -> pathlib.Path`; `_validator` reads through it; `setup.py` `build_py` override; `[tool.setuptools.package-data] agentmem_ref = ["_schemas/*.json"]`.
- **D3**: `docs/ARCHITECTURE_PLAN.md` Dependencies table corrected; `FEATURE_INDEX.md` rows FX001, FX002; ledger entry at seal.
- **D4**: `test_receipts_schema_location.py` four tests pass; CI job `wheel-install` prints "schema resolved from wheel" and `agent-memory --help` exits 0.

### Deliverable: declared runtime dependencies

- **D1**: `pip install .` yields an importable package for the 17 evidence modules (GAP-ARCH-03).
- **D2**: `pyproject.toml` `dependencies` lists jsonschema, cryptography, rfc8785 with bounds; `optional-dependencies.comparators` lists the two comparator pins.
- **D3**: `docs/ARCHITECTURE_PLAN.md` row change; CONTRIBUTING unchanged (requirements-file path still valid).
- **D4**: the `wheel-install` job step "Installed evidence modules import" (`/tmp/wheel-venv/bin/python -c "import agentmem_ref.portable_evidence"`) exits 0.

### Deliverable: deterministic Cedar digest

- **D1**: Cedar policy pin verification is checkout-independent (GAP-RT-02).
- **D2**: `policy_sha256` normalizes CRLF; `.gitattributes` present.
- **D3**: none beyond FEATURE_INDEX FX003.
- **D4**: `test_policy_digest_is_eol_independent` and `test_policy_digest_is_pinned` both pass on a Windows checkout with `core.autocrlf=true`.

### Deliverable: environment-tolerant pin tests

- **D1**: The suite is green on any environment whose comparator packages are absent or at another version (GAP-RT-03).
- **D2**: `reference/tests/pin_support.py` with `installed_version` and `pinned`; two `skipUnless` decorators.
- **D3**: none.
- **D4**: `test_pin_support.py` two tests pass; with `agent-manifest` 0.1.0a1 installed, `test_pinned_release_and_repository_identity_are_explicit` reports skipped, not failed.

### Deliverable: dependency update automation

- **D1**: Version-update PRs flow for pip and actions (GAP-CI-05).
- **D2**: `.github/dependabot.yml` as specified.
- **D3**: none.
- **D4.d**: GitHub evaluates the file server-side; no local test can exercise it. **Follow-up phase**: Sprint 8 release and operations confirms the first Dependabot PR appears.

### Deliverable: documentation truth

- **D1**: README badge no longer implies an achieved conformance level; the nine stale "Proposed" mentions in the site table are corrected and the six deferred sites are recorded against GAP-DOC-09 for Sprint 9; CONFIGURATION sketch lists `discover` (GAP-DOC-01, GAP-DOC-09 partial, GAP-DOC-13).
- **D2**: the edits enumerated in Phase 3.
- **D3**: none.
- **D4.d**: prose changes; link validators confirm resolvability. **Follow-up phase**: Sprint 9 documentation reconciliation covers the broader index gaps.

## CI Commands

- `python -m unittest discover -s reference/tests -t reference` — full reference suite including the new tests
- `python scripts/validate_schemas.py` — schemas unchanged and still valid
- `python scripts/validate_fixtures.py fixtures` — fixtures unchanged
- `python -m build --outdir dist .` — sdist and wheel build; the wheel contains `_schemas/*.json` and the build fails if none were copied
- `python scripts/validate_markdown_links.py README.md docs/CONFIGURATION.md docs/future/multi-agent-shared-memory-protocol.md docs/profiles/policy-projection-compatibility-profile.md docs/profiles/temporal-commitment-evidence-profile.md docs/programs/runtime-evidence/cognitive-mesh.md docs/programs/runtime-evidence/evolveai-cognitive-mesh.md` — edited docs link-clean
- `python scripts/validate_wiki_links.py` — wiki edits link-clean
