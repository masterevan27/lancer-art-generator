# Agent instructions

## Dashboard

Dashboard project ID: lancer-art-generator

Use the scoped dashboard check-in endpoint GET http://127.0.0.1:5080/api/checkin?project=lancer-art-generator for project context and POST http://127.0.0.1:5080/api/checkin/lancer-art-generator/events for project-scoped updates.

## Before starting project work

Before starting work in this project, check the dashboard for project-scoped human notes, active work, blockers, and additional instructions. After work, record completed, blocked, planned, test, and documentation findings through the dashboard API or CLI. Never edit materialized state files directly.

## Dashboard updates

When work in this repository is completed, blocked, planned, tested, or found
to have stale documentation, update the local AI agent dashboard. Start
`G:\GIT-REPOS\ai-agent-dashboard\server.js` if needed, then use its API or
CLI, for example:

```powershell
node G:\GIT-REPOS\ai-agent-dashboard\dashboard-cli.js add-note --project lancer-art-generator --note "Describe the change and remaining work"
```

Use unique event ids and never edit `ai-agent-dashboard/data/state.json` or
`events.jsonl` directly. The canonical protocol is in
`G:\GIT-REPOS\ai-agent-dashboard\data\README.md`.
