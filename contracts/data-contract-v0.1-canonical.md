# Smart Supervisor / IAS — Data Contract v0.1.0 (Canonical)

Status: **AUTHORITATIVE SHARED DATA FOUNDATION**

No workstream may locally redefine the entities, IDs, state meanings, canonical ownership, or cross-module payload semantics in this contract.

## 1. Scope
MVP data contract supports: Automatic Lead Capture, Voice CRM, Customer Timeline, Appointment Management, Follow-up Engine, Lost Lead Recovery, Management Daily Brief, payment/deposit lite, messaging, AI extraction traceability, audit, idempotency, and reliable cross-module integration.

Explicitly outside MVP data scope: diagnosis, AI treatment recommendations, prescribing, detailed medical record, full accounting/payroll, full inventory ledger, unnecessary identity documents, and unbounded raw-audio retention.

## 2. Global principles
- Multi-tenant from day one: all tenant-owned business records carry `clinic_id`.
- One canonical owner/source of truth per business concept.
- AI interprets/proposes; deterministic business engines validate and mutate authoritative state.
- Timeline is append-first and auditable.
- Idempotency is mandatory for messages/events/actions.
- Internal IDs are opaque UUIDs.
- Store timestamps as UTC (`TIMESTAMPTZ`); clinic timezone is for display/scheduling interpretation.
- Enums are shared-contract controlled.
- Minimize PII; administrative CRM is not a medical record.
- Breaking changes require contract version increment and migration/compatibility plan.

## 3. Naming/type conventions
- Tables: plural `snake_case`
- Fields/JSON: `snake_case`
- PK: `id` UUID
- Tenant key: `clinic_id` UUID
- Time: `TIMESTAMPTZ` UTC
- Money: integer canonical amount + ISO `currency_code`
- Phone: normalized E.164 where possible
- Provider IDs: string/text, never internal PK
- Payloads carry `schema_version`
- Mutable business tables where applicable: `id`, `clinic_id`, `created_at`, `updated_at`, `created_by_type`, `created_by_id`
- `created_by_type`: `user`, `system`, `ai_assisted`, `integration`

## 4. `clinics`
Fields: `id`, `name`, `timezone` (IANA), `default_currency_code`, `status`, `created_at`, `updated_at`.
Status: `ACTIVE`, `SUSPENDED`, `ARCHIVED`.
Owner: Platform / CRM Core.

## 5. `staff_members`
Fields: `id`, `clinic_id`, `display_name`, `role`, optional `phone_e164`, optional `email`, `is_active`, optional `external_user_ref`, `created_at`, `updated_at`, optional `deleted_at`.
Roles: `OWNER`, `MANAGER`, `RECEPTIONIST`, `PROVIDER`, `OPERATOR`, `ADMIN`.
Owner: Identity / Permission.

## 6. `customers`
Lead and customer are ONE entity. Lifecycle expresses journey stage.
Fields: `id`, `clinic_id`, optional `display_name`, optional `primary_phone_e164`, `lifecycle_stage`, optional `assigned_staff_id`, optional `lead_source_id`, optional `preferred_channel`, optional `last_contact_at`, optional `next_follow_up_at`, optional `notes_summary`, `created_at`, `updated_at`, optional `deleted_at`.
Lifecycle: `NEW`, `QUALIFIED`, `CONSIDERING`, `BOOKED`, `ACTIVE_CUSTOMER`, `DORMANT`, `LOST`.
Rules: name/phone may be missing at first contact; `last_contact_at` is maintained by Timeline/CRM Core; `next_follow_up_at` is denormalized convenience only—`tasks` is follow-up truth; lifecycle changes must be auditable.
Owner: CRM Core / Lead Lifecycle.

## 7. `customer_identities`
Purpose: channel identity resolution and deduplication.
Fields: `id`, `clinic_id`, `customer_id`, `channel`, `provider`, `external_identity`, optional `phone_e164`, `is_verified`, `created_at`, `updated_at`.
Unique: `(clinic_id, provider, external_identity)`.
Owner: Identity Resolution Engine.

## 8. `lead_sources`
Fields: `id`, `clinic_id`, `name`, `code`, `is_active`.
Examples: `INSTAGRAM`, `WHATSAPP`, `REFERRAL`, `WALK_IN`, `PHONE`, `WEBSITE`.
Owner: CRM Core.

## 9. `services`
Fields: `id`, `clinic_id`, `name`, optional `category`, optional approved `description`, optional `price_min_amount`, optional `price_max_amount`, optional `currency_code`, optional `duration_minutes`, `is_active`, timestamps, optional `deleted_at`.
Owner: Service Catalog.

