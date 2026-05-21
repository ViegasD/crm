# CRM2 - Escopo e status real do projeto

Data da auditoria: 2026-05-21

## Fonte usada

- Repositorio local: `C:\Users\thiag\crm`
- Documento de escopo local: `SCOPE.md`
- ClickUp: pasta `CRM2` no espaco `viponline`
- Validacao local: leitura de codigo, inventario de rotas/modelos e comandos basicos

## Resumo executivo

O projeto ja tem um esqueleto importante de CRM multicanal:

- Backend FastAPI com rotas de auth, usuarios, workspaces, setores, canais, contatos, conversas, mensagens, etiquetas, fluxos, SLA, midia, webhooks e WebSocket.
- Modelos SQLAlchemy para 26 tabelas aproximadas, cobrindo fundacao, canais, contatos, conversas, mensagens, labels, flow builder, SLA/capacidade e bot configs.
- Frontend Next.js com telas de login, inbox, contatos, fluxos, configuracoes e relatorios.
- Docker Compose com Postgres, Redis, MinIO, backend, worker Celery, Evolution API e frontend.

Mas o estado real ainda parece mais "MVP esqueleto" do que produto funcional. O ClickUp marca varias tarefas como fechadas, principalmente em P1 Stage 1 e Stage 2, mas o codigo ainda tem lacunas bloqueantes:

- Nao existem migrations Alembic reais em `backend/migrations/versions`.
- Dependencias locais nao estao instaladas: backend falha ao importar por falta de `sqlalchemy`, frontend falha porque nao existe `node_modules`.
- Ha contratos quebrados entre frontend e backend em canais, fluxos, contatos e mensagens.
- Webhooks Meta/Evolution chamam `persist_inbound_message` com assinatura errada.
- Envio de mensagem pelo agente chama `send_agent_message` com assinatura errada.
- Permissoes por workspace/role existem como helper, mas quase nenhuma rota usa enforcement real.
- Dashboard, auditoria, AI, billing, campanhas, demais canais, Help Center, Live Chat, SSO e white-label ainda estao essencialmente fora do codigo.

## Status ClickUp

Pasta `CRM2`:

- 22 listas
- 93 tarefas
- 20 fechadas
- 73 abertas

Fechado no ClickUp:

- P1 Stage 1 inteiro: auth, workspace, setores, membros, middleware e tabelas base.
- P1 Stage 2 quase inteiro: WhatsApp, inbox, contatos, midia, WebSocket, providers e tabelas base.
- Parte de P1 Stage 3: transferencia e etiquetas.

Aberto no ClickUp:

- Webhook events duravel.
- Segurança de webhooks completa.
- Flow builder completo e executor.
- Capacidade/SLA operacional.
- AI bot, Copilot, auditoria, dashboards, demais canais, pastas, billing, campanhas, macros, white-label, SSO, permissoes granulares, Help Center, Live Chat e integracoes.

## Comparativo por area

### P1 Stage 1 - Auth + Workspace + Setorizacao

ClickUp: fechado.

Codigo existente:

- `users`, `workspaces`, `user_workspace_memberships`, `sectors`, `sector_members`.
- JWT access/refresh.
- Login e registro.
- CRUD basico de workspaces, membros e setores.
- Helper `get_workspace_member` e `require_roles`.

Problemas / divergencias:

- Nao ha migrations reais, apesar das tarefas de tabela estarem fechadas.
- Enforcement de membership/role nao foi aplicado nas rotas principais; muitas rotas apenas exigem usuario autenticado.
- Nao existe UI para criar workspace ou convidar/adicionar membros.
- `MembershipOut` nao inclui dados do usuario, mas o frontend espera `m.user.name` e `m.user.email`.

Status real sugerido: parcial, nao pronto para fechar como funcional.

### P1 Stage 2 - Canal WhatsApp + Inbox Unificado

ClickUp: quase fechado, com `webhook_events` aberto.

Codigo existente:

- Modelos de `channel_accounts`, `channel_credentials`, `conversations`, `messages`, `message_identities`.
- Adapters Meta Cloud e Evolution.
- Webhooks Meta e Evolution.
- Inbox com lista, thread, reply box e WebSocket.
- CRUD de contatos.
- Upload/presigned URL de midia.
- Worker Celery para midia.

Problemas / divergencias:

- Webhooks chamam `persist_inbound_message(db, event)`, mas o servico espera varios argumentos separados.
- `messages.py` chama `send_agent_message(db, conv, current_user.id, body)`, mas o servico espera `workspace_id` antes da conversa.
- O envio de mensagem pelo agente apenas salva no banco; nao chama adapter WhatsApp para enviar ao provider.
- Frontend de canais envia `{ name, provider: "evolution" }`, mas backend espera `display_name` e provider enum `evolution_baileys` ou `evolution_cloud`.
- Credenciais Evolution no frontend usam `url`, `api_key`, `instance_name`, mas factory/backend procuram `evolution_base_url`, `evolution_api_key`, `evolution_instance_id`.
- `ContactOut` nao retorna phones/emails, mas UI lista `c.phones` e `c.emails`.
- `webhook_events` realmente nao existe.
- Nao ha migrations para nenhuma dessas tabelas.

Status real sugerido: estrutura parcial, mas fluxo ponta a ponta ainda quebrado.

### P1 Stage 3 - Acoes de Conversa Basicas

ClickUp: transferencia e etiquetas fechadas; canned responses, participantes e timeline abertas.

Codigo existente:

- Transferencia de conversa altera assignee/setor e cria `conversation_event`.
- Labels e `conversation_labels` existem.
- `conversation_participants` existe no modelo.
- Notas internas existem como tipo de mensagem.

