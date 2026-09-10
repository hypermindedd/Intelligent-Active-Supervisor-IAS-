# IAS Warden Gateway

Warden/Claude is an independent review authority for architecture, contracts, execution quality and risk detection.

## Communication model

The project does not treat unrecorded external conversations as authoritative. Warden review becomes actionable only when the directive is written to a shared surface:

1. GitHub Warden Command Bus issue/comment, or
2. Notion `IAS — Warden Directives` database.

The IAS Orchestrator consumes new directives, reconciles them against human decisions and current contracts, then updates workstream gates and lock state.

## Warden directive format

```text
WARDEN-DIRECTIVE
id: WDN-YYYYMMDD-NNN
workstream: WS-XX | GLOBAL
severity: INFO | ADVISORY | REQUIRED | BLOCKING
action: COMMENT | REWORK | LOCK | UNLOCK | ESCALATE_HUMAN
contract_version: <version or N/A>
reason: <concise evidence-backed reason>
directive: <imperative required action>
evidence: <GitHub/Notion refs>
```

## Lock rules

- `BLOCKING + LOCK` creates/maintains `WARDEN_LOCK`.
- A Warden unlock must reference the exact Warden lock or superseded directive.
- Human Leadership can override a Warden lock explicitly. Such override must remain in the audit trail.
- If a Warden directive conflicts with an explicit human product/business decision, Orchestrator sets `HUMAN_LOCK` and requests human resolution instead of choosing silently.

## Review package Warden should receive

- Current project instructions
- Current Data Contract
- Current Workflow/Event Contract
- Current `control/workstreams.json`
- Current `control/locks.json`
- Open PRs and failing CI
- Latest IAS report
- Open Debugger findings

## Outputs expected from Warden

Warden should distinguish:
- observations,
- recommendations,
- required corrective actions,
- blocking issues,
- explicit unlocks.

Only the last three can change an execution gate.
