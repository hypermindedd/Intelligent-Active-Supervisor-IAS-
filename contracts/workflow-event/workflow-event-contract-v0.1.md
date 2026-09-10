# Smart Supervisor / IAS — Workflow & Event Contract v0.1

**Status:** FREEZE CANDIDATE — WS-01  
**Contract Version:** `0.1.0`  
**Workstream:** `WS-01`  
**Authoritative dependencies:** Project Instructions v4 (Canonical), Data Contract v0.1.0 (Canonical), IAS Control Plane v0.1  

## 1. Purpose and governing principles

This contract defines the MVP workflow boundaries, commands, events, producer/consumer relationships, sync/async boundaries, delivery semantics, retries, idempotency, failure handling, observability, mocks, fixtures, staging order and release gates for Smart Supervisor / IAS.

It does **not** redefine any Data Contract v0.1.0 entity, field meaning, enum, canonical owner or shared payload semantics. Transport metadata introduced here wraps the authoritative Data Contract and does not replace it.

1. AI interprets/proposes; deterministic business engines validate and mutate authoritative business state.
2. One canonical business-logic owner exists per state transition. n8n orchestrates; it is not an alternate owner of CRM, appointment, task, payment, message or audit truth.
3. Cross-module requested state changes are commands. Committed facts are events.
4. Cross-module events are asynchronous by default and delivered at least once.
5. Synchronous calls are allowed only when the caller cannot safely continue without the immediate result and the timeout/retry budget is bounded.
6. Every external journey propagates `clinic_id`, `correlation_id`, `causation_id` where applicable and compatible contract/schema versions.
7. Every state-changing command is idempotent.
8. Failures are explicit, classified, observable and recoverable; no silent loss.
9. Human review is a first-class workflow boundary.
10. Tenant isolation is revalidated by every canonical owner.

## 2. Transport envelopes

### 2.1 Event envelope

```json
{
  "event_id": "uuid",
  "event_type": "appointment.created.v1",
  "event_version": "1.0",
  "occurred_at": "2026-09-10T10:00:00Z",
  "recorded_at": "2026-09-10T10:00:02Z",
  "clinic_id": "uuid",
  "correlation_id": "uuid",
  "causation_id": "uuid-or-null",
  "actor": {
    "type": "user|system|ai_assisted|integration|customer",
    "id": "opaque-id-or-null",
    "on_behalf_of": "opaque-id-or-null"
  },
  "confidence": null,
  "source": {
    "workstream": "WS-05",
    "component": "appointment-engine",
    "version": "0.1.0"
  },
  "aggregate": {
    "type": "appointment",
    "id": "uuid-or-null"
  },
  "payload": {}
}
```

Rules:
- `event_id`: globally unique UUID generated once when the fact is committed to the outbox.
- `event_type`: lowercase dot-separated `<domain>.<fact>.v<major>`.
- `event_version`: semantic payload version. Breaking event changes create a new major event type/version.
- `occurred_at`: authoritative fact time in UTC.
- `recorded_at`: outbox/transport recording time in UTC.
- `clinic_id`: mandatory canonical tenant key for tenant-owned facts.
- `correlation_id`: stable across the end-to-end business journey.
- `causation_id`: ID of the command/event that directly caused this event; null only for a root fact.
- `actor`: machine-checkable origin category; it never replaces authorization checks.
- `confidence`: null for deterministic facts. AI-derived interpretation events carry overall confidence here and MUST preserve per-field confidence inside the payload.
- `source`: producer identity; never trusted as authorization evidence.
- `aggregate`: canonical entity affected where applicable.
- `payload`: immutable minimum fact data required by consumers.

### 2.2 Command envelope

```json
{
  "command_id": "uuid",
  "command_type": "appointment.create.v1",
  "command_version": "1.0",
  "requested_at": "2026-09-10T10:00:00Z",
  "clinic_id": "uuid",
  "correlation_id": "uuid",
  "causation_id": "uuid-or-null",
  "idempotency_key": "string",
  "requested_by": {
    "type": "user|system|integration|ai_assisted|customer",
    "id": "opaque-id-or-null"
  },
  "payload": {}
}
```

Rules:
- retries reuse the same `command_id`, `correlation_id` and `idempotency_key`;
- `idempotency_key` identifies intended business effect, not one network attempt;
- a command can be accepted, rejected or deferred for human review;
- timeout does not prove non-mutation: callers retry with the same idempotency key or query canonical state.

### 2.3 Reconciliation of `WDN-20260910-005`

The REQUIRED Warden specification is fully answered here. The proposed `tenant_id` is **not adopted** because Data Contract v0.1.0 makes `clinic_id` the canonical tenant key and already mandates cross-module propagation of `clinic_id`; adding a parallel tenant field would create conflicting tenant semantics. The requirement is therefore satisfied by mandatory `clinic_id`.

`actor`, `confidence`, `recorded_at` and `causation_id` are adopted. For AI extraction events, the payload preserves the Data Contract `crm_interpretation` confidence map including field-level confidence such as customer name, service and follow-up date.

The Warden proposal that every dead-letter create a follow-up is narrowed: every **business-impacting** terminal failure requiring human action creates/requests a canonical `MANUAL_REVIEW` task through the Follow-up Engine. Pure infrastructure incidents are routed to Reliability/Audit instead of polluting customer follow-up truth.

## 3. Command vs Event semantics

A **command** is an imperative request to a canonical owner and may be refused. Example: `follow_up.create.v1`.

