---
type: Runbook
title: Maintain the documentation bundle
description: Install the pinned OKF tools, validate the bundle and understand documentation coverage.
---
# Maintain the documentation bundle

Start at [the bundle index](index.md). This repository pins house profile 1.0.0
and OKF 0.2 in [.okf/tools/profile.json](../.okf/tools/profile.json);
[the profile](../.okf/tools/profile.md) describes metadata and evidence rules.
The project release version remains governed by [VERSIONING.md](VERSIONING.md).

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
