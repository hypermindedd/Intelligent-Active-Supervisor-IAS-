# IAS Reports

Reports are mirrored between Notion and GitHub so Human Leadership, Warden and distributed workers can read the same operational state.

## Report types

- `2H_CHANGE` — generated every two hours only when meaningful state changed.
- `DAILY_1200` — generated every day at 12:00 Tehran time.
- `PHASE_GATE` — generated before/after a major phase transition.
- `INCIDENT` — generated for critical defects, lock escalations or integration failures.

## Mandatory daily report sections

1. Report timestamp and reporting window
2. Overall project progress %
3. Workstream-by-workstream progress %
4. Changes since previous report
5. Active gates and locks
6. Open Debugger findings
7. New Warden directives and their disposition
8. Human decisions required
9. Current priorities P0/P1/P2
10. Next phase and prerequisites
11. Workstreams allowed to proceed
12. Workstreams that must stop
13. Which work should continue in CHAT vs WORK vs N8N/CODEX
14. Risks and expected verification evidence

A report must not manufacture progress from activity. Progress is based on accepted deliverables and passed gates/tests.