An **event** is an immutable statement that a committed fact already occurred. A consumer may fail processing but does not reject the historical fact. Example: `follow_up.created.v1`.

No event name is used as a command. No consumer mutates another owner's canonical state by interpreting a non-owner event as authority.

## 4. Delivery, outbox, processed events and ordering

### 4.1 Delivery guarantees
- Cross-module events: **at-least-once**.
- Durable async commands: **at-least-once submission**, exactly-once business effect through owner-side idempotency.
- Sync read/resolve calls: request/response with bounded retries.
- Exactly-once network delivery is not claimed.

### 4.2 Event Outbox
A canonical owner that mutates authoritative state and emits an event MUST write the business mutation, audit evidence and `event_outbox` row in the same DB transaction where technically possible.

Outbox lifecycle uses only Data Contract states: `PENDING → PROCESSING → PUBLISHED`; exhausted publication becomes `FAILED`. A crash after send but before `PUBLISHED` may duplicate delivery; consumers must dedupe.

### 4.3 Processed Events
Every consumer records `(consumer_name, event_id)` in `processed_events` in the same transaction as its durable side effect where possible. Unique conflict means replay; return success/no-op and do not repeat the effect.

### 4.4 Ordering
No global ordering is guaranteed. Per-aggregate ordering is best-effort; consumers must tolerate out-of-order events. State-owning consumers always re-read/validate current canonical state before a transition. Stale events cannot overwrite newer canonical state.

## 5. Idempotency

Default command key form:
`v1:<clinic_id>:<command_type>:<business_anchor>:<action_fingerprint>`.

Generation rules:
- provider inbound action: `sha256(clinic_id|provider|provider_message_id|command_type)`;
- event-derived command: `sha256(consumer_name|source_event_id|command_type|stable_target_id)`;
- human/API command: client key preferred; otherwise `sha256(clinic_id|actor_id|command_type|normalized_business_fields)` with explicit dedupe window;
- scheduled scanner: `sha256(clinic_id|workflow_code|entity_id|logical_schedule_bucket|action)`.

Owner enforcement is mandatory before mutation. Duplicate submissions return original/equivalent outcome and MUST NOT repeat external side effects. Outbound messaging additionally dedupes against recipient/channel/content-or-template/cause/schedule-bucket so retries never send the same intended message twice.

## 6. Concurrency and race control

- Unique DB constraints defend provider identity, provider message and processed-event uniqueness.
- Mutable aggregate transitions use row lock or optimistic compare-and-set.
- Appointment slot conflict validation occurs inside the Appointment Engine critical section; callers never reserve by assumption.
- Due/overdue scanners use claim/lease semantics such as `FOR UPDATE SKIP LOCKED` or equivalent.
- Message send creates one durable provider-send action per idempotency key.
- Every entity reference is tenant-checked before mutation.

## 7. Failure taxonomy, retry, timeout and recovery

| Failure class | Examples | Auto-retry | Human | Lock |
|---|---|---:|---:|---|
| `TRANSIENT_EXTERNAL` | 429, network, provider 5xx | yes | after exhaustion | no |
| `TRANSIENT_DB` | deadlock, connection reset/failover | yes | after exhaustion | no |
| `TRANSIENT_QUEUE` | outbox/broker temporary unavailable | yes | after exhaustion | no |
| `PERMANENT_VALIDATION` | malformed schema, missing field, invalid enum | no | if recoverable input | no |
| `PERMANENT_BUSINESS` | illegal transition, inactive service, conflict | no | when business judgment needed | no |
| `SECURITY_TENANT` | clinic mismatch, unauthorized tenant reference | no | security review | `HUMAN_LOCK` if suspected breach |
| `SENSITIVE_POLICY` | clinical request, refund execution, sensitive action | no | mandatory | `HUMAN_LOCK` when authorization/policy unresolved |
| `AI_LOW_CONFIDENCE` | insufficient/contradictory extraction | no repeated AI loop by default | mandatory | no |
| `ARCHITECTURE_CONTRACT` | duplicate owner logic, loop, missing idempotency, contract drift | no | Debugger/Warden | `REVIEW/WARDEN_LOCK` as directed |
| `UNKNOWN` | uncategorized | one guarded retry max | then mandatory | REVIEW if recurring |

Default retry for retryable async actions: **5 total attempts maximum** (initial + 4 retries), exponential backoff with full jitter, `base=5s`, `cap=15m`; representative upper bounds 5s, 30s, 2m, 10m. `Retry-After` wins up to a one-hour ceiling.

Timeouts:
- internal sync read/resolve: connect 2s, total 5s, max 2 caller attempts;
- deterministic sync command: 10s total;
- AI/STT: 60s, one transient provider retry;
- messaging provider send: 15s request timeout; delivery receipts are async;
- reporting query/job unit: 30s before split/batch.

No unbounded retry, recursion or in-memory-only retry counters.

### Dead Letter / Failed Action architecture
v0.1 introduces no new Data Contract entity. Terminal state is represented by existing truths:
- `event_outbox.status=FAILED`;
- `messages.delivery_status=FAILED`;
- `ai_extractions.review_status=FAILED`;
- canonical owner failure statuses where defined;
- a `tasks.task_type=MANUAL_REVIEW` task when human recovery is required;
- append-only audit + structured operational error logs.

`OPS-02 Recover Failed Action` replays the original boundary after authorization/cause resolution with original correlation/idempotency. It never synthesizes new business intent or rewrites history.

## 8. Human-in-the-loop and lock boundary