## 10. `service_interests`
Fields: `id`, `clinic_id`, `customer_id`, `service_id`, `status`, `is_primary`, `first_interested_at`, `last_interested_at`, timestamps.
Status: `ACTIVE`, `BOOKED`, `PURCHASED`, `DROPPED`.
Owner: CRM Core / Lead Lifecycle.

## 11. `knowledge_items`
Approved non-clinical clinic knowledge for receptionist responses.
Fields: `id`, `clinic_id`, `topic`, `content`, `status`, `updated_at`.
Status: `DRAFT`, `APPROVED`, `ARCHIVED`.
Receptionist may use only `APPROVED` clinic-specific factual content.
Owner: Clinic Knowledge / Admin.

## 12. `interactions` — canonical customer timeline
Fields: `id`, `clinic_id`, `customer_id`, `occurred_at`, `channel`, `interaction_type`, `direction`, optional `summary`, optional access-controlled `raw_text`, optional `staff_member_id`, optional `service_id`, optional `result_code`, optional `source_message_id`, `created_at`.
Channels: `WHATSAPP`, `TELEGRAM`, `INSTAGRAM`, `PHONE`, `WEB`, `IN_PERSON`, `INTERNAL`, `OTHER`.
Types: `MESSAGE`, `CALL_NOTE`, `VOICE_NOTE`, `APPOINTMENT_EVENT`, `FOLLOW_UP_EVENT`, `PAYMENT_EVENT`, `STAFF_NOTE`, `STATUS_CHANGE`, `SYSTEM_EVENT`.
Directions: `INBOUND`, `OUTBOUND`, `INTERNAL`.
Rules: append-only in normal operation; corrections are new interactions/audit, not hidden history edits; no clinical diagnosis/treatment notes in MVP.
Owner: Timeline Engine.

## 13. `messages` — messaging transport truth
Fields: `id`, `clinic_id`, optional `customer_id`, `channel`, `provider`, `provider_message_id`, `direction`, `message_type`, optional `text_content`, `delivery_status`, optional `sent_at`, optional `received_at`, `created_at`.
Unique: `(clinic_id, provider, provider_message_id)`.
Message types: `TEXT`, `VOICE`, `IMAGE`, `DOCUMENT`, `BUTTON_RESPONSE`, `SYSTEM`.
Delivery: `RECEIVED`, `QUEUED`, `SENT`, `DELIVERED`, `READ`, `FAILED`.
Owner: Messaging Engine.

## 14. `message_attachments`
Fields: `id`, `clinic_id`, `message_id`, `media_type`, optional `provider_media_ref`, optional `secure_storage_ref`, optional `transcription_text`, optional `retention_until`, `created_at`.
Raw audio retention must be configurable/minimized; structured administrative facts should outlive raw media where appropriate.
Owner: Messaging / Voice Intake.

## 15. `ai_extractions`
Stores AI-proposed structured interpretation, NOT business truth.
Fields: `id`, `clinic_id`, optional `source_interaction_id`, optional `source_message_id`, `schema_name`, `schema_version`, `payload_json`, optional `overall_confidence`, `review_status`, optional `reviewed_by_staff_id`, optional `applied_at`, `created_at`.
Review status: `AUTO_ACCEPTED`, `NEEDS_REVIEW`, `HUMAN_ACCEPTED`, `HUMAN_CORRECTED`, `REJECTED`, `FAILED`.
Authoritative state changes occur only after the owning deterministic engine validates and applies the proposal.
Owner: AI Extraction Engine.

## 16. `appointments`
Fields: `id`, `clinic_id`, `customer_id`, `service_id`, optional `provider_staff_id`, `scheduled_start_at`, optional `scheduled_end_at`, `status`, `confirmation_status`, `reminder_status`, optional `cancellation_reason`, optional `created_by_staff_id`, timestamps.
Appointment status: `TENTATIVE`, `CONFIRMED`, `COMPLETED`, `CANCELLED`, `NO_SHOW`.
Confirmation: `PENDING`, `CONFIRMED`, `DECLINED`, `NOT_REQUIRED`.
Reminder: `NOT_SCHEDULED`, `SCHEDULED`, `SENT`, `FAILED`.
Rules: Appointment Engine alone owns appointment status; reminder sending cannot itself imply confirmation; reschedule updates schedule fields and appends timeline/audit evidence.
Owner: Appointment Engine.

