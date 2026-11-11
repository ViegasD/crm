# AUD01 — authorization and isolation

Implemented on `codex/aud01-authorization`, based on shared planning revision `adbf67f`. This branch contains the authorization changes and their tests; the original checkout's unrelated edits and private environment files remain untouched.

## Access contract

- Workspace membership is required. Nonmembers receive HTTP 403; missing/deleted users and invalid access-token subjects receive HTTP 401.
- A private conversation is visible only to its assignee or an explicit participant who still belongs to the workspace. Administrators do not acquire implicit private access. Hidden and nonexistent conversations both return HTTP 404.
- The same predicate protects lists/counts, direct conversation paths, messages/events, participants, labels, locks, snooze, SLA dispatch, macro execution, canned-response context, contact timelines, mentions, notifications and supervisor/CSAT/heatmap reads.
- Bulk actions preflight every requested conversation before changing any record. Mixed visible/hidden batches return HTTP 404 without partial changes. Static bulk paths are registered before dynamic conversation paths so `/bulk/transfer` reaches its intended handler.
- Workspace-member removal and channel/sector administration require the workspace's admin role. Workspace locking serializes removals and prevents deleting the last admin. Sector/channel references and participant additions cannot cross workspace boundaries.
- WebSocket handshake, incoming frames and outgoing delivery check membership and access-token validity. Idle sessions are rechecked every 15 seconds. Membership removal blocks subsequent delivery; private events are filtered per recipient, and `send_to` targets one user. Presence events retain their subject `user_id` without becoming private notifications.
- Conversation event batches from inbound webhooks/replay and API update/transfer/send publish after successful commit. Nested service broadcasts join the batch. Rollback discards the batch; failure reporting uses primitive IDs/metadata captured before rollback can expire ORM objects.

## Verification

The initial 14 authorization test cases reproduced 45 failures on the published baseline. Additional tests pinned private rendering, first-conversation commit/rollback behavior and an injected processing exception in webhook retry. The latter reproduced SQLAlchemy `MissingGreenlet` before scalar failure-reporting metadata was retained.

Final command, executed against the changed source in the pinned Python 3.12 backend image with `DEBUG=false` and `CRM2_MIGRATION_TEST_URL` set to a separate disposable PostgreSQL admin endpoint:

```text
python -m unittest discover -s tests -p 'test*.py' -v
Ran 38 tests in 19.680s
OK
```

All 26 authorization tests and 12 existing tests passed, including the empty/local/QA migration upgrade checks. Each database integration class/case uses a uniquely named disposable database; tests did not use the shared app database. The final remote log is `/srv/crm2/ops/aud01-verified.log`. `git diff --check` also passed. An independent, read-only reviewer checked the final changes and reported no remaining blocker, subject to these test results.

The suite checks actual HTTP/WebSocket behavior and PostgreSQL persistence. Presence updates and injected provider failures are mocked to avoid Redis/provider side effects. No client number was paired and no real WhatsApp messages were sent.

## Limits and next work

- This is a source-code validation, not a deployment or visual/frontend acceptance. The shared development instance has not been upgraded by this task.
- AUD02 still owns media ownership, attachment linking, download authorization and signed-URL revocation. The conversation authorization fixes do not certify arbitrary storage keys or existing signed URLs.
- AUD03 still owns the known timeline enum failure when messages are rendered, search correctness and full transfer/assignment target validation. The timeline tests here verify which conversations may be returned without claiming that separate content-rendering defect is fixed.
- AUD06 still owns durable/cross-process fanout, recovery and delivery guarantees. The transaction buffer here is process-local and in memory; it does not provide a durable outbox or worker-to-browser transport.
- No schema changes or migrations were introduced. Administrative rules in this task cover membership, channels and sectors; onboarding/deactivation and the full product role matrix remain separate tasks.

Next step: review/merge this branch into the agreed shared baseline, deploy through EasyPanel, run the development smoke checks, then continue AUD02/AUD03 with their own regression evidence.
