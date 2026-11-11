# CRM2 - Escopo e status real do projeto

> **Nota de 11/11/2026:** o retrato abaixo e historico, datado de maio. O MVP mudou para entregas de marketing/e-commerce. A chave ClickUp atual e valida e o folder correto e `901318283724`. A consulta inicial teve 138 tarefas legadas, posteriormente excluidas a pedido do usuario apos backup externo. A trilha ativa tem 30 tarefas em sete listas MVP, com inicio escolhido em 16/11 e fim provisorio em 14/12/2026. O fetch encontrou trabalho remoto Stage 3/4/9 ausente do checkout inicialmente auditado, integrado no merge local `382b97c`. Consulte `docs/REALINHAMENTO_2026-11-11.md` e `docs/INTEGRACAO_VALIDACAO_2026-11-11.md` antes de usar os diagnosticos abaixo como estado atual.

Data da auditoria: 2026-05-21

## Fonte usada

- Repositorio local: `C:\Users\fabio\Work\crm2`
- Documento de escopo local: `SCOPE.md`
- ClickUp: pasta `CRM2` no espaco `viponline`
- Validacao local: leitura de codigo, inventario de rotas/modelos, migrations e chamadas reais aos endpoints locais

## Observacao sobre o ClickUp

Nao foi possivel revalidar o estado live do ClickUp via API nesta auditoria.

- O token embutido em `scripts/clickup_close_done.ps1` retorna `OAUTH_025 Token invalid`.
- Portanto, os status abaixo combinam:
  - o ultimo retrato local ja documentado do folder `CRM2`
  - a validacao atual do repositorio e do ambiente local

Em outras palavras: este arquivo foi atualizado para refletir o estado real do codigo hoje, mas nao confirma se todos esses avancos ja foram marcados manualmente no ClickUp.

## Resumo executivo

O projeto deixou de ser apenas um esqueleto inicial e hoje ja tem uma base local funcional para P1, com varios pontos que o documento anterior marcava incorretamente como ausentes.

Estado atual confirmado no repositorio:

- Backend FastAPI com auth, usuarios, workspaces, setores, canais, contatos, conversas, mensagens, labels, canned responses, fluxos, SLA, midia, webhooks e WebSocket.
- Migrations Alembic reais em `backend/migrations/versions`, incluindo `webhook_events`, `canned_responses` e merge de heads.
- `webhook_events` implementado com persistencia duravel e replay via worker Celery.
- `security_audit_service` implementado e usado em labels, canned responses, transferencias e webhooks.
- Frontend e backend validados localmente para requests-chave de workspace (`labels`, `channels`, `conversations`).
- Correcao do fluxo de criacao de canais no frontend/backend local.

Ainda assim, o produto continua parcial. Os principais gaps atuais sao:

- Registro ainda cria usuario sem workspace automaticamente.
- Nao existe onboarding consistente para criacao/gestao de workspace no frontend.
- Envio de mensagem do agente ainda salva no banco, mas nao esta integrado ponta a ponta ao provider WhatsApp.
- Flow builder, capacidade/SLA operacional e grande parte de P2/P3 continuam incompletos.
- O status live das tarefas no ClickUp nao foi reconsultado nesta rodada por falha de token.

## Status ClickUp

Ultimo retrato local registrado para a pasta `CRM2`:

- 22 listas
- 93 tarefas
- 20 fechadas
- 73 abertas

Ultimo retrato local por area:

- P1 Stage 1 fechado no ClickUp.
- P1 Stage 2 quase inteiro fechado no ClickUp.
- Parte de P1 Stage 3 fechada no ClickUp.
- Demais stages majoritariamente abertos.

Atualizacao desta auditoria:

- O repositorio agora sustenta mais trabalho entregue do que o documento anterior reconhecia em Stage 2, Stage 3 e Stage 4.
- Nao foi possivel confirmar se esse progresso ja foi refletido nas tarefas live do ClickUp.

## Comparativo por area

### P1 Stage 1 - Auth + Workspace + Setorizacao

ClickUp: ultimo retrato local indicava fechado. Status live nao revalidado.

Codigo existente:

- `users`, `workspaces`, `user_workspace_memberships`, `sectors`, `sector_members`.
- JWT access/refresh.
- Login e registro.
- CRUD basico de workspaces, membros e setores.
- `require_workspace_member` e `require_roles`.
- `MembershipOut` inclui dados inline do usuario (`name`, `email`, `avatar_url`).

Problemas / divergencias:

- Registro ainda cria usuario sem criar workspace/membership automaticamente.
- Nao existe fluxo de onboarding consistente para usuario sem workspace.
- Nao existe UI madura para criar workspace e convidar membros no fluxo principal do produto.
- Enforcement por role ainda nao esta aplicado de forma abrangente em todo o backend.

Status real sugerido: backend base implementado e funcional, mas experiencia de produto ainda parcial.

### P1 Stage 2 - Canal WhatsApp + Inbox Unificado

ClickUp: ultimo retrato local indicava quase fechado. Status live nao revalidado.

Codigo existente:

- Modelos de `channel_accounts`, `channel_credentials`, `conversations`, `messages`, `message_identities`.
- Adapters Meta Cloud e Evolution.
- Webhooks Meta e Evolution.
- Inbox com lista, thread, reply box e WebSocket.
- CRUD de contatos.
- Upload/presigned URL de midia.
- Worker Celery para replay de `webhook_events`.
- `webhook_events` implementado com migration e status de processamento.