Human review is mandatory for medical/clinical content, ambiguous consequential customer requests, insufficient AI confidence, sensitive outbound communications outside approved policy, refunds/exceptional financial actions, conflicting customer identity/merge candidates, suspicious tenant/security failures, and retry exhaustion requiring business judgment.

`HUMAN_LOCK` is required when safe continuation depends on unresolved human policy/authorization, a suspected privacy/tenant breach, refund authorization, or explicit Human Leadership control.

`WARDEN_LOCK/REVIEW` is required for shared architecture defects: contradictory ownership, duplicated mutation logic, self-triggering event loops, missing idempotency, contract-version incompatibility, direct AI business-state mutation, unenforceable rules, or production release without required staging evidence.

## 9. Architecture corrections to initial workflow inventory

1. `CORE-01 Customer Resolve` retained; Identity Resolution owner.
2. `CORE-02 Customer Upsert` retained for customer-record facts only.
3. `CORE-03 Add Interaction` retained as append-only Timeline owner operation.
4. **New `CORE-04 Apply Customer Lifecycle`** because CRM record ownership and Lead Lifecycle ownership must not be conflated.
5. `AI-01 Voice Intake` retained but limited to media/STT preparation; no CRM mutation.
6. `AI-02 CRM Extraction` retained as proposal-only AI extraction.
7. `CUS-01 Customer Inbound Router` retained as orchestration only.
8. `CUS-02 Receptionist Response` is restricted to **compose**; `MSG-01` owns transport.
9. Appointment create/confirm/reschedule/cancel/complete/no-show are merged into **`APT-01 Appointment Command Handler`** to prevent duplicated transition logic. Reminder becomes **`APT-02 Appointment Reminder Scheduler/Dispatcher`**.
10. Follow-up create/complete/cancel/reassign/reschedule are merged into **`FU-01 Follow-up Command Handler`**. `FU-02 Due Follow-up Scanner`, `FU-03 Overdue Escalation`, `FU-04 Lost Lead Recovery` remain policy/scanner workflows and call the owner rather than writing tasks directly.
11. `MSG-01 Send Message` retained as Messaging owner command handler.
12. `MGR-01 Daily Brief`, `MGR-02 Manager Query` retained as canonical read/report workflows only.
13. `PAY-01 Record Deposit` renamed **`PAY-01 Payment Record Command Handler`** so payment recording has one owner path; refund execution remains human-authorized.
14. `OPS-01 Global Error Handler`, `OPS-02 Recover Failed Action`, `OPS-03 Audit Logger` retained.
15. **New `OPS-04 Outbox Publisher`** because reliable event delivery is a separate canonical responsibility.

## 10. Workflow Boundary Matrix

| Code | Workflow | Canonical logic owner | Trigger | Boundary | Authoritative writes |
|---|---|---|---|---|---|
| CORE-01 | Customer Resolve | Identity Resolution | normalized inbound / lookup | SYNC | identity binding only when explicitly verified; normal resolve read-only |
| CORE-02 | Customer Upsert | CRM Core | validated command | SYNC + async event | customers; permitted CRM facts |
| CORE-03 | Add Interaction | Timeline Engine | append request | SYNC + async event | interactions; coordinated `last_contact_at` |
| CORE-04 | Apply Customer Lifecycle | Lead Lifecycle | lifecycle command | SYNC + async event | lifecycle/service-interest state |
| AI-01 | Voice Intake | Messaging/Voice Intake | voice message received | ASYNC | attachment transcription fields |
| AI-02 | CRM Extraction | AI Extraction | text/transcription | ASYNC | ai_extractions only |
| CUS-01 | Customer Inbound Router | Customer Reception orchestrator | accepted inbound event | ASYNC | none directly |
| CUS-02 | Receptionist Response Compose | Customer Reception | resolved inbound intent | SYNC/ASYNC compose | no canonical business state |
| APT-01 | Appointment Command Handler | Appointment Engine | appointment command | SYNC + async events | appointments |
| APT-02 | Reminder Scheduler/Dispatcher | Appointment + Messaging boundary | schedule/event | ASYNC | reminder state through Appointment owner; message through MSG-01 |
| FU-01 | Follow-up Command Handler | Follow-up Engine | follow-up command | SYNC + async events | tasks, derived next_follow_up_at |
| FU-02 | Due Follow-up Scanner | Follow-up Engine | schedule | ASYNC | claim/dispatch only; no alternate lifecycle |
| FU-03 | Overdue Escalation | Follow-up Engine | overdue scan | ASYNC | OVERDUE via canonical owner |
| FU-04 | Lost Lead Recovery | Lead Lifecycle + Follow-up boundary | eligibility scan | ASYNC | no direct task mutation; invokes FU-01 |
| MSG-01 | Send Message | Messaging Engine | send command | ASYNC preferred | messages |
| MGR-01 | Daily Brief | Reporting/Supervisor | schedule | ASYNC read job | no shadow CRM truth |
| MGR-02 | Manager Query | Reporting/Supervisor | manager request | SYNC read | none |
| PAY-01 | Payment Record Command Handler | Payment Engine Lite | authorized command | SYNC + async event | payments |
| OPS-01 | Global Error Handler | Reliability | workflow failure | ASYNC | error/audit evidence; requests human task when needed |
| OPS-02 | Recover Failed Action | Reliability + original owner | operator recovery | ASYNC | replay through owner only |
| OPS-03 | Audit Logger | Audit/Security | audit request | ASYNC helper | audit_logs |
| OPS-04 | Outbox Publisher | Event Layer | outbox claim | ASYNC | event_outbox status |

