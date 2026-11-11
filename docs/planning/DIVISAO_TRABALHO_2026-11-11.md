# Divisao de trabalho e sequencia - 11/11/2026

Divisao confirmada pelo usuario: **Fabio: backend/deploy; Thiago: frontend**. Marketing e e-commerce fazem parte do MVP; comercial permanece secundario. O novo contexto remoto `aaf08df` tambem inclui marketing/e-commerce. Nao reabrir essa decisao nem apagar os achados tecnicos da auditoria.

## Sequencia e limites

1. Fabio corrige inconsistencias de autorizacao, midia, timeline/busca/transferencia, webhook, envio e transporte. Thiago valida jornadas e direcao visual em UI01 e prepara a base visual em UI02.
2. AUD08 libera integracao funcional somente com contratos e regressoes verificadas. UI nao deve simular sucesso para APIs ausentes ou inseguras.
3. Fabio entrega os dominios e APIs de clientes/servicos, marketing e e-commerce. Thiago integra as telas nas tarefas existentes e UI10.
4. API01 entrega indicadores de entregas para D05.1. QA de frontend, backend e aceite manual ficam registrados separadamente.
5. Fabio publica pelo EasyPanel com backup/restauracao/alerta/rollback; homologacao conjunta com agencia. WhatsApp permanece sem pareamento ate autorizacao.

**Datas provisorias:** alvo de 16/11 a 14/12/2026; fins de semana e 20/11 excluidos. A ampliacao de auditoria e rework exige reestimativa em UI01/AUD08, sem garantia de caber na janela original. Datas foram reorganizadas para priorizar estabilizacao; nao representam capacidade ja estimada.

## Contrato de colaboracao

- Fabio edita `backend/`, migrations, contratos OpenAPI, workers e `deploy/`. Thiago edita `frontend/`, incluindo `src/lib/api.ts`, tipos, stores e UI. Mudancas de contrato sao combinadas antes da integracao.
- Cada tarefa tem um responsavel e o outro como revisor no texto; revisar nao adiciona um segundo assignee nem representa revisao ja executada.
- Usar uma branch por tarefa e PR pequeno. Nao misturar redesign com alteracoes de schema. Nao editar a branch do outro nem incorporar trabalho local nao publicado sem combinacao.
- Os 30 IDs existentes sao preservados. Tarefas de produto com frontend novo dependem dos contratos entregues por Fabio; o responsavel pela tela nao passa a ser dono do backend.
- Nenhum status existente e encerrado/reaberto automaticamente. Aceite exige commit, comandos/resultados e verificacao manual quando indicada.
- D05.2 registra separadamente `npm run type-check`, `npm run lint`, `npm run build -- --webpack`, testes de comportamento dos fluxos alterados e roteiro real desktop/mobile. Build nao substitui autorizacao, interacao por teclado, persistencia apos recarga ou integracao entre processos. AUD08 fornece os resultados backend, sem usar o banco compartilhado como banco de teste.

## Inventario base

Ver [cobertura backend/frontend](../reports/BACKEND_FRONTEND_COVERAGE_2026-11-11.md). A evidencia e leitura estatica da base publicada `f6a9a22` e do checkout local com correcoes ainda nao publicadas; nao equivale a homologacao visual.

## Tarefas e responsaveis

