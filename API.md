# API Endpoint Map

Base URL: `http://localhost:8000`  
All REST routes are prefixed with `/api/v1`.  
All routes marked 🔒 require `Authorization: Bearer <access_token>`.

---

## Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | — | Register a new user |
| POST | `/api/v1/auth/login` | — | Login → access + refresh tokens |
| POST | `/api/v1/auth/refresh` | — | Exchange refresh token → new token pair |

---

## Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/users/me` | 🔒 | Get current user |
| PATCH | `/api/v1/users/me` | 🔒 | Update current user (name, avatar_url) |

---

## Workspaces

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/workspaces` | 🔒 | Create workspace (creator auto-added as admin) |
| GET | `/api/v1/workspaces` | 🔒 | List workspaces the current user belongs to |
| GET | `/api/v1/workspaces/{workspace_id}` | 🔒 | Get workspace detail |
| GET | `/api/v1/workspaces/{workspace_id}/members` | 🔒 | List workspace members |
| DELETE | `/api/v1/workspaces/{workspace_id}/members/{user_id}` | 🔒 | Remove member from workspace |

---

## Sectors

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/workspaces/{workspace_id}/sectors` | 🔒 | Create sector |
| GET | `/api/v1/workspaces/{workspace_id}/sectors` | 🔒 | List sectors |
| DELETE | `/api/v1/workspaces/{workspace_id}/sectors/{sector_id}` | 🔒 | Delete sector |
| POST | `/api/v1/workspaces/{workspace_id}/sectors/{sector_id}/members` | 🔒 | Add agent to sector |
| DELETE | `/api/v1/workspaces/{workspace_id}/sectors/{sector_id}/members/{user_id}` | 🔒 | Remove agent from sector |

---

## Channel Accounts

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/workspaces/{workspace_id}/channels` | 🔒 | Create channel account |
| GET | `/api/v1/workspaces/{workspace_id}/channels` | 🔒 | List channel accounts |
| GET | `/api/v1/workspaces/{workspace_id}/channels/{channel_id}` | 🔒 | Get channel account |
| PATCH | `/api/v1/workspaces/{workspace_id}/channels/{channel_id}` | 🔒 | Update channel account |
| DELETE | `/api/v1/workspaces/{workspace_id}/channels/{channel_id}` | 🔒 | Delete channel account |
| PUT | `/api/v1/workspaces/{workspace_id}/channels/{channel_id}/credentials` | 🔒 | Upsert credentials (AES-256 encrypted at rest) |

---

## Contacts

| Method | Path | Auth | Query params | Description |
|--------|------|------|--------------|-------------|
| POST | `/api/v1/workspaces/{workspace_id}/contacts` | 🔒 | — | Create contact (with phones + emails) |
| GET | `/api/v1/workspaces/{workspace_id}/contacts` | 🔒 | `search`, `page`, `page_size` | List contacts (paginated) |
| GET | `/api/v1/workspaces/{workspace_id}/contacts/{contact_id}` | 🔒 | — | Get contact |
| PATCH | `/api/v1/workspaces/{workspace_id}/contacts/{contact_id}` | 🔒 | — | Update contact |
| DELETE | `/api/v1/workspaces/{workspace_id}/contacts/{contact_id}` | 🔒 | — | Delete contact |

---

## Conversations

| Method | Path | Auth | Query params | Description |
|--------|------|------|--------------|-------------|
| GET | `/api/v1/workspaces/{workspace_id}/conversations` | 🔒 | `status`, `assignee_id`, `sector_id`, `channel_account_id`, `page`, `page_size` | List conversations (filtered, paginated) |
| GET | `/api/v1/workspaces/{workspace_id}/conversations/{conversation_id}` | 🔒 | — | Get conversation |
| PATCH | `/api/v1/workspaces/{workspace_id}/conversations/{conversation_id}` | 🔒 | — | Update (assignee, sector, status, priority) |
| POST | `/api/v1/workspaces/{workspace_id}/conversations/{conversation_id}/transfer` | 🔒 | — | Transfer to agent/sector (with note) |

---

## Messages

| Method | Path | Auth | Query params | Description |
|--------|------|------|--------------|-------------|
| GET | `/api/v1/workspaces/{workspace_id}/conversations/{conversation_id}/messages` | 🔒 | `page`, `page_size` | List messages (paginated, newest first) |
| POST | `/api/v1/workspaces/{workspace_id}/conversations/{conversation_id}/messages` | 🔒 | — | Send message or internal note (`is_note: true`) |
| POST | `/api/v1/workspaces/{workspace_id}/conversations/{conversation_id}/messages/read` | 🔒 | — | Mark all inbound messages as read |

---

## Labels

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/workspaces/{workspace_id}/labels` | 🔒 | Create label |
| GET | `/api/v1/workspaces/{workspace_id}/labels` | 🔒 | List labels |
| DELETE | `/api/v1/workspaces/{workspace_id}/labels/{label_id}` | 🔒 | Delete label |
| POST | `/api/v1/workspaces/{workspace_id}/labels/{label_id}/assign` | 🔒 | Assign label to conversation |
| DELETE | `/api/v1/workspaces/{workspace_id}/labels/{label_id}/assign/{conversation_id}` | 🔒 | Remove label from conversation |