## 11. Complete Command Matrix

| Command | Producer(s) | Consumer/owner | Idempotency anchor | Output |
|---|---|---|---|---|
| `customer.resolve.v1` | WS-04/08/03 | CORE-01 / WS-02 | provider identity/phone fingerprint | resolved/not_found/ambiguous |
| `customer.upsert.v1` | WS-04; approved AI apply path | CORE-02 | source message/extraction + identity | customer result |
| `interaction.append.v1` | all business modules | CORE-03 | source cause + interaction type | interaction_id |
| `customer.lifecycle.apply.v1` | deterministic policy/approved apply | CORE-04 | cause + target stage | applied/rejected |
| `appointment.create.v1` | WS-04/manual | APT-01 | customer + slot + origin | appointment result |
| `appointment.confirm.v1` | WS-04/manual | APT-01 | appointment + cause | appointment result |
| `appointment.reschedule.v1` | WS-04/manual | APT-01 | appointment + new slot + cause | appointment result |
| `appointment.cancel.v1` | WS-04/manual | APT-01 | appointment + cause | appointment result |
| `appointment.mark_completed.v1` | staff/manual | APT-01 | appointment + action | result |
| `appointment.mark_no_show.v1` | staff/policy | APT-01 | appointment + action | result |
| `follow_up.create.v1` | WS-03 apply/04/05/FU-04 | FU-01 | customer + reason + due_at + cause | task result |
| `follow_up.complete.v1` | staff/WS-04 | FU-01 | task + action | task result |
| `follow_up.cancel.v1` | staff/policy | FU-01 | task + action | task result |
| `follow_up.reassign.v1` | staff/manager | FU-01 | task + assignee + cause | task result |
| `follow_up.reschedule.v1` | staff/customer request | FU-01 | task + due_at + cause | task result |
| `message.send.v1` | CUS-02/APT-02/FU/manual-approved | MSG-01 | recipient/channel/template-or-content/cause/bucket | queued message_id + delivery events |
| `payment.record.v1` | authorized staff/integration | PAY-01 | external_reference or business fingerprint | payment result |
| `failed_action.recover.v1` | operator | OPS-02 | original action id | accepted/rejected |
| `audit.append.v1` | non-transactional modules | OPS-03 | action + entity + cause | accepted |

Data Contract `appointment_command` and `follow_up_command` payload meanings are preserved exactly; the command envelope wraps them.

## 12. Complete Event Matrix / Producer-Consumer Matrix

| Event | Producer | Consumers | Minimum payload/fact |
|---|---|---|---|
| `message.received.v1` | WS-08 | WS-04, WS-03 when eligible, timeline path | message_id, channel, provider, provider_message_id, message_type |
| `message.queued.v1` | WS-08 | origin/observability | message_id, customer_id, channel |
| `message.sent.v1` | WS-08 | timeline/origin | message_id, sent_at |
| `message.delivered.v1` | WS-08 | reporting/timeline if configured | message_id, delivered_at/status |
| `message.failed.v1` | WS-08 | OPS-01, origin, reporting | message_id, failure_class/provider_code |
| `voice.transcribed.v1` | WS-03 | AI-02 | message_id, attachment_id, transcription ref/content per retention policy |
| `ai.extraction.proposed.v1` | WS-03 | WS-02/04/06 apply-router or human review | ai_extraction_id, schema/version, overall confidence, **per-field confidence map**, requires_human_review |
| `ai.extraction.review_required.v1` | WS-03 | human/manual-review path | ai_extraction_id, reason codes |
| `ai.extraction.failed.v1` | WS-03 | OPS-01, human review | source, failure class |
| `customer.resolved.v1` | WS-02 Identity | WS-04/03 | customer_id, resolution_method |
| `customer.created.v1` | WS-02 CRM | WS-04/07 | customer_id |
| `customer.updated.v1` | WS-02 CRM | WS-07/scoped consumers | customer_id, changed_fields |
| `customer.lifecycle_changed.v1` | WS-02 Lead Lifecycle | WS-06/07/04 | customer_id, from_stage, to_stage |
| `interaction.appended.v1` | WS-02 Timeline | WS-07/06 where relevant | interaction_id, customer_id, type, occurred_at |
| `appointment.created.v1` | WS-05 | WS-06/07/04/timeline | appointment_id, customer_id, status, schedule |
| `appointment.confirmed.v1` | WS-05 | WS-06/07/04/timeline | appointment_id, confirmation_status |
| `appointment.rescheduled.v1` | WS-05 | WS-06/07/04/APT-02/timeline | appointment_id, old/new schedule |
| `appointment.cancelled.v1` | WS-05 | WS-06/07/04/APT-02/timeline | appointment_id, reason |
| `appointment.completed.v1` | WS-05 | WS-06/07/02 lifecycle/timeline | appointment_id, customer_id |
| `appointment.no_show.v1` | WS-05 | WS-06/07/timeline | appointment_id, customer_id |
| `appointment.reminder_due.v1` | WS-05 | APT-02 | appointment_id, customer_id, due_at |
| `appointment.reminder_sent.v1` | WS-05 after messaging fact | WS-07/timeline | appointment_id, message_id |
| `appointment.reminder_failed.v1` | WS-05 | OPS-01/07/human | appointment_id, failure |
| `follow_up.created.v1` | WS-06 | WS-07/04/timeline | task_id, customer_id, due_at, priority |
| `follow_up.completed.v1` | WS-06 | WS-07/02 lifecycle/timeline | task_id, customer_id, result |
| `follow_up.rescheduled.v1` | WS-06 | WS-07/04/timeline | task_id, old/new due_at |
| `follow_up.cancelled.v1` | WS-06 | WS-07/04/timeline | task_id, reason |
| `follow_up.overdue.v1` | WS-06 | WS-07/escalation/timeline | task_id, customer_id, overdue_since |
| `lost_lead.identified.v1` | WS-06 deterministic scanner | FU-01/WS-07 | customer_id, evidence/reason |
| `payment.recorded.v1` | Payment Engine Lite | WS-07/timeline/WS-05 if linked | payment_id, customer_id, type, amount, currency, status |
| `audit.recorded.v1` | WS-09 | compliance/observability | audit_log_id, action, entity refs |

