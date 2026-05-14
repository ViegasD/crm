# Project Structure

> Reference map of all files and directories in the CRM project.
> Stack: Next.js (frontend) + FastAPI (backend) + PostgreSQL + Redis + MinIO + Celery + LiteLLM.

---

## Root

```
crm2/
├── docker-compose.yml          # All services: postgres, redis, minio, backend, celery, frontend
├── SCOPE.md                    # Project scope and requirements
├── STRUCTURE.md                # This file
├── backend/
└── frontend/
```

---

## Backend

```
backend/
├── Dockerfile
├── alembic.ini                 # Alembic config — points to migrations/
├── requirements.txt
├── .env.example
│
├── migrations/
│   ├── env.py                  # Alembic env — imports all models for auto-detect
│   └── versions/               # Generated migration files
│
└── app/
    ├── main.py                 # FastAPI app factory, CORS, router registration
    │
    ├── api/
    │   └── v1/
    │       ├── auth.py             # POST /auth/login, /auth/refresh, /auth/logout
    │       ├── workspaces.py       # CRUD workspaces + branding
    │       ├── users.py            # CRUD users, profile, status
    │       ├── sectors.py          # CRUD sectors + sector_members
    │       ├── channel_accounts.py # CRUD channel accounts + credentials
    │       ├── contacts.py         # CRUD contacts, phones, emails, custom attrs
    │       ├── conversations.py    # List/get/update conversations, filters
    │       ├── messages.py         # Send message, list messages, mark read
    │       ├── labels.py           # CRUD labels + assign to conversations
    │       ├── flows.py            # CRUD flows + activate/deactivate
    │       ├── bot_configs.py      # CRUD bot_configs + capabilities
    │       ├── sla_policies.py     # CRUD SLA policies
    │       ├── agent_capacity.py   # Get/set agent capacity limits
    │       ├── campaigns.py        # CRUD campaigns + contacts + launch
    │       ├── macros.py           # CRUD macros + execute
    │       ├── media.py            # POST /media/upload, GET /media/presign
    │       ├── billing.py          # Subscription, usage, invoices
    │       ├── analytics.py        # Dashboard metrics, agent drill-down
    │       ├── exports.py          # Async export jobs
    │       ├── canned_responses.py # CRUD canned responses
    │       └── help_center.py      # CRUD articles + categories
    │
    ├── webhooks/
    │   ├── whatsapp/
    │   │   ├── meta.py             # POST /webhooks/whatsapp/meta
    │   │   ├── gupshup.py          # POST /webhooks/whatsapp/gupshup
    │   │   └── evolution.py        # POST /webhooks/whatsapp/evolution
    │   ├── instagram.py            # POST /webhooks/instagram/meta
    │   ├── facebook.py             # POST /webhooks/facebook/meta
    │   ├── telegram.py             # POST /webhooks/telegram/{bot_id}
    │   └── stripe.py               # POST /webhooks/stripe
    │
    ├── models/                     # SQLAlchemy ORM models (one file per domain)
    │   ├── base.py                 # declarative_base(), common mixins (id, timestamps)
    │   ├── enums.py                # All PostgreSQL enum types
    │   ├── workspace.py            # workspaces, users, memberships, sectors, branding, sso
    │   ├── channel.py              # channel_accounts, channel_credentials
    │   ├── contact.py              # contacts, phones, emails, notes, custom_attrs, org_links
    │   ├── conversation.py         # conversations, messages, message_identities, events,
    │   │                           #   participants, labels, conversation_labels
    │   ├── filter.py               # conversation_folders, folder_rules, saved_filters
    │   ├── sla.py                  # sla_policies, sla_events, agent_capacity, agent_status_logs
    │   ├── flow.py                 # flows, flow_executions, tool_executions
    │   ├── bot.py                  # bot_configs, bot_config_capabilities
    │   ├── campaign.py             # campaigns, campaign_contacts
    │   ├── macro.py                # macros, macro_actions
    │   ├── audit.py                # audit_logs, security_audit_logs
    │   ├── csat.py                 # csat_surveys
    │   ├── metrics.py              # conversation_metrics
    │   ├── help.py                 # help_articles, help_categories, help_article_embeddings
    │   ├── integration.py          # integration_configs
    │   ├── canned.py               # canned_responses
    │   └── billing.py              # plans, workspace_subscriptions, llm_usage_records,
    │                               #   billing_invoices, billing_invoice_items
    │
    ├── schemas/                    # Pydantic v2 schemas (request/response DTOs)
    │   ├── auth.py
    │   ├── workspace.py
    │   ├── user.py
    │   ├── sector.py
    │   ├── channel.py
    │   ├── contact.py
    │   ├── conversation.py
    │   ├── message.py
    │   ├── label.py
    │   ├── flow.py
    │   ├── bot_config.py
    │   ├── sla.py
    │   ├── campaign.py
    │   ├── macro.py
    │   ├── media.py
    │   ├── billing.py
    │   ├── analytics.py
    │   └── export.py
    │
    ├── services/                   # Business logic layer
    │   ├── auth_service.py         # JWT issue/verify, login, refresh
    │   ├── conversation_service.py # Create/assign/transfer/resolve conversations
    │   ├── message_service.py      # Send message → adapter → persist → websocket
    │   ├── flow_executor.py        # Flow execution engine (node processor, state machine)
    │   ├── bot_runner.py           # Agentic loop: LLM + tools until handoff
    │   ├── media_service.py        # Upload to MinIO, generate presigned URLs
    │   ├── sla_service.py          # Check deadlines, escalate, update sla_status
    │   ├── campaign_service.py     # Build contact list, rate-limit send, track delivery
    │   ├── billing_service.py      # Aggregate usage, generate invoices, Stripe sync
    │   ├── analytics_service.py    # Metric queries for dashboard + drill-down
    │   ├── export_service.py       # Build CSV/JSON/PDF exports
    │   ├── copilot_service.py      # LLM suggestions for human agents
    │   ├── notification_service.py # Slack, email, in-app alerts
    │   └── contact_service.py      # Dedup, merge, link org contacts
    │
    ├── channels/                   # Provider adapter layer
    │   ├── base.py                 # WhatsAppProviderAdapter ABC + NormalizedEvent + ProviderCapabilities
    │   ├── whatsapp/
    │   │   ├── meta_cloud.py       # MetaCloudAdapter
    │   │   ├── gupshup.py          # GupshupAdapter
    │   │   ├── evolution_baileys.py # EvolutionBaileysAdapter
    │   │   └── evolution_cloud.py  # EvolutionCloudAdapter
    │   ├── instagram.py
    │   ├── facebook.py
    │   └── telegram.py
    │
    ├── workers/
    │   ├── celery_app.py           # Celery instance + broker config
    │   └── tasks/
    │       ├── campaigns.py        # send_campaign_batch, track_delivery
    │       ├── exports.py          # generate_export_file, notify_ready
    │       ├── media.py            # download_provider_media, reupload_to_minio
    │       ├── embeddings.py       # generate_help_article_embeddings
    │       ├── billing.py          # close_billing_period, emit_nfe
    │       └── sla.py              # check_sla_deadlines (periodic)
    │
    ├── websocket/
    │   ├── manager.py              # ConnectionManager — per-workspace rooms
    │   └── handlers.py             # /ws/{workspace_id} endpoint + message dispatch
    │
    └── core/
        ├── config.py               # Settings via pydantic-settings (.env parsing)
        ├── database.py             # Async engine, session factory, get_db dependency
        ├── dependencies.py         # get_current_user, require_role, get_workspace
        ├── security.py             # JWT, bcrypt, HMAC webhook validation (timing-safe)
        ├── encryption.py           # AES-256 for channel_credentials + sso_configurations
        ├── redis.py                # Async Redis client singleton
        ├── minio.py                # MinIO/S3 client, presign helpers
        └── litellm_client.py       # LiteLLM wrapper — completion, streaming, cost tracking
```

