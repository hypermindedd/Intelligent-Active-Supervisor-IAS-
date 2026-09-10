# IAS Shared Contracts

Shared contracts are authoritative across every chat, account, developer, n8n instance, agent and environment.

## Current authoritative contract set

1. `project-instructions-v4-canonical.md` — canonical runtime project rules, including chat handoff, modularity, Control Plane, locks, Orchestrator, Warden, Active Debugger, reporting, cross-account status publication and GitHub enforcement.
2. `data-contract-v0.1-canonical.md` — canonical Data Contract v0.1.0.
3. `control-plane-v0.1.md` — executable governance/authority/gate protocol.
4. Workflow & Event Contract v0.1 — **pending under WS-01 and currently the next foundation gate**.

The long-form Project Instructions v4 and Data Contract v0.1 files are also retained in the project handoff/download bundle. Runtime workers should use the canonical files above for preflight and consult long-form artifacts when deeper context is required.

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

Until the Workflow & Event Contract is frozen, implementation workstreams WS-02 through WS-11 remain blocked unless an explicit scoped unlock is issued through the IAS Control Plane.