Event-loop guards:
- `interaction.appended.v1` cannot cause the originating module to append the same source interaction again;
- reporting facts never trigger business mutation;
- reminder due → message send → message result may update reminder state once, but never schedules another reminder;
- lost-lead identification creates at most one equivalent recovery task per policy window;
- delivery events never re-request the same send.

## 13. Sync / Async Matrix

| Boundary | Mode | Reason |
|---|---|---|
| provider webhook → normalized inbound acceptance | sync ACK + async business processing | fast provider ACK + durability |
| router → Customer Resolve | SYNC | routing cannot safely continue without identity result |
| router/AI apply → Customer Upsert | SYNC | caller needs canonical customer id/outcome |
| module → Append Interaction | SYNC preferred | timeline evidence should be durable with command success |
| caller → Appointment Handler | SYNC | immediate validation/slot result; facts propagate async |
| caller → Follow-up Handler | SYNC | immediate deterministic result; facts async |
| compose/reminder/follow-up → Send Message | ASYNC | provider latency must not hold business transaction |
| voice → STT → AI extraction | ASYNC | external compute/retry latency |
| canonical owner → event consumers | ASYNC | decoupling/parallel development |
| Manager Query | SYNC read | interactive read-only query |
| Daily Brief | ASYNC scheduled | aggregation job |
| error/recovery/outbox | ASYNC | durable operational handling |

## 14. Workflow specification and state rules

### CORE-01 Customer Resolve
Input: `clinic_id`, provider/external identity, optional phone. Exact verified provider identity wins; phone may yield candidates but ambiguity returns `AMBIGUOUS`, never auto-merge. Cross-tenant lookup is prohibited. Acceptance: same identity resolves one customer; second channel only after verified binding; cross-clinic attempt returns no data. DB transient errors retry bounded; conflicting identity becomes human review.

### CORE-02 Customer Upsert
Validates tenant/fields and mutates customer-record facts only. Lifecycle changes go through CORE-04. AI proposals cannot bypass validation. DB transaction writes customer + audit + outbox. Duplicate idempotency never creates a duplicate customer action.

### CORE-03 Add Interaction
Validates clinic/customer, channel/type/direction and appends only. Corrections are new interactions. Duplicate source/cause key creates one timeline fact. Timeline updates `last_contact_at` only under documented eligible-contact rules.

### CORE-04 Apply Customer Lifecycle
Applies only Data Contract lifecycle enums and only legal transitions justified by canonical facts. AI suggestion alone is insufficient. Legal v0.1 transitions:
- `NEW → QUALIFIED|CONSIDERING|BOOKED|DORMANT|LOST`
- `QUALIFIED → CONSIDERING|BOOKED|DORMANT|LOST`
- `CONSIDERING → QUALIFIED|BOOKED|DORMANT|LOST`
- `BOOKED → ACTIVE_CUSTOMER|CONSIDERING|DORMANT|LOST`
- `ACTIVE_CUSTOMER → BOOKED|DORMANT`
- `DORMANT → CONSIDERING|BOOKED|ACTIVE_CUSTOMER|LOST`
- `LOST → CONSIDERING|QUALIFIED|BOOKED` on reactivation.
Other transitions require shared review/change.

### AI-01 Voice Intake
Retrieves/transcribes voice attachments only. No CRM mutation. One transcription effect per source attachment. STT transient error retries once; permanent/intelligible failure routes to extraction failure/human review.

### AI-02 CRM Extraction
Persists `ai_extractions` only and emits proposal/review events. It preserves Data Contract `crm_interpretation` and per-field confidence. Uncertain values remain null. Low confidence, contradictory facts, medical/sensitive content or policy-required review cannot auto-apply.

### CUS-01 Customer Inbound Router
Consumes accepted inbound messages, resolves customer, requests timeline append, routes voice/text and invokes only canonical owner commands. Duplicate provider webhook causes at most one business effect.

### CUS-02 Receptionist Response Compose
Reads approved tenant-scoped `knowledge_items` and service facts. It may compose/AI-assist but does not mutate business truth or message delivery state. It must not diagnose, recommend treatment or invent price/service facts. Sensitive/medical/ambiguous/low-confidence response moves to human review. Auto-send, where policy permits, is executed only through MSG-01.

### APT-01 Appointment Command Handler
Validates clinic/customer/service/provider tenant match, start/end validity, legal state and slot availability inside the owner transaction. Appointment Engine alone changes appointment state.

Legal v0.1 normal transitions:
- create → `TENTATIVE` or `CONFIRMED` per validated policy;
- `TENTATIVE → CONFIRMED|CANCELLED`;
- `CONFIRMED → COMPLETED|CANCELLED|NO_SHOW`;
- reschedule changes schedule fields while retaining a valid non-terminal state and appending audit/timeline evidence;
- `COMPLETED|CANCELLED|NO_SHOW` are terminal in normal operations.
Confirmation status remains distinct from appointment status. Concurrent slot requests must deterministically allow at most one conflicting reservation.