| Codigo | Responsavel | Entrega | Janela provisoria |
| --- | --- | --- | --- |
| D00.1 | Fabio | Validar fluxo real de marketing e e-commerce | 11-16 a 11-18 |
| D00.2 | Fabio | Definir revisao interna, aprovacao e acesso do cliente | 11-16 a 11-18 |
| D00.3 | Fabio | Definir recorrencia, prazos, anexos e notificacoes | 11-16 a 11-18 |
| D00.4 | Fabio | Decidir papel do WhatsApp no MVP | 11-16 a 11-18 |
| D00.5 | Fabio | Alinhar escopo, proposta e criterios de aceite | 11-16 a 11-18 |
| D01.1 | Fabio | Integrar e validar checkout com branches remotas | 11-16 a 11-17 |
| D01.2 | Fabio | Aplicar papeis e isolamento em operacoes administrativas | 11-16 a 11-19 |
| D01.3 | Fabio | Corrigir autorizacao de upload e download de midia | 11-16 a 11-19 |
| D01.4 | Fabio | Concluir onboarding e gerenciamento de equipe | 11-19 a 11-23 |
| D01.5 | Fabio | Validar migrations em banco vazio e banco existente | 11-16 a 11-18 |
| D02.1 | Fabio | Modelar clientes, servicos e vinculos operacionais | 11-26 a 11-27 |
| D02.2 | Thiago | Entregar cadastro e consulta de clientes e servicos | 11-30 a 12-01 |
| D02.3 | Fabio | Definir e executar carga inicial de clientes | 11-30 a 12-01 |
| D03.1 | Fabio | Modelar demandas, etapas e regras de transicao | 11-26 a 11-27 |
| D03.2 | Thiago | Entregar criacao, atribuicao e Kanban de demandas | 11-30 a 12-02 |
| D03.3 | Thiago | Adicionar comentarios, anexos e historico de demanda | 12-03 a 12-03 |
| D03.4 | Fabio | Entregar revisao, ajustes, aprovacao e conclusao | 11-30 a 12-02 |
| D03.5 | Fabio | Validar recorrencia e alertas operacionais de marketing | 12-03 a 12-04 |
| D04.1 | Fabio | Modelar projetos, marcos e checklists de e-commerce | 11-30 a 12-02 |
| D04.2 | Thiago | Entregar painel de projeto e execucao de checklist | 12-03 a 12-04 |
| D04.3 | Thiago | Vincular evidencias, revisao e entrega do projeto | 12-07 a 12-08 |
| D04.4 | Fabio | Homologar um projeto real de e-commerce | 12-09 a 12-10 |
| D05.1 | Thiago | Entregar indicadores operacionais de entregas | 12-08 a 12-09 |
| D05.2 | Thiago | Executar QA integrado e isolamento por papel/workspace | 12-10 a 12-11 |
| D05.3 | Fabio | Preparar deploy, backup, armazenamento e monitoramento | 11-26 a 12-11 |
| D05.4 | Fabio | Homologar MVP com agencia e registrar aceite | 12-14 a 12-14 |
| D06.1 | Fabio | Mapear reuso WhatsApp de fabia para CRM2 | 11-16 a 11-18 |
| D06.2 | Fabio | Validar envio, webhooks e isolamento por numero | 11-26 a 11-27 |
| D06.3 | Fabio | Implementar regras de entrega, erros e midia necessarias | 11-30 a 12-02 |
| D06.4 | Fabio | Validar coexistencia e historico se aprovados | 12-03 a 12-04 |
| AUD01 | Fabio | Unificar autorizacao privada, papeis e revogacao | 11-16 a 11-18 |
| AUD02 | Fabio | Proteger ownership, vinculo e acesso de midia | 11-16 a 11-19 |
| AUD03 | Fabio | Corrigir timeline, busca e destinatarios de transferencia | 11-16 a 11-18 |
| AUD04 | Fabio | Unificar webhook, conta por item, dedupe e replay duravel | 11-19 a 11-23 |
| AUD05 | Fabio | Persistir correlacao de envio e recibos idempotentes | 11-19 a 11-24 |
| AUD06 | Fabio | Entregar transporte worker para browser com isolamento | 11-19 a 11-24 |
| AUD07 | Fabio | Corrigir contratos de autenticacao e Flows existentes | 11-16 a 11-18 |
| AUD08 | Fabio | Validar baseline corrigida e liberar integracao funcional | 11-24 a 11-25 |
| API01 | Fabio | Implementar API e reconciliacao dos indicadores de entregas | 12-03 a 12-07 |
| UI01 | Thiago | Validar jornadas e direcao visual do frontend completo | 11-16 a 11-18 |
| UI02 | Thiago | Reconstruir shell, navegacao e componentes compartilhados | 11-19 a 11-23 |
| UI03 | Thiago | Refazer login, perfil, onboarding e equipe por papel | 11-26 a 11-27 |
| UI04 | Thiago | Refazer contatos e timeline com contratos validados | 11-26 a 11-30 |
| UI05 | Thiago | Refazer inbox e integrar capacidades existentes sem UI | 11-30 a 12-03 |
| UI06 | Thiago | Integrar central de notificacoes e leitura | 11-26 a 11-30 |
| UI07 | Thiago | Refazer settings e expor administracao e diagnosticos faltantes | 11-30 a 12-03 |
| UI08 | Thiago | Alinhar UI do Flow Builder e tornar indisponibilidade explicita | 12-04 a 12-07 |
| UI09 | Thiago | Refazer supervisor e preservar indicadores existentes verificaveis | 12-07 a 12-09 |
| UI10 | Thiago | Integrar revisao, ajustes, aprovacao e conclusao de marketing | 12-04 a 12-07 |

32 tarefas com Fabio e 17 com Thiago; quantidade nao mede esforco. Rework visual e integracao concentram-se nas tarefas maiores de Thiago. Reavaliar carga e datas ao fechar UI01/AUD08.

Plano estruturado e dependencias: [CLICKUP_OWNERSHIP_PLAN](clickup/CLICKUP_OWNERSHIP_PLAN_2026-11-11.json). Resultado verificado da aplicacao: `clickup/CLICKUP_OWNERSHIP_RESULT_2026-11-11.json` (apos execucao).
