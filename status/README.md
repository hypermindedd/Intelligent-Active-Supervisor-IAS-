# IAS Cross-Account Worker Status

`status/` is the publication surface for parallel chats/accounts/workers.

## Critical distinction

Status files are **reports, not authority**. A worker may report that it believes it is ready, blocked, or complete, but it cannot change its executable gate here. Only the authoritative Control Plane under `control/` can grant `GO`, `WORK`, `REVIEW`, locks, or `DONE`.

## One file per workstream

Each workstream publishes to `status/WS-XX.json`. This prevents multiple accounts from constantly editing one shared file and reduces merge conflicts.

Every material milestone, pause, chat closure, handoff, blocker, failed test, or contract-impacting discovery must update the relevant status file.

## Required fields

```json
{
  "schema_version": "0.1.0",
  "workstream": "WS-XX",
  "reported_at": "ISO-8601",
  "reporter": {"account":"...","worker":"..."},
  "claimed_progress": 0,
  "observed_gate": "GO|WORK|REVIEW|HUMAN_LOCK|WARDEN_LOCK|BLOCKED|DONE",
  "execution_mode": "CHAT|WORK|N8N|CODEX|MANUAL",
  "contract_versions": [],
  "deliverables": [],
  "tests": [],
  "blockers": [],
  "open_decisions": [],
  "next_action": "...",
  "refs": []
}
```

The IAS Orchestrator validates reported progress against accepted deliverables/tests and decides the authoritative progress/gate separately.