### APT-02 Appointment Reminder Scheduler/Dispatcher
Scans eligible appointments, claims one reminder per policy bucket, requests async message send, and updates `reminder_status` only through Appointment ownership after message facts. Reminder send never implies confirmation. Exhausted send failure produces `FAILED` and human/business recovery where required.

### FU-01 Follow-up Command Handler
Follow-up Engine alone owns task lifecycle. Legal normal transitions:
- `OPEN → DONE|CANCELLED|OVERDUE`;
- `OVERDUE → DONE|CANCELLED`;
- explicit RESCHEDULE of an overdue task may update due time and return to `OPEN` under owner policy;
- `DONE|CANCELLED` terminal in normal operations.
`OVERDUE` is a system transition, not a user command. `customers.next_follow_up_at` remains derived convenience only.

### FU-02 Due Follow-up Scanner
Periodic scanner (default production target every 5 minutes, configurable) claims due work with lease semantics and never invents business outcomes. Parallel scanners must not double-dispatch.

### FU-03 Overdue Escalation
Moves eligible OPEN tasks to OVERDUE exactly once through the owner and emits timeline/audit/event evidence. Manager escalation is policy-driven and idempotent.

### FU-04 Lost Lead Recovery
Deterministically reads canonical lifecycle/interactions/interests/appointments/tasks; no separate lost-lead truth. It creates recovery follow-up via FU-01 only and suppresses duplicate/equivalent open tasks or ineligible/sensitive contacts.

### MSG-01 Send Message
Messaging Engine owns transport truth. Validates tenant/channel/recipient/content policy and creates one provider send per idempotency key. Returns queued/message_id and later sent/delivered/failed facts. 429/5xx/network errors auto-retry bounded; invalid recipient or permanent provider rejection is terminal. Sensitive outbound content requires human policy.

### MGR-01 Daily Brief
Read-only canonical aggregation scheduled in clinic local timezone and executed in UTC. No shadow CRM state. Partial-source failures must mark the brief incomplete rather than fabricate zero.

### MGR-02 Manager Query
Authenticated, role/tenant-scoped, read-only. AI may summarize retrieved facts but cannot mutate. Cross-clinic queries are denied.

### PAY-01 Payment Record Command Handler
Records Data Contract payment facts after tenant/customer/appointment/amount/currency/type/status validation. Refund **execution** is never automatic and requires human authorization; the table may record final authorized state.

### OPS-01 / OPS-02 / OPS-03 / OPS-04
- OPS-01 classifies and surfaces failure; it does not mutate another owner's state.
- OPS-02 replays authorized failed actions through original owner boundaries with original idempotency/correlation.
- OPS-03 is append-only audit helper; transactional owner-side audit is preferred where possible.
- OPS-04 publishes outbox facts, marks publication state and alerts/retries boundedly; it never changes payload semantics.

## 15. Structured Observability Contract

Every workflow log includes where applicable:
`timestamp`, `severity`, `environment`, `workflow_code`, `workflow_version`, `workstream`, pseudonymous `clinic_id`, `correlation_id`, `causation_id`, `event_id`, `command_id`, `idempotency_key_hash`, `aggregate_type`, `aggregate_id`, `attempt`, `failure_class`, `error_code`, `duration_ms`, `outcome`.

Never log credentials, tokens, raw clinical content or unnecessary PII. Raw message/content logging requires an explicitly secured sink and retention policy.

Minimum metrics:
- command accept/reject/defer counts;
- event publication latency and failed outbox count;
- consumer replay/duplicate count;
- workflow success/failure/timeout rate;
- retries and exhaustion;
- human-review queue size/age;
- message send/delivery/failure rate;
- AI extraction success/review/failure and confidence distribution;
- appointment conflicts/rejections;
- follow-up overdue/completion;
- cross-tenant/security rejections;
- p50/p95/p99 synchronous latency.

`correlation_id` is the trace key; `causation_id` reconstructs why an action happened.

## 16. Tenant/Security expectations at workflow boundaries

Every consumer independently validates `clinic_id`; no module trusts upstream tenant scope. Referenced IDs must belong to the same clinic. DB should use RLS/equivalent defense in depth. Webhook authenticity is verified before normalized acceptance. Credentials are environment-local and never appear in payloads.

Under active Warden repository-visibility constraint, all committed fixtures are synthetic: no credentials, live webhook URLs, tenant identifiers from real systems, clinic datasets, customer records or commercial pricing artifacts.

## 17. Mock Contracts and Test Fixtures

Each workflow publishes contract-compliant synthetic fixtures under `contracts/workflow-event/fixtures/` or an equivalent reviewed shared fixture path.

Required fixture inventory:
1. new customer with phone;
2. new customer without name;
3. existing customer same channel;
4. same customer second channel;
5. duplicate provider message;
6. ambiguous voice requiring review;
7. clear voice with follow-up date;
8. appointment create + confirm;
9. appointment reschedule;
10. appointment cancel;
11. no-show;
12. follow-up completed on time;
13. follow-up overdue;
14. lost-lead candidate;
15. message provider failure;
16. AI extraction failure;
17. DB write failure;
18. cross-clinic access attempt;
19. event replay;
20. out-of-order appointment fact;
21. concurrent appointment slot requests;
22. outbox crash-after-send replay;
23. exhausted retry → human review;
24. medical/sensitive inbound escalation;
25. refund-record request requiring human authorization.

