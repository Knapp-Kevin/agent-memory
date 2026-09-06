# Agent Memory Wiki source

This directory is the canonical source set for the reader-facing GitHub Wiki.

The Wiki is intentionally a navigation and explanation layer, not a second doctrine tree. Technical authority remains in `docs/`, `schemas/`, `fixtures/`, and `docs/adr/`.

## Design rules

- prefer concise reader-oriented pages over copying repository documents
- use progressive disclosure and role-based navigation
- avoid Mermaid on Wiki presentation surfaces
- use stable repository-native graphics where they materially help comprehension
- link every material doctrine summary back to the canonical repository source
- do not create Wiki-only doctrine
- preserve source-rights and authorship boundaries

## Publication

GitHub stores Wiki content in a separate Git repository:

```text
https://github.com/MythologIQ-Labs-LLC/agent-memory.wiki.git
```

Publication is automated. [`.github/workflows/publish-wiki.yml`](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/.github/workflows/publish-wiki.yml) validates this tree and republishes it whenever `wiki-src/**` changes on `main`, and can also be run on demand through workflow dispatch. It treats `wiki-src` as canonical: the published pages are replaced from the validated source rather than merged into, so an edit made directly in the GitHub Wiki UI will be overwritten on the next publish. Edit the source here instead.

`README.md` is deliberately excluded from publication. It documents the source tree and is not a reader-facing page. Every other `*.md` file in this directory becomes a Wiki page, so adding a page means adding a file here, a sidebar entry, and an inventory line below.

Manual publication remains possible from any git-capable environment, which matters because some connectors expose no Wiki write operations at all:

```bash
git clone https://github.com/MythologIQ-Labs-LLC/agent-memory.wiki.git
cp wiki-src/*.md agent-memory.wiki/
cd agent-memory.wiki
git add .
git commit -m "Publish Agent Memory Wiki"
git push origin master
```

If GitHub initializes the Wiki repository with a different default branch, push to that branch instead.

## Validation

Run the Wiki-link validator before publishing:

```bash
python scripts/validate_wiki_links.py wiki-src
```

The validator understands GitHub Wiki extensionless page links such as `[PAMA](PAMA)` and verifies that a corresponding `PAMA.md` source page exists.

## Page inventory

- `Home.md`
- `Getting-Started.md`
- `Core-Concepts.md`
- `PAMA.md`
- `Lifecycle-and-Forgetting.md`
- `Canonical-and-Derived-State.md`
- `Governed-Uncertainty.md`
- `Governance-Projection.md`
- `Temporal-Memory-Architecture.md`
- `Cryptographic-Temporal-Commitments.md`
- `Temporal-Policy-and-Governed-Memory.md`
- `Security-and-Privacy.md`
- `Conformance-and-Evidence.md`
- `Runtime-Evidence.md`
- `Research-and-Sources.md`
- `Implementation-Guide.md`
- `Configuration-and-Profiles.md`
- `Architecture-Decisions.md`
- `Aligned-Projects-and-Intellectual-Lineage.md`
- `Quality-Peers-and-Useful-Projects.md`
- `Decision-Flows-and-Memory-Lifecycle.md`
- `Contributing.md`
- `Glossary.md`
- `_Sidebar.md`
- `_Footer.md`