## 17. `tasks` — canonical follow-up work
Fields: `id`, `clinic_id`, optional `customer_id`, `task_type`, optional `assigned_staff_id`, `due_at`, `priority`, optional `reason_code`, `reason_text`, `status`, optional `result_code`, optional `result_text`, optional `source_interaction_id`, optional `source_appointment_id`, optional `completed_at`, timestamps.
Task types: `FOLLOW_UP`, `CALLBACK`, `APPOINTMENT_CONFIRMATION`, `MANUAL_REVIEW`, `PAYMENT_CHECK`, `OTHER`.
Priority: `LOW`, `NORMAL`, `HIGH`, `URGENT`.
Status: `OPEN`, `DONE`, `OVERDUE`, `CANCELLED`.
Rules: Follow-up Engine owns task lifecycle; Lost Lead Recovery uses tasks rather than inventing a second follow-up truth; `customers.next_follow_up_at` derives from open tasks.
Owner: Follow-up Engine.

## 18. `payments` — MVP lite
Fields: `id`, `clinic_id`, `customer_id`, optional `appointment_id`, `payment_type`, `amount`, `currency_code`, `status`, optional `method`, optional `external_reference`, optional `paid_at`, `created_at`.
Type: `DEPOSIT`, `PAYMENT`, `REFUND_RECORD`.
Status: `PENDING`, `PAID`, `FAILED`, `REFUNDED`, `CANCELLED`.
Refund execution requires appropriate human authorization; table may record final state.
Owner: Payment Engine Lite.

## 19. `event_outbox`
Reliable cross-module event delivery.
Fields: `id`, `clinic_id`, `event_name`, `event_version`, `aggregate_type`, `aggregate_id`, `payload_json`, `status`, `attempt_count`, `available_at`, `created_at`, optional `published_at`.
Status: `PENDING`, `PROCESSING`, `PUBLISHED`, `FAILED`.
Owner: Core Integration / Event Layer.

## 20. `processed_events`
Consumer-side idempotency ledger.
Fields: `id`, `consumer_name`, `event_id`, `processed_at`.
Unique: `(consumer_name, event_id)`.
Owner: Core Integration / Event Layer.

## 21. `audit_logs`
Fields: `id`, `clinic_id`, `occurred_at`, `actor_type`, optional `actor_id`, `action`, `entity_type`, `entity_id`, optional `before_json`, optional `after_json`, `correlation_id`.
Append-only and access-controlled.
Owner: Audit / Security.

## 22. Cross-module correlation
Externally triggered workflows propagate `correlation_id`, optional `causation_id`, `schema_version`, and `clinic_id` across n8n/accounts/modules.

## 23. Canonical ownership matrix
- Customer identity/dedup → Identity Resolution Engine
- Customer record → CRM Core
- Customer lifecycle → Lead Lifecycle
- Timeline → Timeline Engine
- Message delivery/transport → Messaging Engine
- AI extracted meaning → AI Extraction proposal only
- Appointment state → Appointment Engine
- Follow-up/task state → Follow-up Engine
- Payment/deposit state → Payment Engine Lite
- Service facts → Service Catalog
- Manager aggregates → Reporting/Supervisor (read canonical state; no shadow CRM)
- Audit → Audit/Security
- Cross-module event delivery → Event Layer

## 24. Core invariants
1. Clinic A data must never be accessible/mutable via Clinic B context.
2. Duplicate provider messages produce one canonical message and at most one business action per idempotency key.
3. Initial customer may be anonymous/unnamed/phone-less but channel identity remains resolvable.
4. Customer merges preserve historical interactions.
5. AI confidence never bypasses human-required policy.
6. Appointment state changes leave audit/timeline evidence.
7. Follow-up completion/overdue transitions leave audit/timeline evidence.
8. Manager reporting reads canonical state; no shadow CRM truth.
9. Failed downstream APIs leave retriable/visible failure state; no silent loss.
10. PII deletion/anonymization uses controlled privacy workflow while preserving required audit integrity.

## 25. Shared payload — `crm_interpretation` v0.1.0
Required shape conceptually:
```json
{
  "schema_name": "crm_interpretation",
  "schema_version": "0.1.0",
  "clinic_id": "uuid",
  "correlation_id": "uuid",
  "source": {"message_id":"uuid-or-null","interaction_id":"uuid-or-null","channel":"TELEGRAM"},
  "customer": {"customer_id":"uuid-or-null","display_name":"خانم رضایی","phone_e164":null},
  "service": {"service_id":"uuid-or-null","service_name_text":"فیشیال"},
  "interpretation": {"intent":"FOLLOW_UP_REQUIRED","proposed_lifecycle_stage":"CONSIDERING","objection_code":"PRICE","summary":"..."},
  "follow_up": {"required":true,"due_at":"2026-09-30T12:00:00Z","reason":"Callback requested"},
  "confidence": {"overall":0.91,"customer_name":0.96,"service":0.93,"follow_up_due_at":0.72},
  "requires_human_review": false
}
```
AI may leave uncertain values null and must not invent. Consumer validates, resolves customer/service, appends timeline, and requests follow-up through owning engines.