Blocked downstream workstreams may prepare mocks/fixtures against this contract but may not treat that as release authorization.

## 18. Acceptance Test Matrix

| Workflow | Required acceptance evidence |
|---|---|
| CORE-01 | exact resolve, not found, ambiguous, cross-tenant rejection |
| CORE-02 | create/update, replay, lifecycle ownership preserved |
| CORE-03 | append-once, correction append, replay suppression |
| CORE-04 | legal/illegal transition, AI cannot bypass validation |
| AI-01 | one transcription/source, retry then failure path |
| AI-02 | clear proposal, per-field confidence, low-confidence review, malformed output rejection |
| CUS-01 | one route per inbound provider message |
| CUS-02 | approved response, clinical escalation, zero direct state mutation |
| APT-01 | create/confirm/reschedule/cancel/complete/no-show + race conflict |
| APT-02 | one reminder/bucket + success/failure evidence |
| FU-01 | create/complete/cancel/reassign/reschedule + replay |
| FU-02 | due selection + parallel scanner dedupe |
| FU-03 | one overdue transition/event |
| FU-04 | one recovery task + equivalent-open-task suppression |
| MSG-01 | queued→sent/delivered, provider failure, duplicate send suppression |
| MGR-01 | aggregate reconciliation, timezone, partial-data disclosure |
| MGR-02 | authorized read, cross-tenant denial, no writes |
| PAY-01 | valid record, duplicate suppression, refund authorization boundary |
| OPS-01 | correct taxonomy + bounded retry/human escalation |
| OPS-02 | same-idempotency replay + unauthorized recovery denial |
| OPS-03 | append-only audit + sensitive-data minimization |
| OPS-04 | publish/replay/dedupe + exhausted outbox failure |

## 19. Failure Test Matrix

Every applicable workflow tests malformed input, missing tenant, cross-tenant reference, dependency timeout, transient DB error, permanent validation error, duplicate/replay and observability completeness.

Additional required failures:
- AI: timeout, invalid schema/JSON, invented uncertain fact, low confidence, sensitive/medical content;
- Messaging: 429, 5xx, invalid recipient, duplicate send, delivery-webhook replay;
- Appointment: double-booking race, stale reschedule, terminal-state mutation, duplicate reminder;
- Follow-up: scanner race, duplicate lost-lead candidate, stale completion, overdue replay;
- Event layer: crash publish-before-mark, consumer crash side-effect-before-processed-marker, out-of-order event, poison event, retry exhaustion;
- Security: forged webhook, unauthorized manager query, Clinic A entity inside Clinic B command/event.

Failure test passes only when canonical state stays consistent, failure is observable, retries are bounded and required human/lock path occurs.

## 20. Dependency Graph

```text
WS-00 Control Plane/Governance
  └─ WS-01 Workflow & Event Contract
      ├─ WS-02 CRM Core & Identity
      ├─ WS-03 AI Voice & Extraction
      ├─ WS-08 Messaging & Channels
      ├─ WS-09 Security/Audit/Reliability
      ├─ WS-10 QA/Integration/Debugger
      ├─ WS-05 Appointment Engine ─┐
      └─ WS-06 Follow-up Engine ──┼─> WS-07 Manager/Supervisor
              WS-02 ──────────────┘
      WS-02 + WS-08 ─> WS-04 Customer Reception

WS-11 Pilot & Metrics depends on WS-02..WS-10 integration evidence.
```

Proposed future WS-12/13/14 from Warden are not authoritative until Human Leadership approves their codes/names. This contract does not create them.

## 21. Parallel Development Matrix and execution surface

| Workstream | Contract-ready after freeze | Mock prep while blocked | Release now | Target execution after valid unlock |
|---|---:|---:|---:|---|
| WS-02 CRM/Identity | yes | yes | NO | `CODEX` + `N8N` adapters |
| WS-03 AI Voice/Extraction | yes | yes | NO | `WORK` → `N8N/CODEX` |
| WS-04 Customer Reception | contract mocks yes; live depends WS-02+08 | yes | NO | `N8N` + `CODEX` |
| WS-05 Appointment | yes | yes | NO | `CODEX` + `N8N` |
| WS-06 Follow-up/Lost Lead | yes | yes | NO | `CODEX` + `N8N` |
| WS-07 Manager/Reporting | mocks yes; live data depends WS-02+06 | yes | NO | `WORK` + `CODEX/N8N` |
| WS-08 Messaging | yes | yes | NO | `N8N` + `CODEX` |
| WS-09 Security/Audit/Reliability | yes | yes | NO | `CODEX` + `WORK` |
| WS-10 QA/Integration | yes | yes | NO | `CODEX` + `WORK` |
| WS-11 Pilot/Metrics | no, integrated evidence needed | fixture planning only | NO | `WORK` + `MANUAL` |

## 22. n8n Naming / Version / Export / Import Standard

Workflow name:
`IAS.<ENV>.<WORKSTREAM>.<CODE>.<Name>.v<major>_<minor>`

Examples:
- `IAS.DEV.WS08.MSG01.SendMessage.v1_0`
- `IAS.STG.WS05.APT01.AppointmentCommandHandler.v1_0`

Node names are stable intent labels: `10 Validate Envelope`, `20 Resolve Tenant Context`, `30 Call Owner`, `90 Handle Error`.

