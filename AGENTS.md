# Agent instructions

## Dashboard

Dashboard project ID: lancer-art-generator

Use the shared `DASHBOARD_BASE_URL` for dashboard requests: GET `DASHBOARD_BASE_URL/api/checkin?project=lancer-art-generator` for project context and POST `DASHBOARD_BASE_URL/api/checkin/lancer-art-generator/events` for project-scoped updates.

## Before starting project work

Before starting work in this project, check the dashboard for project-scoped human notes, active work, blockers, and additional instructions. After work, record completed, blocked, planned, test, and documentation findings through the dashboard API or CLI. Never edit materialized state files directly.

## Dashboard updates

When work in this repository is completed, blocked, planned, tested, or found
to have stale documentation, update the AI agent dashboard through the shared
`DASHBOARD_BASE_URL` configuration. Do not start a local server automatically;
if the URL is unavailable, report the exact request and tell the user how to
run the dashboard manually. Use its API or CLI, for example:

```powershell
node G:\GIT-REPOS\ai-agent-dashboard\dashboard-cli.js add-note --project lancer-art-generator --note "Describe the change and remaining work"
```

Use unique event ids and never edit `ai-agent-dashboard/data/state.json` or
`events.jsonl` directly. The canonical protocol is in
`G:\GIT-REPOS\ai-agent-dashboard\data\README.md`.
## Release versioning

Read [`docs/VERSIONING.md`](docs/VERSIONING.md) before completing project work.
It identifies the machine-readable version source and any project-specific
release automation.
