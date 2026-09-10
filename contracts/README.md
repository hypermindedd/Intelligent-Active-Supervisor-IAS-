# IAS Shared Contracts

Shared contracts are authoritative across every chat, account, developer, n8n instance, agent and environment.

## Current contract set

- Project Instructions: Smart Supervisor Project Instructions v3 (current project-source baseline; Control Plane additions are being promoted into the next version).
- Data Contract: Smart Supervisor Data Contract v0.1.0.
- Workflow & Event Contract: pending — WS-01, current next foundation step.

## Contract rule

No workstream may locally rename, reinterpret, add, remove or change shared entities, statuses, event meanings, payload semantics, ownership boundaries or cross-module interfaces.

Any breaking change requires:

1. Change request with evidence.
2. Impact analysis.
3. Shared contract version increment.
4. Migration/compatibility plan.
5. Orchestrator review.
6. Warden review when architecture/integration risk is material.
7. Human approval when product/scope/sensitive policy changes.
8. Staging integration verification.

Until the Workflow & Event Contract is frozen, implementation workstreams remain blocked by the Control Plane unless explicitly unlocked for mock-only development.
