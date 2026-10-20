---
type: Runbook
title: Maintain the documentation bundle
description: Install the pinned OKF tools, validate the bundle and understand documentation coverage.
status: stable
tags:
  - documentation
sources:
  - id: okf-profile
    resource: ../.okf/tools/profile.md
    title: House documentation profile
  - id: okf-lock
    resource: ../.okf/tools/profile.json
    title: Pinned profile and specification revision
  - id: okf-config
    resource: ../.okf.json
    title: Bundle configuration
  - id: okf-external-catalog
    resource: ../.okf/external-docs.json
    title: Catalog of documents outside the bundle
  - id: okf-external-check
    resource: ../.okf/check-external.mjs
    title: Supplemental external-document checker
  - id: okf-workflow
    resource: ../.github/workflows/okf.yml
    title: Documentation CI workflow
  - id: okf-spec
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/0b87c52c6ef999286c745e19998fdfcd03d5dbee/SPEC.md
    title: Open Knowledge Format v0.2 specification
generated:
  by: claude-code/claude-opus-5-5
  at: 2026-10-20T05:04:51Z
stale_after: 2027-01-18T00:00:00Z
---
# Maintain the documentation bundle

Start at [the bundle index](index.md). This repository pins house profile 1.1.0
and OKF 0.2 in [.okf/tools/profile.json](../.okf/tools/profile.json);
[the profile](../.okf/tools/profile.md) describes metadata and evidence rules.
The project release version remains governed by [VERSIONING.md](VERSIONING.md).
Profile 1.1.0 warns when a concept lacks `generated` or a runbook lacks
`sources` or `stale_after`; warnings keep the check passing, but treat them
as review work.

From the repository root, with Node 20.19 or newer:

```sh
npm ci --prefix .okf/tools --ignore-scripts --no-audit --no-fund
node .okf/tools/cli.mjs index .
node .okf/tools/cli.mjs check .
node .okf/check-external.mjs
```

The dedicated documentation workflow installs the locked dependencies and runs
the same checker. Refresh generated indexes after changing metadata; preserve
handwritten navigation. Tool upgrades are deliberate reviewed snapshots.

The checker covers Markdown inside docs/, its required indexes and local links.
The catalog below retains first-party documents at their existing paths; added
metadata and links outside docs/ are checked by the supplemental command and
CI, using the explicit .okf/external-docs.json catalog. README and AGENTS entry
points retain their own format. Skill files,
generated content, third-party material and application input formats are outside
this bundle. No legacy-document or missing-link exceptions are configured.

Metadata and link validation do not constitute factual or human review. Existing
status prose, dates, acceptance gaps and historical plans are preserved. Dashboard
task state and roadmap progress remain authoritative; no roadmap delivery is
claimed by this conversion.

CI uses `actions/checkout@v7`, `actions/setup-node@v7` and Node 24.

## Metadata conventions

Every concept carries `status`, `tags` and `generated`, in addition to the
required keys. Only record what evidence supports.

- `status`: `draft` while a design or plan is still under review, `stable`
  otherwise, `deprecated` once replaced (link the replacement). It never records
  whether the described work shipped; prose `Status:` lines in the body and
  the dashboard carry implementation state.
- `tags`: choose from `3d-models`, `animation`, `backgrounds`, `comfyui`,
  `documentation`, `expressions`, `gui`, `npc`, `prompts`, `spaceships`,
  `traits` and `versioning`. Extend this list here before using a new tag.
- `generated`: `by` names the agent that wrote the current content, using
  `codex/unrecorded` when the producer version was not recorded,
  `claude-code/<model-id>` when a commit trailer names the model, or
  `human:masterevan27` for hand-written content. `at` is the last meaningful
  content change; metadata-only edits do not move it.
- `sources`: runbooks and references cite the scripts, prompt tables and
  ComfyUI workflows they describe as GitHub URLs pinned to the commit the
  content was written against. When the cited file changes in the same commit
  as the document, use a relative path instead, because that commit does not
  exist yet. Refresh pins when the content is next revised. Historical plans
  and designs rely on their links instead.
- `stale_after`: runbooks, this guide and VERSIONING use 90 days after
  `generated.at`; dependency references use 180 days. Historical plans,
  designs and render notes have none. When the deadline passes, check the
  content against its sources, then revise or verify it before moving the date.
- `verified`: add `{ by: human:masterevan27, at: ... }` only after the owner
  actually reviewed the content, or an agent entry only after an agent checked
  it against its sources. The 2026-10-20 metadata backfill recorded no
  verification.

## Documents retained outside the bundle

- [README.md](../README.md) — Repository or component entry point retains its README format.
- [REMAINING-WORK.md](../REMAINING-WORK.md) — Metadata added; retained at its established path.

## Preserved input and instruction formats

- [AGENTS.md](../AGENTS.md) — Agent or skill instructions retain their own format.
- [prompts/background-generator-tables.md](../prompts/background-generator-tables.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [prompts/battlemap-art-prompts.md](../prompts/battlemap-art-prompts.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [prompts/city-background-art-prompts.md](../prompts/city-background-art-prompts.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [prompts/equipment-art-prompts.md](../prompts/equipment-art-prompts.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [prompts/expression-tables.md](../prompts/expression-tables.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [prompts/mech-catalogue-art-prompts.md](../prompts/mech-catalogue-art-prompts.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [prompts/npc-generator-tables.md](../prompts/npc-generator-tables.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [prompts/scene-and-spaceship-tables.md](../prompts/scene-and-spaceship-tables.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [prompts/scene-background-art-prompts.md](../prompts/scene-background-art-prompts.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [prompts/spaceship-generator-tables.md](../prompts/spaceship-generator-tables.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [test/fixtures/expression-groups.md](../test/fixtures/expression-groups.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [test/fixtures/expression-tables.md](../test/fixtures/expression-tables.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [test/fixtures/ship-tables-minimal.md](../test/fixtures/ship-tables-minimal.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [test/fixtures/tables-groups.md](../test/fixtures/tables-groups.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [test/fixtures/tables-minimal.md](../test/fixtures/tables-minimal.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
- [test/fixtures/tables-themed.md](../test/fixtures/tables-themed.md) — Application-consumed Markdown or parser fixture; existing input format is preserved.
