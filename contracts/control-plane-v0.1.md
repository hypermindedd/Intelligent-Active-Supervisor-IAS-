# IAS Control Plane Contract v0.1

Status: ACTIVE FOUNDATION CONTRACT

## Purpose

Prevent parallel chats, accounts, agents, n8n instances and developers from moving the project in incompatible directions. The contract is executable governance, not only documentation.

## Shared authorities

1. **Human Leadership** — final business and strategic authority; may override all lower authorities explicitly.
2. **Warden** — independent architecture/risk reviewer; may issue REQUIRED/BLOCKING directives within delegated scope.
3. **IAS Orchestrator** — maintains cross-workstream state, dependencies, priorities, execution modes and gates.
4. **IAS Active Debugger** — detects evidence-backed defects and may issue corrective REVIEW/BLOCK orders within approved contracts.
5. **Worker** — executes only inside its approved boundary and current gate.

## Gate state machine

- `GO`: proceed inside approved scope.
- `WORK`: proceed using long-form Work execution.
- `REVIEW`: validation/correction only; no scope expansion.
- `HUMAN_LOCK`: stop until explicit Human unlock.
- `WARDEN_LOCK`: stop until explicit Warden unlock, unless Human Leadership explicitly overrides.
- `BLOCKED`: stop until dependency/evidence is resolved and a GO order is recorded.
- `DONE`: frozen; reopen requires REWORK/GO order.

No elapsed time, new chat, commit, worker suggestion or implicit assumption releases a lock.

## Execution mode

Every active workstream declares one of:

- `CHAT`: architecture, decisions, contract work, scoped discussion.
- `WORK`: substantial multi-step execution requiring persistent work context/computer/browser/tool use.
- `N8N`: workflow implementation/export/integration.
- `CODEX`: repository code implementation/refactor/testing.
- `MANUAL`: human-only action such as account/permission/branch-protection settings.

The Orchestrator may move a workstream between modes through a Control Order.

## Cross-account preflight

Every worker must read, in order:

1. current `control/workstreams.json`
2. current `control/locks.json`
3. Human and Warden command buses / current control orders
4. relevant contracts
5. latest relevant Debugger findings

Copied chat context never overrides fresher control-plane state.

## Enforcement

`IAS Governance Gate` evaluates changed paths against the gate state stored in the PR base branch. This intentionally prevents a worker from changing its own gate to GO in the same work PR.

Full repository enforcement additionally requires `main` branch protection with required PR and required IAS Governance Gate status check.

## Contract changes

Shared contract changes require versioned review. Any change to ownership boundaries, states, payload meanings, events, security policy or cross-module interfaces cannot be introduced locally by a worker.

## Warden protocol

Warden/Claude directives are authoritative only when recorded in the GitHub Warden Command Bus or Notion `IAS — Warden Directives`. External/unrecorded conversations are context, not execution state.

## Debugger protocol

When evidence is sufficient, Debugger output is imperative: identify evidence, required action, verification and resulting gate. A fix requiring new product/business policy or shared-contract redesign is escalated instead of silently implemented.

## Reporting

- 2H change review: only when meaningful change exists.
- Daily command report: 12:00 Asia/Tehran.
- Active Debugger check: hourly, only surfaces new actionable defects.

Reports must state per-workstream progress, gates, active locks, priorities, Warden directives, Debugger findings, human decisions, dependencies, next phase and required execution mode.