## 26. Shared payload — `inbound_message` v0.1.0
```json
{
  "schema_name":"inbound_message",
  "schema_version":"0.1.0",
  "clinic_id":"uuid",
  "correlation_id":"uuid",
  "channel":"WHATSAPP",
  "provider":"provider_name",
  "provider_message_id":"provider-12345",
  "external_sender_identity":"external-user-id",
  "phone_e164":"+989121234567",
  "message_type":"TEXT",
  "text":"سلام هزینه ژل لب چقدره؟",
  "received_at":"2026-09-10T08:30:00Z"
}
```
All channel adapters normalize provider payloads into this envelope before core processing.

## 27. Shared payload — `appointment_command` v0.1.0
```json
{
  "schema_name":"appointment_command",
  "schema_version":"0.1.0",
  "clinic_id":"uuid",
  "correlation_id":"uuid",
  "command":"CREATE",
  "customer_id":"uuid",
  "service_id":"uuid",
  "provider_staff_id":null,
  "requested_start_at":"2026-09-12T13:30:00Z",
  "requested_end_at":null,
  "requested_by":{"type":"customer","id":"uuid-or-external-ref"}
}
```
Commands: `CREATE`, `CONFIRM`, `RESCHEDULE`, `CANCEL`, `MARK_COMPLETED`, `MARK_NO_SHOW`.

## 28. Shared payload — `follow_up_command` v0.1.0
```json
{
  "schema_name":"follow_up_command",
  "schema_version":"0.1.0",
  "clinic_id":"uuid",
  "correlation_id":"uuid",
  "command":"CREATE",
  "customer_id":"uuid",
  "assigned_staff_id":"uuid-or-null",
  "due_at":"2026-09-15T06:30:00Z",
  "priority":"NORMAL",
  "reason_code":"CUSTOMER_REQUESTED_CALLBACK",
  "reason_text":"Customer asked to be called back",
  "source_interaction_id":"uuid"
}
```
Commands: `CREATE`, `COMPLETE`, `CANCEL`, `REASSIGN`, `RESCHEDULE`. `OVERDUE` is normally a system transition, not a user command.

## 29. Minimum constraints
- FK tenant entities to `clinics.id`
- FK customer-linked entities to `customers.id`
- Enforce clinic-context match for referenced entities
- Unique customer provider identity
- Unique provider message ID per clinic/provider
- Unique processed event per consumer/event
- appointment end >= start when present
- `tasks.completed_at` required for `DONE`
- positive normal deposit/payment amounts
- enums constrained to contract values
- if PostgreSQL is used, design for Row-Level Security rather than UI-only tenant filtering

## 30. Parallel development
After shared contracts are frozen, CRM Core, Voice/AI, Receptionist, Appointment, Follow-up, Messaging, Manager/Supervisor, and Audit/Reliability can develop against contract-compliant mocks. No workstream changes shared field/status meanings locally.

## 31. Required shared test fixtures
1. New customer with phone
2. New customer without name
3. Returning customer same channel
4. Same customer second channel
5. Duplicate provider message
6. Ambiguous voice requiring review
7. Voice with clear follow-up date
8. Appointment create + confirm
9. Appointment reschedule
10. Cancellation
11. No-show
12. Follow-up completed on time
13. Follow-up overdue
14. Lost-lead candidate
15. Messaging provider failure
16. AI extraction failure
17. Database write failure
18. Cross-clinic access attempt

## 32. Contract change policy
Optional additive change still needs review/fixture update/version note. Breaking change (rename/remove/type/meaning/enum semantics/canonical ownership) requires version increment, migration plan, compatibility strategy where practical, affected-workstream review, and staging integration validation. No silent local breaking changes.

## 33. Current definition of done for Data Contract v0.1
The contract is considered usable by parallel workers once entity names, IDs/tenant model, enums, ownership, shared payloads, idempotency, fixtures, and shared-source storage are accepted and all workers are instructed not to redefine it locally.

## 34. Next required foundation
`Workflow & Event Contract v0.1` must define event names, producer/consumer ownership, workflow boundaries, sync vs async calls, retry/timeouts/dead-letter behavior, correlation/idempotency, mock interfaces, integration order, and workflow-level acceptance/failure tests.
