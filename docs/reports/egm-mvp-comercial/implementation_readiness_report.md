# EGM 9 · Prontidão de implementação

Alvo: crm2_mvp_comercial.md, linhas 249–356. Readiness, codebase-details e style concluíram. Sol low substituiu Luna para style. O revisor de código conferiu a cadeia e os caminhos existentes na árvore Git f6a9a22, sem executar o projeto. Todos os arquivos marcados para alteração que já deveriam existir estão presentes. O trecho ainda não atende ao critério de execução sem decisões de desenho.

| ID | Persona | Severidade | Linhas | Achado |
| --- | --- | --- | --- | --- |
| 9-R1 | Readiness | Blocker | 275–286, 292–298 | Fixar head de partida, colunas, restrições, valores iniciais e migração por linhagem, com asserções de preservação. |
| 9-R2 | Readiness | Major | 276–284, 295–296 | Definir rotas, métodos, campos, paginação, erros, transições, matriz de acesso e revogação observável de WebSocket. |
| 9-R3 | Readiness | Blocker | 309–314, 320 | Provar antes de M3 os sinais do anúncio, versão, mapeamento, chave de deduplicação, ausência de campos e comportamento no retry. |
| 9-R4 | Readiness | Major | 326–329, 344 | Definir campos de origem, limites do intervalo, fuso, ordenação e resultados esperados dos indicadores. |
| 9-R5 | Readiness | Blocker | 335–338, 345 | Definir componentes, executor, agendamento, destino do backup, restauração, alertas e gatilho de reversão. |
| 9-R6 | Readiness | Major | 257–265, 340–346 | Associar comandos, preparação de dados, asserções e evidência a cada bloco. |
| 9-C1 | Codebase | Major | 278–285, 313 | Lista considera conversa privada; consulta direta, mensagens e timeline exigem a política equivalente já em M1. Evidência em backend/app/services/conversation_service.py:15–21,102–115; backend/app/api/v1/messages.py:23–70; backend/app/services/timeline_service.py:241–290. |
| 9-C2 | Codebase | Major | 279, 284 | A equipe só lista e remove membros. Cadastro público cria conta, e conta autenticada pode criar workspace. Decidir provisionamento e bootstrap. Evidência em backend/app/api/v1/workspaces.py:16–29,57–95; backend/app/services/auth_service.py:55–62. |
| 9-C3 | Codebase | Major | 280, 298, 318 | Worker separado chama um gerenciador WebSocket em memória. Fixar transporte, destinatários e revogação. Evidência em backend/app/websocket/manager.py:11–37; backend/app/services/webhook_retry.py:132–146; backend/tests/test_worker_transport.py:9. |
| 9-C4 | Codebase | Major | 281, 285 | Mídia sobe antes de existir vínculo com conversa. A serialização também emite URL. Definir propriedade temporária, vínculo, autorização e validade. Evidência em backend/app/api/v1/media.py:37–60; backend/app/schemas/message.py:47–63; frontend/src/components/inbox/reply-box.tsx:192. |
| 9-C5 | Codebase | Major | 297–298, 300 | O notificador usa sessão própria e pode acionar canais externos; falta chave por ocorrência. Definir contrato reutilizado, periodicidade e operação idempotente. Evidência em backend/app/services/notifier.py:39–108; backend/app/models/stage9_extras.py:109–137; backend/app/api/v1/stage9_extras.py:281–307. |
| 9-C6 | Codebase | Major | 310, 314, 317 | Meta autentica e persiste lote a partir da primeira conta. Retry reaplica a conta a todos os itens. Incluir webhook_event_service.py e definir autenticação, unidade persistida e histórico. Evidência em backend/app/webhooks/whatsapp/meta.py:130–141,179–204,245–263; backend/app/services/webhook_retry.py:82–110,132–146. |
| 9-C7 | Codebase | Major | 311–313, 317 | O fluxo cria ou reabre conversa antes de deduplicar. A abertura atual registra ator system. Incluir conversation_service.py e timeline_service.py e explicitar os eventos. Evidência em backend/app/services/message_service.py:295–308; backend/app/services/timeline_service.py:193–230; backend/app/services/conversation_service.py:170–214,224–264. |
| 9-C8 | Codebase | Major | 335–337, 345 | Smoke fixa o ambiente de desenvolvimento. O registro mostra backup manual local. Especificar seleção do ambiente e rotina de backup e alerta. Evidência em deploy/smoke_development.py:9–28; docs/reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md:50–52. |
| 9-S1 | Style | Major | 260, 293, 295, 329 | Explicitar nomes canônicos e mapeamento entre lead/captação e negócio/oportunidade. |
| 9-S2 | Style | Major | 276, 280 | Nomear o campo que aceita herdar e explicitar o resultado da revogação em uma sessão conectada. |
| 9-S3 | Style | Nit | 296, 303 | Padronizar a descrição do arquivamento de etapa com remanejamento. |
| 9-S4 | Style | Nit | 320 | Mover limites de coexistência e histórico para o critério de aceite ou para fora de escopo. |