Validacao local recente:

- `GET /api/v1/workspaces/{id}/labels` respondeu `200`.
- `GET /api/v1/workspaces/{id}/channels` respondeu `200`.
- `GET /api/v1/workspaces/{id}/conversations?status=open&page_size=50` respondeu `200`.
- Instancia Evolution local `test` foi configurada com webhook valido para o backend local.

Problemas / divergencias:

- O envio de mensagem do agente ainda grava mensagem no CRM, mas nao faz dispatch real para o provider WhatsApp.
- A operacao local depende de seed/manual setup de workspace e canal para ficar utilizavel.
- Ainda ha risco de inconsistencias em outros contratos nao revalidados ponta a ponta nesta auditoria.

Status real sugerido: implementacao parcial forte, com ingestao e leitura funcionais localmente; envio outbound ainda incompleto.

### P1 Stage 3 - Acoes de Conversa Basicas

ClickUp: ultimo retrato local indicava transferencia e etiquetas fechadas; canned responses, participantes e timeline abertos. Status live nao revalidado.

Codigo existente:

- Transferencia de conversa com `conversation_event`.
- Labels e `conversation_labels`.
- Endpoints de participantes de conversa.
- Endpoints de eventos de conversa.
- `canned_responses` existe em modelo, API e migration.
- Logs de auditoria em labels, transferencias e canned responses.

Problemas / divergencias:

- Participantes e timeline existem no backend, mas ainda precisam validacao/UI madura no frontend.
- `canned_responses` estava faltando no banco local e precisou de migration corretiva nesta rodada.
- O stage nao pode ser tratado como completamente pronto sem validacao integrada de UX.

Status real sugerido: avancou alem do retrato anterior; labels e transferencia prontas no backend, canned responses implementado, participantes/timeline presentes em API mas ainda parciais no produto.

### P1 Stage 4 - Seguranca de Webhooks

ClickUp: ultimo retrato local indicava aberto. Status live nao revalidado.

Codigo existente:

- Meta verifica HMAC.
- Evolution verifica assinatura.
- Timestamp verification e anti-replay por Redis.
- `webhook_events` duravel com persistencia propria.
- `security_audit_service` e `SecurityAuditLog` usados nos webhooks.
- Replay de eventos recebidos via Celery.

Problemas / divergencias:

- Precisa validacao mais ampla de cobertura e operacao em producao.
- Rotacao de secret e alguns detalhes de hardening ainda nao estao claramente fechados como produto.

Status real sugerido: significativamente mais avancado do que o documento anterior; nao concluido, mas nao mais apenas iniciado.

### P1 Stage 5 - Flow Builder

ClickUp: aberto.

Codigo existente:

- Modelos `flows` e `flow_executions`.
- Tela/lista de fluxos.
- Integracao parcial com execucao de fluxo ao persistir mensagem inbound.

Problemas / divergencias:

- O builder ainda nao esta validado como fluxo ponta a ponta de producao.
- Persistem riscos de contrato e de configuracao dos nos.
- O stage continua parcial.

Status real sugerido: iniciado/parcial.

### P1 Stage 9 - Capacidade + SLA

ClickUp: aberto.

Codigo existente:

- Modelos `sla_policies`, `sla_events`, `agent_capacity`.
- CRUD basico de politicas de SLA.
- Base de capacidade e UI simples de SLA.

Problemas / divergencias:

- Nao ha fluxo operacional completo de atribuicao atomica e ocupacao em tempo real.
- Nao ha escalonamento automatico validado ponta a ponta.
- Continua como fundacao de dados/API, nao como feature operacional pronta.

Status real sugerido: parcial.

## P2/P3

Estado geral: majoritariamente aberto ou apenas iniciado.

Existe base inicial para:

- Bot configs e capabilities no modelo.
- Dependencia `litellm` no backend.
- Reports placeholder.

Ainda nao ha validacao funcional suficiente para fechar como entregue:

- Bot autonomo / LiteLLM router.
- Copilot de IA.
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

## Tarefas do folder CRM2 com mudanca clara desde a auditoria anterior

Estas frentes tiveram avancos concretos no repositorio e devem ser revisadas/atualizadas no ClickUp quando houver token valido:

- P1 Stage 2 - Tabela `webhook_events` / ingestao duravel.
- P1 Stage 2 - Correcoes do fluxo de canais WhatsApp no frontend/backend.
- P1 Stage 3 - Mensagens pre-escritas (`canned_responses`).
- P1 Stage 4 - Seguranca de webhooks com audit log e replay/anti-replay.
- Dev tooling local (`dev-backend.ps1`, `dev-frontend.ps1`, seed local, `.env.local`).

## Bloqueadores tecnicos imediatos

1. Obter token ClickUp valido para reconciliar o folder `CRM2` com o estado real do repositorio.
2. Fechar o fluxo de registro/onboarding para que usuario nao fique sem workspace.
3. Integrar envio outbound do agente ao provider WhatsApp.
4. Consolidar e validar o fluxo de migrations para evitar novos desvios schema vs codigo.
5. Validar frontend para participantes, timeline e canned responses de ponta a ponta.
