# IAS Control Plane

This directory is the authoritative execution-control layer for every IAS worker, chat, account, agent and automation.

## Required preflight

Before starting or resuming implementation, a worker MUST:

1. Read `workstreams.json`.
2. Locate its workstream and current `gate`.
3. Read `locks.json`.
4. Read the Human and Warden command buses for newer directives.
5. Read relevant shared contracts.
6. Obey the most recent valid directive according to authority and lock rules.

## Enforcement semantics

- `GO`: implementation is allowed within the approved contract/path boundary.
- `WORK`: implementation is allowed but should be executed through ChatGPT Work/long-form execution, not an ordinary planning chat.
- `REVIEW`: review, test and correction only; no scope expansion.
- `HUMAN_LOCK`: implementation must stop. Only an explicit Human `UNLOCK` referencing the lock ID can release it.
- `WARDEN_LOCK`: implementation must stop. Only an explicit Warden `UNLOCK` referencing the lock ID can release it, unless Human Leadership explicitly overrides.
- `BLOCKED`: implementation must stop until the named dependency/evidence is resolved and a GO order is recorded.
- `DONE`: frozen. Any change requires an explicit reopen/rework order.

## Authority precedence

1. Human Leadership explicit directive
2. Valid blocking Warden directive within delegated review authority
3. IAS Orchestrator order
4. IAS Active Debugger corrective order
5. Worker-local judgment

Human Leadership may override any lower authority. Warden directives that conflict with explicit human business decisions must be escalated to `HUMAN_LOCK` rather than silently applied.

## No implicit unlock

A new commit, chat message, suggestion or elapsed time never unlocks a workstream. Unlock must be explicit, attributable and auditable.

## Control Order format

```json
{
  "order_id": "ORD-YYYYMMDD-NNN",
  "authority": "HUMAN|WARDEN|ORCHESTRATOR|DEBUGGER",
  "action": "GO|LOCK_HUMAN|LOCK_WARDEN|BLOCK|UNLOCK|MOVE_TO_WORK|RETURN_TO_CHAT|STOP|REWORK",
  "workstream": "WS-XX",
  "issued_at": "ISO-8601",
  "directive": "imperative instruction",
  "evidence": ["refs"],
  "supersedes": null
}
```

## Chat closure

When a chat reaches a boundary that requires a new chat, it must close with a complete handoff, exact next-chat name, copy/paste prompt, open risks, contract versions and current gate. The next chat must run preflight again rather than trusting copied context alone.
