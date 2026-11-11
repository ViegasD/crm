# CRM2 — Retrato histórico da base integrada

Para escopo e andamento, comece por [Como retomar o CRM2](docs/context/CONTINUIDADE_CRM2.md). Este retrato de 11/11/2026 foi registrado durante a [direção anterior](SCOPE.md). O [relatório de maio](docs/archive/crm/ESCOPO_STATUS_2026-05-21.md) também é histórico.

> Atualizacao de deploy no mesmo dia: a instancia compartilhada esta em `https://hermes-crm2-dev.5tpiot.easypanel.host`, EasyPanel `hermes` / `crm2-dev`. Os bloqueios de build/transporte encontrados foram corrigidos; migrations vazia/local/QA passaram em PostgreSQL descartavel e o novo banco de desenvolvimento chegou ao head. HTTPS, login/API, CRUD de contato, midia, WSS, refresh e tarefa Celery passaram, inclusive apos restart. Isso supera o retrato anterior de Docker indisponivel abaixo. WhatsApp permanece sem pareamento e aceite visual/manual continua pendente. Veja o [relatorio atual de deploy](docs/reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md).

## Implementacao

A base existente ainda e predominantemente CRM/atendimento: autenticacao, workspaces, contatos, equipe, WhatsApp, midia, conversas, timeline, macros, webhooks e capacidade/SLA. Ela pode apoiar o novo produto apos validacao e ajustes.

O dominio de entregas de marketing/e-commerce ainda nao esta implementado: faltam projetos/demandas, etapas operacionais, checklists, revisao/aprovacao e indicadores de entregas.

O merge local `382b97c` integrou `origin/main` em `ca2616d` e a branch QA em `33a02ea`, preservando o trabalho local. Stage 9 existe nessa base integrada; a ausencia identificada na primeira auditoria dizia respeito ao checkout anterior ao fetch. Nenhuma conclusao de producao decorre apenas da existencia desse codigo.

## ClickUp e planejamento

- Chave validada em 11/11/2026; folder correto: `901318283724`.
- Sete listas MVP e 30 tarefas abertas no ultimo retrato verificado.
- As 138 tarefas legadas e 23 listas vazias foram excluidas por solicitacao do usuario, apos backup externo de registros e comentarios.
- Todas as tarefas ativas receberam inicio e vencimento provisorios entre 16/11 e 14/12/2026.
- [Plano, datas e resultado verificado](docs/planning/clickup/).

Nao houve mudanca remota no ClickUp durante a reorganizacao do workspace.

## Validacao tecnica da integracao

Passaram: TypeScript, lint, build Webpack, import/mapeamento backend, OpenAPI, smoke de health, registro Celery e tres testes de regressao. O backend registra 57 tabelas e 110 caminhos OpenAPI. Head Alembic: `202611110001`.

Turbopack falhou por falta de memoria; o build Webpack passou. Docker estava indisponivel: migrations em banco, workers reais, provider WhatsApp e aceite manual nao foram validados. O ambiente herdado `DEBUG=release` precisou de override de processo `DEBUG=false` para as verificacoes backend.

## Pendencias prioritarias

1. Validar as decisoes de fluxo da lista MVP 00.
2. Aplicar autorizacao administrativa por papel e isolamento de upload/presign de midia.
3. Concluir onboarding de usuario sem workspace.
4. Validar/corrigir o historico de migrations em banco descartavel: ha raizes antigas com criacao explicita e `metadata.create_all()`, apesar do head unico.
5. Executar os roteiros manuais de timeline, SLA/capacidade, midia e webhooks antes de fechar stages.
6. Implementar o fluxo integrado de entregas, com requisitos aprovados.

## Evidencias

- [Integracao, limitacoes e testes manuais](docs/reports/INTEGRACAO_VALIDACAO_2026-11-11.md).
- [Auditoria inicial, anterior ao fetch](docs/reports/AUDITORIA_DIRECIONAMENTO_2026-11-11.md).
- [Realinhamento e referencias de fabia](docs/planning/REALINHAMENTO_2026-11-11.md).
- [Registro da exclusao legada](docs/archive/clickup/CLICKUP_LEGACY_DELETION_2026-11-11.json).
