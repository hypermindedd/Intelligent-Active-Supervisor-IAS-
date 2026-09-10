# WS-01 — WDN-20260910-007 Reconciliation

**Status:** NORMATIVE ADDENDUM TO Workflow & Event Contract v0.1.0 freeze candidate  
**Directive:** `WDN-20260910-007`  
**Scope:** Corrections C1-C3 only; no Data Contract semantic changes.

This addendum is normative for the v0.1.0 freeze candidate and supersedes any conflicting readiness/deferred-ownership wording in Sections 27 and 28 of `workflow-event-contract-v0.1.md`. It must be folded into the canonical contract text in a later editorial-only revision; until then consumers MUST read the contract and this addendum together.

## C1 — Fixture freeze semantics

The following are frozen as contract semantics: the **25-scenario fixture inventory, fixture obligations, synthetic-data constraint, expected canonical effects, event/command semantics, and acceptance/failure intent**.

Fixture artefacts are considered delivered only when the corresponding files exist on the authoritative branch. PR #8 now carries the 25 synthetic fixture files plus `fixtures/index.json`; this does not make them authoritative until merge.

`WS-01` MUST NOT be marked `DONE` merely because the contract document merges. Completion requires verification that the contract, this reconciliation, and all 25 fixture artefacts are present on the authoritative branch and satisfy the governance gate.

## C2 — Downstream readiness semantics

`contract-ready`, `mock-ready`, and `authorized` are separate states:

- **Contract-ready:** the applicable boundary, schema, owner, command/event semantics and failure rules are frozen on the authoritative branch.
- **Mock-ready:** the applicable synthetic fixture artefacts are also present on the authoritative branch and can be used as shared behavioral oracles.
- **Authorized:** the IAS Control Plane gate explicitly permits execution (`GO`/`WORK`) and no applicable lock blocks it.

Until the contract plus all 25 fixture artefacts are merged, no downstream workstream may claim mock-readiness. After they are merged, downstream workstreams may be technically contract/mock-ready, but `WDN-20260910-001` still prohibits any `BLOCKED → GO/WORK` release until Gate Hardening v0.2, all required negative tests, and an explicit Warden UNLOCK referencing that directive exist.

Readiness is evidence; it is never authorization.

## C3 — Canonical owners and logical configuration surfaces

### AI confidence thresholds

- **Canonical policy owner:** `WS-03 — AI Voice & CRM Extraction`, specifically the AI Extraction Engine policy boundary.
- **Single logical configuration surface:** `AI Confidence Policy`, resolved by `clinic_id` plus extraction schema/use-case.
- **Deferred:** numeric values, storage technology and clinic-specific tuning.
- **Not deferred:** ownership, semantics, precedence and consumer behavior.
- Consumers MUST NOT invent local confidence thresholds. They consume the owner-produced confidence/review decision or call the canonical policy interface.
- Human-required boundaries (medical/clinical, refund/exceptional financial, explicit sensitive policy) override numeric confidence; high confidence never bypasses mandatory human review.

### Lost-lead eligibility thresholds

- **Canonical policy owner:** `WS-06 — Follow-up & Lost Lead Engine`, specifically `FU-04 Lost Lead Recovery` policy boundary.
- **Single logical configuration surface:** `Lost Lead Eligibility Policy`, resolved by `clinic_id` and approved recovery policy context.
- **Deferred:** numeric inactivity windows/threshold values, storage technology and clinic-specific tuning.
- **Not deferred:** ownership, eligibility semantics and duplicate/suppression behavior.
- Other modules may supply canonical facts but MUST NOT compute or persist an independent lost-lead eligibility truth.

These two logical configuration surfaces are **interfaces/configuration ownership**, not new Data Contract entities or tables. If a shared persistent configuration entity becomes necessary, it requires Data Contract review/versioning before introduction.

## Warden proposal disposition

The Warden's earlier proposals for a parallel `tenant_id` and blanket dead-letter-to-follow-up behavior are withdrawn in `WDN-20260910-007`. The contract's existing decisions remain authoritative candidates:

- canonical tenant key remains `clinic_id` from Data Contract v0.1.0;
- only business-impacting terminal failures requiring human action create/request `MANUAL_REVIEW`; pure infrastructure failures remain Reliability/Audit concerns.

## Completion condition

This addendum resolves C1-C3 at the contract level. `WS-01` remains `GO` and not `DONE` until authoritative-branch merge/verification of the contract + reconciliation + 25 fixtures. No downstream gate changes are authorized by this addendum.