Rules:
- no secret/account identifiers in names;
- committed export JSON must be sanitized of credentials/live endpoints;
- credential IDs are environment-local; use documented logical names;
- each export/manifest records contract version, workflow version, workstream and compatible command/event versions;
- independent dev accounts may diverge internally, but Git-exported artifact is imported to shared staging before production;
- no routine direct production editing; emergency human-authorized change must be exported back, reconciled and versioned;
- breaking interface change increments major version; compatible internal corrections do not change contract semantics.

## 23. Staging Integration Order

1. WS-09 event/audit/idempotency skeleton + OPS-04 outbox harness.
2. WS-02 Identity/CRM/Timeline/Lifecycle owners.
3. WS-08 inbound normalization + outbound provider sandbox.
4. WS-03 Voice/AI proposal path on synthetic fixtures.
5. WS-05 Appointment + reminder interaction.
6. WS-06 Follow-up/overdue/lost-lead.
7. WS-04 Customer Reception orchestration across dependencies.
8. WS-07 Manager reads/daily brief.
9. WS-10 full integration: replay, race, failure, tenant isolation and recovery.
10. WS-11 controlled pilot only after production gates.

No stage assumes all consumers exist; events can be tested against contract fixture sinks.

## 24. Production Release Gates

Production requires all of:
- workstream gate authorizes release;
- no active HUMAN_LOCK/WARDEN_LOCK applies;
- contract compatibility tests pass;
- acceptance and failure suites pass in shared staging;
- tenant isolation/security tests pass;
- idempotency/replay/race tests pass;
- no unbounded retry;
- outbox/processed-events evidence passes;
- structured metrics/logging/correlation evidence exists;
- rollback/export artifact exists;
- no secrets/customer data in repo artifacts;
- provider sandbox/staging test precedes live credentials;
- Human approval exists for sensitive/refund/production communication policies where required;
- current IAS Governance Gate and repository-protection requirements satisfy active Warden/Control Plane directives.

For the current single-GitHub-identity condition, `WDN-20260910-006` requires PR rule visibility with **0 required approvals**, Code Owner review OFF, strict required `governance` status check, no bypass, deletion/force-push blocked. This is WS-00 work and does not alter business contract semantics.

## 25. Contract Versioning / Compatibility

v0.1.0 permits only compatible additions after review and fixture update. Breaking changes include event/command rename/removal, payload meaning/type change, ownership transfer, delivery or idempotency semantic change, state-machine change, or security-boundary change.

Breaking changes require impact analysis, contract increment, migration/compatibility plan, dual-read/dual-publish where practical, affected-workstream review, staging evidence, Orchestrator approval and Warden/Human review when applicable.

Consumers publish supported versions. Producers do not stop old major versions until required consumers migrate or a coordinated cutover is approved.

## 26. Active Debugger Pre-Freeze Review

Reviewed against mandatory defect classes:
- contradictory ownership — resolved by canonical owner table;
- duplicated business logic — appointment/task transitions centralized;
- event loops — explicit loop guards;
- missing failure paths — taxonomy/retry/dead-letter/recovery defined;
- inconsistent state mutation — owner-only mutations;
- race conditions — lock/CAS/lease and appointment critical section;
- missing idempotency — command keys + processed_events;
- insufficient auditability — actor/correlation/causation/audit/observability;
- unbounded retry — hard attempt limits;
- cross-tenant risk — repeated owner-side tenant validation;
- direct AI mutation — prohibited; AI writes only extraction proposal truth;
- unenforceable rules — acceptance/failure/release gates make obligations testable.

No unresolved WS-01 architecture defect remains from this checklist. The separate open WS-00 security finding and Warden global release lock remain active and are not falsely resolved by this contract.

## 27. Frozen boundaries vs deferred configuration

**Frozen when this candidate is merged to the authoritative branch:**
- event/command envelopes and naming;
- event/command catalogues;
- producer/consumer ownership;
- sync/async boundaries;
- workflow boundary/owner rules;
- legal state-transition constraints defined here;
- idempotency generation/enforcement;
- at-least-once delivery;
- ordering/replay/duplicate handling;
- retry/timeout/backoff/max attempts;
- failure/dead-letter/recovery architecture;
- outbox/processed-events semantics;
- race/concurrency controls;
- human/lock boundaries;
- observability fields/metrics/correlation;
- n8n naming/versioning/export rules;
- fixtures, acceptance/failure obligations;
- staging order and production gates.

**Deferred without changing shared semantics:** provider-specific APIs, exact DB/queue technology, AI/STT vendor/model, clinic-specific reminder timing, lost-lead eligibility thresholds, numeric AI confidence thresholds, customer-facing web API design, commercial/GTM workstreams, and any Data Contract change.

## 28. Orchestrator effect after freeze

This contract makes WS-02, WS-03, WS-05, WS-06, WS-08, WS-09 and WS-10 **contract-ready** for parallel implementation; WS-04 and WS-07 are ready for contract mocks but retain implementation dependencies; WS-11 remains integration-dependent.

However `WDN-20260910-001` is a BLOCKING Warden directive on **release of any BLOCKED workstream**. Therefore WS-02..WS-11 must remain `BLOCKED` until Gate Hardening v0.2, the required three negative tests and a Warden UNLOCK referencing that directive exist. Mock/fixture preparation is permitted only as non-release preparation.

Correct control action after freeze:
1. mark WS-01 complete/frozen through the Control Plane after merge evidence;
2. record downstream contract-readiness evidence;
3. keep WS-02..WS-11 BLOCKED;
4. do not issue BLOCKED→GO/WORK transition yet;
5. after valid Warden unlock, Orchestrator may release eligible workstreams according to this contract and dependency graph.
