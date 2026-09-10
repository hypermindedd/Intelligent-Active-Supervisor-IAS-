# IAS — Intelligent Active Supervisor

This repository is the executable source of truth for the Smart Supervisor / IAS project.

## Operating model

- **GitHub** = versioned contracts, workstream gates, locks, directives, code/workflow exports, CI and integration evidence.
- **Notion** = command center, executive reporting, Warden review surface, debugger findings and human decisions.
- **Chats / accounts / agents** = workers. They are not allowed to invent local project truth.

## Mandatory worker bootstrap

Before any worker starts or resumes work it must:

1. Read `control/workstreams.json`.
2. Resolve its workstream by code/path.
3. Read `control/locks.json` and active orders.
4. Read the relevant files under `contracts/`.
5. Obey the current `gate` and `execution_mode`.
6. If the gate is `HUMAN_LOCK`, `WARDEN_LOCK`, `BLOCKED`, or `DONE`, stop implementation.
7. If the gate is `WORK`, use the long-form Work execution path rather than an ordinary implementation chat.
8. Report material progress/change back to the shared control plane.

## Gate states

- `GO` — proceed within approved contract boundary.
- `WORK` — proceed, but execution belongs in a long-running Work workflow.
- `REVIEW` — no new scope; review/validation only.
- `HUMAN_LOCK` — stop until explicit human unlock directive.
- `WARDEN_LOCK` — stop until explicit Warden unlock directive.
- `BLOCKED` — stop until dependency is resolved.
- `DONE` — frozen/complete; changes require reopening by control order.

## Repository structure

- `contracts/` — authoritative shared contracts.
- `control/` — orchestration state, locks and orders.
- `warden/` — Warden/Claude handoff protocol.
- `debugger/` — Active Debugger protocol and findings.
- `reports/` — change and daily reports mirrored from Notion.
- `scripts/` — governance and validation tooling.
- `.github/workflows/` — enforcement checks.

Direct pushes to `main` should be avoided. Use workstream branches and PRs so governance checks can run before integration.