Problemas / divergencias:

- UI visivel de labels/transferencia depende do header, mas precisa validacao manual.
- `assign_label` cria `ConversationLabel` sem `workspace_id`, embora o modelo exija esse campo.
- Participantes existem no modelo, mas nao ha API/UI.
- Timeline de eventos existe como tabela, mas nao ha endpoint/UI.
- Canned responses nao existem.

Status real sugerido: parcial.

### P1 Stage 4 - Seguranca de Webhooks

ClickUp: aberto.

Codigo existente:

- Meta verifica HMAC quando ha `app_secret`.
- Evolution verifica assinatura pelo adapter.
- Existe helper de HMAC e timestamp.

Problemas / divergencias:

- Sem `security_audit_logs`.
- Sem log de tentativas invalidas.
- Sem anti-replay aplicado de forma consistente.
- Sem ingestao duravel em `webhook_events`.

Status real sugerido: iniciado, nao pronto.

### P1 Stage 5 - Flow Builder

ClickUp: aberto.

Codigo existente:

- Modelos `flows` e `flow_executions`.
- Tela de lista de fluxos.
- Tela com ReactFlow e palette de alguns nos.

Problemas / divergencias:

- Frontend cria fluxo com `{ name, description }`, mas backend exige `trigger_type` e `nodes_data`.
- Frontend salva `graph`, mas backend schema espera `nodes_data`; extra fields do Pydantic tendem a ser ignorados.
- `FlowOut` nao retorna o grafo; editor nao consegue recarregar o fluxo.
- Nao existe executor de fluxo.
- Nao ha configuracao real dos parametros dos nos.

Status real sugerido: UI inicial, contrato quebrado, sem execucao.

### P1 Stage 9 - Capacidade + SLA

ClickUp: aberto.

Codigo existente:

- Modelos `sla_policies`, `sla_events`, `agent_capacity`.
- CRUD basico de politicas de SLA.
- Endpoint para set/list de capacidade.
- UI simples de SLA.

Problemas / divergencias:

- Nao existe `conversation_assignments`.
- Nao existe atribuicao atomica com limite de capacidade.
- Nao existe calculo de SLA por worker.
- Nao existe escalonamento automatico.
- Nao existe visao de ocupacao em tempo real.

Status real sugerido: fundacao de dados/API, sem comportamento operacional.

## P2/P3

Estado geral: majoritariamente nao implementado.

Existe apenas base inicial para:

- Bot configs e capabilities no modelo.
- Dependencia `litellm` no backend.
- Tela `Reports` placeholder.

Nao encontrei implementacao funcional para:

- Bot autonomo / LiteLLM router.
- Copilot de IA.
- Auditoria imutavel e security audit logs.
- Exportacoes operacional/juridica.
- Dashboard analitico.
- Demais canais alem de WhatsApp.
- Pastas/categorizacao.
- Help Center.
- Live Chat.
- Billing/planos/Stripe/uso LLM.
- Campanhas.
- Macros.
- White-label.
- SSO/SAML.
- Permissoes granulares.
- Integracoes de terceiros.

## Bloqueadores tecnicos imediatos

1. Criar migrations Alembic reais para o schema atual.
2. Instalar e validar dependencias locais de backend e frontend.
3. Corrigir contratos frontend/backend para snake_case vs camelCase.
4. Corrigir chamadas quebradas de `send_agent_message` e `persist_inbound_message`.
5. Corrigir create/update/list de Flow para usar um contrato unico (`graph` ou `nodes_data`).
6. Corrigir create/list de ChannelAccount para provider enum e campos de credenciais.
7. Corrigir serializacao de contatos para incluir phones/emails ou mapear no frontend.
8. Aplicar `get_workspace_member`/`require_roles` nas rotas por workspace.
9. Adicionar testes basicos de API para auth, workspace, channel, contact, message e flow.
10. Subir ambiente Docker e validar fluxo real: registrar, criar workspace, criar canal, receber webhook, abrir conversa e responder.

## Escopo recomendado para o proximo ciclo

Objetivo: transformar o P1 fechado no ClickUp em algo realmente executavel.

### Sprint 1 - Fundacao executavel

- Instalar dependencias e documentar setup local.
- Criar migrations Alembic para modelos atuais.
- Corrigir import/start do backend.
- Corrigir type-check/build do frontend.
- Criar seed minimo de workspace/admin.

### Sprint 2 - Contratos API/UI

- Padronizar snake_case/camelCase.
- Corrigir Channels UI/API.
- Corrigir Contacts UI/API.
- Corrigir Flows UI/API.
- Corrigir Messages API.

### Sprint 3 - Inbox WhatsApp ponta a ponta

- Corrigir webhooks Meta/Evolution.
- Persistir inbound message com contato/conversa/idempotencia.
- Enviar mensagem de agente via adapter do provider.
- Validar WebSocket de nova mensagem.
- Adicionar webhook_events duravel ou reabrir tarefa como bloqueador P1.

### Sprint 4 - Permissoes e operacao basica

- Aplicar membership/role nas rotas.
- Finalizar labels/transferencia/timeline basica.
- Criar participantes ou mover para escopo posterior.
- Ajustar status no ClickUp com base no resultado real.

## Conclusao

O escopo do produto esta bem definido em `SCOPE.md` e no ClickUp. O repositorio ja representa uma boa intencao arquitetural, mas ainda nao esta alinhado com o status fechado no ClickUp. A recomendacao e tratar o projeto como MVP em fase de fundacao, reabrindo ou auditando as tarefas fechadas que dependem de migrations, contratos API/UI e fluxo WhatsApp ponta a ponta.