---

## Flows

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/workspaces/{workspace_id}/flows` | 🔒 | Create flow |
| GET | `/api/v1/workspaces/{workspace_id}/flows` | 🔒 | List flows |
| GET | `/api/v1/workspaces/{workspace_id}/flows/{flow_id}` | 🔒 | Get flow |
| PATCH | `/api/v1/workspaces/{workspace_id}/flows/{flow_id}` | 🔒 | Update flow (name, graph, trigger) |
| DELETE | `/api/v1/workspaces/{workspace_id}/flows/{flow_id}` | 🔒 | Delete flow |
| POST | `/api/v1/workspaces/{workspace_id}/flows/{flow_id}/activate` | 🔒 | Activate flow |
| POST | `/api/v1/workspaces/{workspace_id}/flows/{flow_id}/deactivate` | 🔒 | Deactivate flow |

---

## SLA

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/workspaces/{workspace_id}/sla/policies` | 🔒 | Create SLA policy |
| GET | `/api/v1/workspaces/{workspace_id}/sla/policies` | 🔒 | List SLA policies |
| PATCH | `/api/v1/workspaces/{workspace_id}/sla/policies/{policy_id}` | 🔒 | Update SLA policy |
| DELETE | `/api/v1/workspaces/{workspace_id}/sla/policies/{policy_id}` | 🔒 | Delete SLA policy |
| PUT | `/api/v1/workspaces/{workspace_id}/sla/capacity` | 🔒 | Set agent max conversation capacity |
| GET | `/api/v1/workspaces/{workspace_id}/sla/capacity` | 🔒 | List agent capacities |

---

## Media

| Method | Path | Auth | Query params | Description |
|--------|------|------|--------------|-------------|
| POST | `/api/v1/media/upload` | 🔒 | `workspace_id` | Upload file → MinIO (multipart/form-data, max 50 MB) |
| GET | `/api/v1/media/presign` | 🔒 | `key` | Generate presigned download URL (1h TTL) |

---

## Webhooks

No auth header — secured by HMAC signature or hub verify token.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/webhooks/whatsapp/meta` | Meta hub challenge verification (`hub.verify_token`) |
| POST | `/webhooks/whatsapp/meta` | Inbound events from Meta Cloud API (HMAC: `X-Hub-Signature-256`) |
| POST | `/webhooks/whatsapp/evolution/{instance_name}` | Inbound events from Evolution API (HMAC: `x-evolution-signature`, optional in dev) |

---

## WebSocket

| Path | Auth | Description |
|------|------|-------------|
| `ws://host/ws/{workspace_id}?token=<jwt>` | JWT via query param | Per-workspace real-time room. Send `ping` → receives `pong`. |

### WebSocket event types (server → client)

| `type` | Payload fields | Trigger |
|--------|----------------|---------|
| `message.new` | `conversation_id`, `message_id` | New inbound or outbound message |
| `conversation.updated` | `conversation_id`, `status` | Conversation status/assignment changed |

---

## Utility

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | — | Liveness check → `{"status": "ok"}` |
| GET | `/docs` | — | Swagger UI (FastAPI auto-generated) |
| GET | `/redoc` | — | ReDoc UI |
