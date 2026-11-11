# Shared development deployment - design and implementation plan

> For agentic workers: execute the independent migration/storage checks in parallel under `superpowers:dispatching-parallel-agents`; integrate and verify before deployment. Remaining dependent operations are sequential. This plan implements the user's authorized request to configure SSH, deploy the current version, and validate a shared development app through EasyPanel.

## Goal and design

Deploy the current integrated code to 93.127.210.42 as an EasyPanel-managed CRM2 development stack, visible in the panel with per-container status/logs. Keep the existing Hermes and other services operating. The user selected this VPS and explicitly requested EasyPanel management.

Use a dedicated Compose service `crm2-dev` in the existing `hermes` project, with backend, frontend, worker, beat, PostgreSQL, Redis, MinIO, Evolution and its own PostgreSQL. A new project was attempted through the API, but the panel rejected it because the installation is at its project limit; no existing project is removed or renamed. EasyPanel's Compose service manages the containers, domains and deployment logs. Use the panel's existing generated domain suffix for an initial HTTPS development URL; no custom DNS change or panel-wide setting change is required. A lightweight gateway routes same-origin app/API/WebSocket traffic; storage gets a separate HTTPS route for signed URLs.

Use private service networking, dedicated persistent data, generated secrets and an explicit immutable source revision. No default development password is acceptable for the shared admin login. Do not import local databases, channel credentials or real client data. Keep databases/cache/Evolution administration private; route only required HTTP endpoints. New services must fit the two-core/8-GB VPS with memory available to existing apps.

Native services per process would also be visible, but duplicate code/build settings across backend/worker/beat. A panel-managed Compose service preserves one versioned definition and still exposes container logs/status. A standalone Compose stack outside EasyPanel does not meet the user's visibility requirement.

## Global constraints

- Existing services/projects/networks/data are outside the mutation scope.
- Remote commands use the already verified SSH identity with strict known-host checks. Add a descriptive `crm2-dev` SSH alias without changing existing aliases.
- Secrets stay on the VPS and in ignored local deployment records, never in Git, stdout or the handoff.
- Preserve the preexisting local edits in `backend/.env.local` and `frontend/.env.example`.
- Build from clean versioned source, excluding private source documents and environment files.
- Run migration checks against disposable databases only before applying to the new CRM2 development database.
- No known fake success: a healthy HTTP endpoint alone does not validate auth, DB, WebSocket, storage and worker execution.
- Actual WhatsApp delivery/QR/Meta validation requires a designated number/provider credential; do not send to arbitrary real recipients.

## Review focus

1. Empty/local/QA database histories must upgrade without duplicate-table errors or loss of historical webhook payloads.
2. Browsers must receive HTTPS API/WebSocket/storage URLs rather than localhost or Docker hostnames.
3. A remote deployment must not expose database/cache/default credentials or interrupt other EasyPanel applications.
4. Build settings and runtime environment must agree; NEXT_PUBLIC values are compiled into the frontend.
5. Registered workers must execute a real queued task; periodic jobs and storage need checks beyond container startup.

## Tasks

- [ ] Migration compatibility: inspect/reproduce the history against disposable PostgreSQL databases; add regression coverage, fix only demonstrated migration issues, verify preservation. Owner: migration agent; files `backend/migrations/` and targeted tests.
- [ ] Media endpoint compatibility: test explicit HTTPS public endpoint with internal HTTP storage; adjust endpoint handling without changing existing bare-host behavior. Owner: storage agent; files `backend/app/core/minio.py` and targeted tests.
- [ ] Deployment definition: create deployment Dockerfiles, versioned Compose/gateway configuration and a runbook. Owner: coordinator; files `deploy/`, deployment helper and documentation.
- [ ] SSH and panel setup: add alias; use EasyPanel API over SSH for the new project/service, generated secrets, domains, persistence and deployment. Never mutate EasyPanel's database directly.
- [ ] Build/deploy: validate configuration, build with resources appropriate to the VPS, migrate the new development DB and start dependencies/apps/workers through the panel.
- [ ] Verification: health/readiness, login/workspace/API CRUD, WebSocket, upload/presign/download, Celery queue/beat, provider reachability, logs, TLS and persistence/restart checks. Mark real-provider tests pending when no approved number is connected.
- [ ] Record revision, public URL, panel location, credential location, evidence, limitations and repeatable deployment/rollback instructions. Update the shared branch/PR and appropriate active ClickUp task with evidence under the task's existing authorization.

## Acceptance

The shared URL serves the deployed version over HTTPS, the new stack is visible in EasyPanel, internal dependencies are private, and the implemented core flows pass recorded smoke checks. Unimplemented delivery-domain features and integrations lacking credentials must be identified explicitly. Credentials are provided through a local/private handoff location rather than committed or logged.
