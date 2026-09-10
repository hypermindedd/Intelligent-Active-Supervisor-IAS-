# IAS Control Plane Baseline — 2026-09-10

Type: `PHASE_GATE`
Timezone: Asia/Tehran
Overall project progress: **8%**

## Accepted foundation

- Smart Supervisor project instructions established.
- Data Contract v0.1.0 established as shared data foundation.
- IAS Control Plane v0.1 created.
- GitHub workstream registry, locks registry and orchestration order created.
- IAS Governance Gate GitHub Action created.
- Human Command Bus and Warden Command Bus created.
- Notion IAS command center created with Workstreams, Control Orders, Reports, Warden Directives and Debugger Findings.
- 2-hour change orchestrator scheduled.
- Daily 12:00 Tehran command report scheduled.
- Hourly Active Debugger scheduled.

## Current workstream gates

| Workstream | Progress | Gate | Mode |
|---|---:|---|---|
| WS-00 Control Plane & Governance | 85% | REVIEW | CHAT |
| WS-01 Workflow & Event Contract | 0% | GO | CHAT |
| WS-02 CRM Core & Identity | 0% | BLOCKED | WORK |
| WS-03 AI Voice & Extraction | 0% | BLOCKED | WORK |
| WS-04 Customer Reception | 0% | BLOCKED | WORK |
| WS-05 Appointment Engine | 0% | BLOCKED | WORK |
| WS-06 Follow-up & Lost Leads | 0% | BLOCKED | WORK |
| WS-07 Manager/Supervisor/Reporting | 0% | BLOCKED | WORK |
| WS-08 Messaging/Channels | 0% | BLOCKED | WORK |
| WS-09 Security/Audit/Reliability | 0% | BLOCKED | WORK |
| WS-10 QA/Integration/Debugger | 0% | BLOCKED | WORK |
| WS-11 Pilot & Metrics | 0% | BLOCKED | WORK |

## P0 priorities

1. Complete and freeze Workflow & Event Contract v0.1 (WS-01).
2. Enable GitHub `main` branch protection and require `IAS Governance Gate` before merge.
3. Ensure Warden/Claude has an actual shared channel identity/access path and starts writing directives to the Warden Command Bus or Notion Warden Directives.
4. Promote current project instructions and Data Contract into GitHub `/contracts` as canonical full files.

## Active limitations

- Warden is not discoverable as a Notion workspace user through the connected Notion account, so direct Notion sharing/invitation cannot be completed from the current tool surface.
- No dedicated ChatGPT project chat can be programmatically created from this control plane. A `Reports` project chat must be created manually, then bootstrapped from the shared control plane.
- Logical/CI lock enforcement exists, but repository-level prevention is incomplete until `main` branch protection requires PRs and the IAS Governance Gate status check.

## Current orchestration order

`ORD-20260910-001`: proceed with WS-01. WS-02 through WS-11 remain BLOCKED until Workflow & Event Contract v0.1 is frozen or an explicit scoped unlock is issued.
