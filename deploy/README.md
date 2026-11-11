# Shared development app on EasyPanel

Target: `93.127.210.42`. SSH alias on Fabio's machine: `crm2-dev`, using the existing verified key/known-host file. No private key is stored in this repository.

EasyPanel location: project **hermes**, Compose service **crm2-dev**. The panel rejected a fourth project due to its project limit, so this isolated service lives in the existing project. It does not share databases, Redis, Evolution instances or volumes with the existing applications.

Expected routes:

- App/API/WebSocket: `https://hermes-crm2-dev.5tpiot.easypanel.host`.
- Signed storage downloads: `https://hermes-crm2-storage.5tpiot.easypanel.host`.
- EasyPanel: `https://www.powerupwebhooks.cloud` (or existing panel access).

## Definition and secrets

`compose.development.yml` is the panel's inline Compose source. `frontend.Dockerfile` builds Next.js standalone with explicit public HTTPS/WSS URLs and an internal API destination. `nginx.conf` sends `/api`, `/webhooks`, `/ws`, health and API docs to the backend and other requests to Next.js. Access logs are disabled to avoid storing query JWTs/signed URLs.

The panel creates the proxy-network override for `gateway` and `minio`. No host data ports are published. PostgreSQL, Redis, storage, beat state and Evolution data use dedicated named volumes. Worker concurrency is one; only one API process is configured because WebSocket rooms currently reside in process memory.

Environment values are generated on the VPS and saved in the panel's environment editor, plus root-only `/srv/crm2/ops/development.env`. `development.env.example` contains variable names only. Keep the encryption key stable across redeployments or existing channel credentials cannot be decrypted. Never copy `.env` files from a developer checkout into the deployed source.

Development login credentials are root-only at `/srv/crm2/ops/credentials.json`. Obtain them over SSH or another approved private channel. `bootstrap_development.py` provisions the designated account/workspace from JSON on stdin; it does not print the password or use the default seed account.

## Deployment procedure

1. Use an agreed source commit from the shared integration branch; review changes and back up CRM2 database/storage before migration or volume changes.
2. Stage clean source under `/srv/crm2/releases/<revision>` and the panel-mounted code source directory `/etc/easypanel/projects/hermes/crm2-dev/code/source`. Exclude every real environment file, private document, cache and dependency directory. The current host's release marker is `/srv/crm2/ops/source-revision`.
3. Set `SOURCE_DIR` to that directory in the panel environment. Use immutable matching image tags in `CRM2_REVISION`. Set the app/storage hostname build arguments before building; NEXT_PUBLIC values are compiled into JavaScript.
4. Update inline Compose source from this directory and deploy **through EasyPanel**. Do not launch an independent app stack that bypasses panel management. The deployment action builds backend/frontend, waits for PostgreSQL/Redis health, applies migrations once, and starts app/workers.
5. Review deployment output and service logs in the panel. Verify the migrate container exited zero and running services stay healthy. A failed migration must not be worked around by stamping or dropping application data.
6. Bootstrap only the designated development account when needed, then run `smoke_development.py /srv/crm2/ops/credentials.json` on the host. The script tests public HTTPS login/API, contact CRUD, storage upload/presign/download, WebSocket ping/pong, token refresh, a real queued Celery task and Evolution API reachability. It removes its contact/object fixtures.
7. Record actual revision, health status, test output and missing real-provider checks in a dated report. Changing a tag or restarting a container alone is not validation.

The local deployment implementation also fixes independent public HTTPS/internal HTTP storage URLs and a synchronous-helper await error in media upload. The unavailable, unused `litellm==1.51.0` pin was removed; AI routing remains unimplemented.

## Migration regression checks

`backend/tests/test_migration_upgrade.py` requires `CRM2_MIGRATION_TEST_URL` pointing to a **disposable PostgreSQL admin database** with CREATEDB privileges. It creates/drops only uniquely named test databases. Cover empty, representative local and QA histories and historical webhook payloads/new ORM inserts. Do not point it at production or use the normal application database as its admin database.

Historical migrations were made conditional on the equivalent schema already existing when joining independent roots. The merge keeps old webhook payloads but drops the obsolete column's NOT NULL requirement so current raw_payload-only writes work. Validate any deployed schema not represented in these fixtures separately; these tests are not a universal database repair tool.

## Recovery and testing limits

Redeploying a previous application image is possible from the panel, but schema changes and data restoration require their own compatibility review. Never remove volumes to fix a startup issue. Keep database and uploaded-file backups together and test restoration in an isolated environment before relying on them.

The app is a shared development instance. Delivery-domain features have not yet been implemented. Role/media isolation gaps in the existing backlog still apply; use test data. Real WhatsApp sending, receiving, QR pairing or Meta coexistence needs a designated number and provider setup. No real number should be connected or messaged without its owner's authorization.

Current WebSocket broadcasting is in-memory per API process; events emitted directly from a separate Celery worker do not automatically reach connected browsers. Worker-to-browser live updates need additional integration coverage and potentially a Redis pub/sub bridge before claiming full real-time behavior.