---

## Frontend

```
frontend/
├── Dockerfile
├── next.config.ts              # Rewrites /api/* → backend; image domains
├── tsconfig.json
├── package.json
├── tailwind.config.ts          # Tailwind config + shadcn preset
├── postcss.config.mjs
├── .env.example
│
└── src/
    ├── app/                    # Next.js App Router
    │   ├── layout.tsx          # Root layout (fonts, providers)
    │   ├── globals.css
    │   ├── page.tsx            # Redirects → /inbox
    │   │
    │   ├── (auth)/             # Unauthenticated layout (centered card)
    │   │   ├── layout.tsx
    │   │   ├── login/
    │   │   │   └── page.tsx
    │   │   └── register/
    │   │       └── page.tsx
    │   │
    │   └── (dashboard)/        # Authenticated layout (sidebar + main)
    │       ├── layout.tsx
    │       │
    │       ├── inbox/
    │       │   ├── page.tsx                    # Conversation list (all / mine / unassigned)
    │       │   └── [conversationId]/
    │       │       └── page.tsx                # Conversation detail + message thread
    │       │
    │       ├── contacts/
    │       │   ├── page.tsx                    # Contact list with search + filters
    │       │   └── [contactId]/
    │       │       └── page.tsx                # Contact profile page
    │       │
    │       ├── flows/
    │       │   ├── page.tsx                    # Flow list
    │       │   └── [flowId]/
    │       │       └── page.tsx                # ReactFlow canvas editor
    │       │
    │       ├── reports/
    │       │   ├── page.tsx                    # Overview dashboard
    │       │   └── agents/
    │       │       └── [agentId]/
    │       │           └── page.tsx            # Agent drill-down
    │       │
    │       └── settings/
    │           ├── page.tsx                    # Settings landing
    │           ├── channels/
    │           │   └── page.tsx                # Channel accounts list + connect new
    │           ├── team/
    │           │   └── page.tsx                # Users, roles, sectors, capacity
    │           ├── sla/
    │           │   └── page.tsx                # SLA policies
    │           ├── integrations/
    │           │   └── page.tsx                # Third-party integrations
    │           ├── branding/
    │           │   └── page.tsx                # White-label config
    │           └── billing/
    │               └── page.tsx                # Plans, usage chart, invoices
    │
    ├── components/
    │   ├── ui/                 # shadcn/ui primitives: Button, Input, Dialog, etc.
    │   │
    │   ├── layout/
    │   │   ├── Sidebar.tsx         # Icon sidebar with nav items
    │   │   ├── Header.tsx          # Top bar (workspace selector, user menu)
    │   │   └── WorkspaceProvider.tsx # Context: current workspace, role
    │   │
    │   ├── inbox/
    │   │   ├── ConversationList.tsx    # Scrollable list with real-time updates
    │   │   ├── ConversationItem.tsx    # Row: avatar, last message, unread badge
    │   │   ├── MessageThread.tsx       # Chat history with virtualized scroll
    │   │   ├── MessageBubble.tsx       # Renders text/media/note/activity messages
    │   │   ├── ReplyBox.tsx            # Input + attachment + canned + copilot suggest
    │   │   ├── ConversationHeader.tsx  # Assignee, status, actions menu
    │   │   ├── ContactSidebar.tsx      # Contact info panel (right side)
    │   │   ├── ActionTimeline.tsx      # Conversation events timeline
    │   │   └── CopilotSuggest.tsx      # AI suggestion bar inside ReplyBox
    │   │
    │   ├── flow-builder/
    │   │   ├── FlowCanvas.tsx          # ReactFlow wrapper with custom nodes/edges
    │   │   ├── FlowToolbar.tsx         # Add node, zoom, save, toggle active
    │   │   ├── nodes/
    │   │   │   ├── TriggerNode.tsx
    │   │   │   ├── MessageNode.tsx
    │   │   │   ├── BotNode.tsx
    │   │   │   ├── QuestionNode.tsx
    │   │   │   ├── MenuNode.tsx
    │   │   │   ├── ConditionNode.tsx
    │   │   │   ├── SwitchNode.tsx
    │   │   │   ├── ActionNode.tsx
    │   │   │   ├── HttpRequestNode.tsx
    │   │   │   ├── WaitNode.tsx
    │   │   │   ├── AssignAgentNode.tsx
    │   │   │   └── EndNode.tsx
    │   │   └── panels/
    │   │       └── NodeConfigPanel.tsx # Right-side config form per selected node type
    │   │
    │   ├── contacts/
    │   │   ├── ContactCard.tsx
    │   │   ├── ContactMetrics.tsx
    │   │   └── ConversationHistory.tsx
    │   │
    │   └── analytics/
    │       ├── MetricCard.tsx
    │       ├── AgentRankingTable.tsx
    │       └── charts/
    │           ├── DailyLineChart.tsx
    │           ├── DonutChart.tsx
    │           └── StackedBarChart.tsx
    │
    ├── hooks/
    │   ├── use-conversations.ts    # SWR/React Query for conversation list + mutations
    │   ├── use-messages.ts         # Messages for a conversation + infinite scroll
    │   ├── use-websocket.ts        # Connect WS, dispatch typed events to stores
    │   ├── use-contacts.ts
    │   └── use-auth.ts             # Login, logout, token refresh
    │
    ├── stores/                     # Zustand stores
    │   ├── auth-store.ts           # token, user, workspace
    │   ├── conversation-store.ts   # active conversation, list cache, filters
    │   └── ui-store.ts             # sidebar collapsed, active panel, modals
    │
    ├── lib/
    │   ├── api.ts                  # Axios instance + auth interceptor
    │   ├── websocket.ts            # WS client: connect, reconnect, typed dispatch
    │   └── utils.ts                # cn(), formatDate(), formatBytes(), etc.
    │
    └── types/
        ├── conversation.ts         # Conversation, Message, Attachment types
        ├── flow.ts                 # FlowGraph, FlowNode, FlowEdge, node types
        ├── contact.ts              # Contact, ContactPhone, ContactEmail
        ├── channel.ts              # ChannelAccount, ChannelType, WhatsAppProvider
        └── api.ts                  # Generic API response wrappers (Paginated<T>, ApiError)
```

---

## Key Conventions

| Convention | Rule |
|---|---|
| **API prefix** | All REST routes under `/api/v1/`. Webhooks under `/webhooks/`. WebSocket under `/ws/` |
| **Auth header** | `Authorization: Bearer <jwt>` on every authenticated request |
| **Tenant isolation** | Every DB query filters by `workspace_id` — enforced in `get_workspace` dependency |
| **Webhook validation** | HMAC-SHA256 timing-safe compare + 5-min replay window — done in router before handler |
| **Idempotency** | `message_identities.idempotency_key` checked before inserting any inbound message |
| **Media** | Never store binaries in DB. Always MinIO key. Frontend uses presigned URLs (TTL 1h) |
| **Credentials** | All channel credentials and SSO configs encrypted AES-256 before DB insert |
| **LLM calls** | Always through `core/litellm_client.py` — logs `llm_usage_records` after every call |
| **Async jobs** | Anything slow (exports, campaigns, media re-upload) goes to Celery tasks |
| **Real-time** | Backend broadcasts via `websocket/manager.py` to per-workspace rooms |
| **No business logic in Next.js** | Frontend is pure UI. All logic in FastAPI services |
