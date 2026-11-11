# Cobertura backend/frontend — 11/11/2026

Inventário para dividir trabalho, não certificado de funcionamento. Base publicada auditada: `f6a9a22`. O checkout local contém correções de segurança ainda não publicadas; o contexto remoto mais recente `aaf08df` altera documentação, sem implementar as correções. O split confirmado é Fabio backend/deploy, Thiago frontend.

## Cobertura observada

| Área | Backend | Frontend | Trabalho vinculado |
| --- | --- | --- | --- |
| Auth/perfil/workspace/equipe | Login, refresh, perfil, workspace, membros; onboarding/provisionamento/revogação incompletos | Login e listagem/remoção de equipe; sem jornada completa de provisionamento/edição de perfil | D01.4, UI03, AUD01/AUD07 |
| Contatos/timeline | CRUD e timeline existem; enum inválido quebra timeline com mensagens; autorização privada precisa unificação | CRUD e timeline já possuem telas; rework deve preservar funcionalidades | AUD01/AUD03, UI04 |
| Setores e canais | CRUD, membros de setor e edição de canal existem; validar RBAC e escopo | Setores têm criação/listagem/remoção; add/remove de membros e edição de canal são candidatos a integração faltante | AUD01, UI07 |
| Inbox | Listagem, filtros por conta, views, bulk actions, envio, anexos e eventos existem; há falhas de autorização, busca, transferência e envio | Inbox/mentions/timeline já existem. Lista pede somente 50 itens; não possui filtro de conta na consulta observada. Views listadas, sem consumidor direto para create/update/delete; bulk transfer/participantes sem consumidor direto | AUD01–AUD06, UI05 |
| Mídia | Upload/presign/storage existem; prefixo de key e membership não bastam para ownership/conversa privada/revogação | Anexos existem. Falta fechar jornada segura; ausência de consumidor de presign não prova, isoladamente, ausência de download | AUD02, UI04/UI05 |
| Notificações | `/notifications` e `/notifications/read` existem | Wrappers `listNotifications`/`markNotificationsRead` sem consumidor direto; badge de mentions é outro recurso | UI06 |
| Catálogos/macros/SLA/calendários | Endpoints existem, incluindo categorias, capacidade, horários, routing, feriados e regras | Há diversas telas em settings/operations. Não reconstruir como se tudo estivesse ausente; verificar edições pontuais e diagnósticos faltantes | UI07 |
| Webhook/integrações | Retry, ops, attempts e deliveries existem, mas replay multi-conta e durabilidade precisam correção | Telas de webhook events/ops existem; wrappers listAttempts/listApiWebhookDeliveries sem consumidor direto | AUD04, UI07 |
| Supervisor/CSAT/heatmap | APIs existem; valores e permissões precisam validação | Supervisor já existe; rework deve preservar e reconciliar os indicadores existentes | UI09 |
| Reports | Não existem métricas do novo domínio de entregas | `reports/page.tsx` retorna somente `<div>Reports</div>` | API01, D05.1 |
| Flows | Contrato publicado usa `nodes_data` enquanto handler usa `body.graph`; retorno/active e conta precisam alinhamento. Executor ausente | Editor/lista existem; tipo `isActive` diverge de `active` do backend; não apresentar ativação falsa | AUD07, UI08 |
| Clientes/serviços de entrega | Novo domínio ainda ausente; contatos não equivalem a clientes/serviços operacionais | Sem telas do novo domínio | D02.1/D02.2 |
| Marketing | Demandas/etapas/revisão/aprovação ainda precisam modelos, APIs e regras aprovadas | Sem módulo de entregas | D03.1–D03.5, UI10 |
| E-commerce | Projetos/checklists/evidências ainda precisam modelos e APIs | Sem módulo de projetos de e-commerce | D04.1–D04.4 |

## Evidência e limites

- Rotas conferidas em `backend/app/main.py`, `backend/app/api/v1/catalog.py`, `stage9_extras.py`, `sla.py`, `contacts.py`, `conversations.py`, `flows.py` e demais routers.
- Frontend conferido em `frontend/src/lib/api.ts`, páginas em `frontend/src/app/(dashboard)/`, `components/inbox/`, `components/settings/` e `types/flow.ts`.
- A busca de consumidores percorreu `.ts/.tsx` fora de `lib/api.ts`, procurando `objetoApi.metodo`. É uma indicação estática: aliases, acesso indireto ou mudanças posteriores exigem conferir cada candidato antes de implementar. Wrapper de API não comprova UI nem endpoint correto.
- A revisão do colaborador declara não ter executado testes. A rodada local de 11 testes de comportamento em PostgreSQL descartável terminou com 10 passando e 1 falhando por `label: null` adicional no round-trip do grafo. Isso não comprova a suíte completa nem as correções de ownership, revogação contínua ou replay.
- Browser/fluxos reais não foram homologados nesta rodada. A verificação anterior de deploy cobre smoke de API, mídia, refresh, WSS ping e Celery separadamente, não prova worker→browser autorizado nem WhatsApp real.

## Critério para expor uma capacidade existente

Confirmar contrato, permissão, erro e persistência no backend; integrar a ação real no frontend com loading/empty/error; testar dados em mais de uma página, dois workspaces e papéis diferentes; registrar evidência em commit/PR e tarefa. Não implementar telas de sucesso fictício para APIs ausentes.
