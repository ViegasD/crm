# Shared development deployment - 11/11/2026

## Access and management

- Application: **https://hermes-crm2-dev.5tpiot.easypanel.host**.
- EasyPanel: existing panel at `https://www.powerupwebhooks.cloud`, project **hermes**, Compose service **crm2-dev**. Containers/logs are managed there.
- Signed media: `https://hermes-crm2-storage.5tpiot.easypanel.host`.
- VPS: `93.127.210.42`; verified SSH alias on Fabio's workstation: `crm2-dev`.
- Development login: `admin@crm2.dev`; generated password is in ignored local `var/access/crm2-development-login.json` and root-only `/srv/crm2/ops/credentials.json`. Never commit or post the password. Account belongs to workspace CRM2 Development.

Creating a separate `crm2` project was rejected by EasyPanel's project limit. A dedicated `crm2-dev` Compose service was created in the existing Hermes project without removing/renaming any existing service. Application data, Redis, PostgreSQL and Evolution storage are separate. No CRM2 database/cache/app host ports are published; EasyPanel routes only gateway and storage HTTP traffic.

## Build and runtime corrections

Initial code/deployment commit `8014fa7`; subsequent fixes `f8b5dac`, `1abe85e` and `42c653d` supply media-upload and dependency compatibility corrections. Deployed runtime source is recorded at `/srv/crm2/ops/source-revision`; the initial image tag is the deployment identifier `8014fa7b367a9baf0508d62d6ef625034fdb0851`, not a claim that later compatibility fixes are absent. Image tags must be advanced for subsequent releases.

- Explicit public HTTPS MinIO endpoint works independently of internal HTTP MinIO networking.
- Upload no longer awaits the synchronous bucket helper; reproduced by regression before correction.
- Unavailable, unused `litellm==1.51.0` dependency removed; no AI runtime is implemented.
- `packaging==25.0` explicitly installed and `kombu==5.4.2` pinned to work with Celery 5.4/redis-py 5.2. The unbounded resolver had selected incompatible Kombu 5.7.
- Backend starts after one migration job; worker concurrency is one, and beat has persistent schedule state.
- Next.js standalone image built using Webpack with public HTTPS/WSS URLs; internal rewrites target Docker backend DNS.
- Migration compatibility guards join the existing roots without recreating complete equivalent schemas; legacy webhook payload values are retained and obsolete NOT NULL constraint relaxed for current writes.

Tracked historical `backend/.env.local` was explicitly removed from remote source before the build. No local channel credentials, databases, PDF/WhatsApp exports or default seed password were deployed.

## Validation evidence

EasyPanel successful deployment action: `cmwc9ayke000c07mn6dmcelmt`; prior successful full build `cmwc8x00i000a07mn84zu3aak`. Earlier attempts failed visibly and led to the fixes above. Do not use their error logs as current state without checking the latest action.

| Check | Result |
| --- | --- |
| Real PostgreSQL regression suite | 11 tests passed, including empty/local/QA upgrades and preserved webhook data/new ORM writes; disposable DB container removed |
| Deployed application DB | Migration job exited zero at `202611110001` |
| Frontend image | Webpack compilation, TypeScript, standalone/static generation succeeded on VPS |
| Local lint/type-check | Passed after deployment configuration changes |
| Public HTTPS health/login | 200 from VPS and external workstation, certificate validation enabled |
| Login, workspace, core lists | Passed for members, contacts, channels, conversations, SLA policies, flows, labels, canned responses |
| Contacts | Create, update, delete smoke fixture passed |
| Media | Upload, presign, public HTTPS download/content comparison and cleanup passed |
| WebSocket | Public authenticated WSS ping/pong passed |
| Token refresh | Passed |
| Celery | Real `webhook.retry_pending` task processed and result retrieved |
| Evolution | Authenticated API reachable, zero instances |
| EasyPanel restart | Restart API succeeded; the complete public smoke suite passed again afterward, preserving the development account/data |
| Runtime | Ten running services, zero restart counts at status capture; backend/frontend/PostgreSQL/Redis healthchecks healthy; migrate exited zero |
| Isolation | No CRM2 host-port bindings; existing applications stayed running |
| Logs | No error/traceback markers in recent API/worker/beat logs at capture |

After the restart, worker control ping returned one active worker and Redis contained 45 successful task results, with no failed result reported in that capture. This supports scheduler/worker operation; it does not certify every business-rule branch. D01.5 and D05.3 task descriptions were updated with evidence and left `in progress` for remaining manual/backup/acceptance work.

Detailed smoke/status output is stored privately on VPS under `/srv/crm2/ops/`. Initial database dump: `/srv/crm2/backups/initial-verified-crm.dump` (180372 bytes at creation). This is a local manual DB backup, not an off-server scheduled backup or tested restore. Storage was empty after smoke cleanup; no existing business objects were migrated.

## Limits and next testing

The user explicitly chose **leave WhatsApp unpaired**. No test/client number was paired and no WhatsApp messages were sent. QR pairing, Meta credentials/coexistence, live inbound/outbound media and delivery receipts remain untested. All new marketing/e-commerce delivery-domain functionality is still pending implementation.

Browser automation could not open a browser because its host was unavailable. HTTP/API/WebSocket checks above do not constitute a visual UI walkthrough. Thiago and the contributor should walk through login, workspace, settings, contacts, inbox/timeline, simultaneous assignment, pauses/SLA and error states using this shared development instance.

Existing authorization/media tenant-isolation and onboarding gaps remain tracked in the backlog. Use test data. One API process is used because WebSocket rooms are in memory; background-worker-originated browser broadcasts need separate coverage/pubsub work. Passing a queue task and a WebSocket ping does not prove worker-to-browser event delivery.

The test schemas represent the known database histories, not every possible manual schema variation. Do not drop/stamp an existing shared DB to silence migration errors. Back up and reproduce upgrades on copies first.

## Reuse and redeploy

See [deployment runbook](../../deploy/README.md) and [design/plan](../planning/DEPLOYMENT_EASYPANEL_2026-11-11.md). Deploy an agreed commit through EasyPanel, preserve secrets and volumes, and run the smoke script after every rollout. Inline source uses the panel-mounted source directory; source is uploaded deliberately and automatic GitHub deployment has not been configured. Other agents should coordinate deployment ownership to avoid overwriting each other's running version.
