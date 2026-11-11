# CRM2 — code review do PR #1 e plano de realinhamento

Data: 11/11/2026. Revisão auditada: `f6a9a22ab79cf1b8cff9b4bb1c35ed516d8b13ff`, head do [PR #1](https://github.com/ViegasD/crm/pull/1), contra `main` em `ca2616d51487d85f16b5ba21ba8b281e59246e17`.

A revisão foi feita sobre o objeto Git publicado, com leitura estática da árvore e do diff.

## Resultado executivo

- **Reaproveitar:** contatos, contas de canal, conversas, mensagens, eventos/timeline, notificações internas, Redis/Celery, migrações integradas e a base de deploy/smoke.
- **Adaptar:** papéis e onboarding, autorização de conversas privadas, WebSocket, mídia, transferência, replay/deduplicação do WhatsApp, confirmação de envio, relatórios existentes e operação/backup.
- **Implementar para o MVP:** lead/captação, etapas, oportunidades, eventos comerciais, tarefas/lembretes, Kanban paginado e métricas comerciais reconciliáveis.
- **Fora do MVP:** marketing, e-commerce, finanças, comissões, migração integral do legado, histórico retroativo do WhatsApp, IA, campanhas e demais canais.
- **Candidato à retirada:** nenhum componente adicional está comprovado como seguro para remover. O PR é amplo e há dados/migrações/consumidores suficientes para exigir evidência de runtime antes de qualquer retirada.

## Achados prioritários do code review

### Bloqueadores

1. Uniformizar as permissões de conversa privada na listagem, nos detalhes e nas ações.
2. Aplicar o vínculo ativo por workspace e a revogação em sessões de tempo real.
3. Validar o workspace, a propriedade e o vínculo da mídia com uma conversa autorizada.
4. Corrigir a classificação de origem de mensagens na timeline e cobrir o caso de histórico com mensagens.

### Majors

5. **Transferência e atribuição.** Validar o vínculo ativo do destinatário no workspace e preservar a trilha de eventos. Bloqueia o aceite de transferência em M1/M3.

6. **Replay e despacho de webhook ainda não garantem conta por item.** O caminho Meta escolhe o primeiro item no POST inicial; o retry reaplica a única conta gravada ao payload inteiro (`backend/app/webhooks/whatsapp/meta.py:130,256-263`; `backend/app/workers/tasks/webhook_retry.py:82-93,132-146`). Há ainda um caminho legado separado em `backend/app/workers/tasks/webhook.py:94-155`. Efeito no aceite: lotes com dois números, reentrega e histórico podem ser associados à conta errada.

7. **Envio externo ocorre antes de existir correlação local durável.** `backend/app/services/message_service.py:416-440` chama o provedor antes de registrar a identidade; atualizações posteriores dependem de external ID/WAMID já conhecido (`:566-609`). Efeito no aceite: perda de resposta deixa o envio sem estado confirmável; faltam o estado pendente, a correlação e a regra para recibos tardios/fora de ordem.

8. **Transporte worker → navegador não está testado de ponta a ponta.** Redis existe (`backend/app/core/redis.py:1-19`), mas o WebSocket permanece em memória. `backend/tests/test_worker_transport.py:1-13` verifica apenas a construção do transporte Kombu, e `docs/reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md:60` registra a limitação. Efeito no aceite: tarefa Celery e ping WSS não comprovam que uma mudança do worker aparece somente para sessões autorizadas.

9. **O domínio comercial não existe na revisão.** A árvore tem contatos e timeline, mas não contém modelos/rotas de lead, etapa, oportunidade ou métricas comerciais; `backend/app/main.py:58-88` confirma os routers atuais. Efeito no aceite: M2 e M4 são implementação nova apoiada em componentes existentes, não simples configuração.

10. **Operação de produção ainda não está fechada.** A evidência histórica prova desenvolvimento compartilhado, 11 regressões PostgreSQL, migração, smoke, WSS e Celery; não prova WhatsApp real, backup automatizado, restauração, alerta ou rollback (`docs/reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md:35-66`). Efeito no aceite: D05.3/M5 permanece em andamento até evidência própria.

## Matriz de decisão

| Área | Classe | Evidência verificável | Dependências | Efeito no aceite | Natureza da evidência |
| --- | --- | --- | --- | --- | --- |
| Login/JWT/refresh | Reaproveitar | `backend/app/api/v1/auth.py:14-27`; smoke público documentado | Política de cadastro e bootstrap | Mantém entrada existente; cadastro aberto não substitui provisionamento | Estática + histórica |
| Workspace, papéis e equipe | Adaptar | `backend/app/core/dependencies.py:44-118`; `backend/app/api/v1/workspaces.py:16-95` | Matriz de visibilidade, `is_active`, timezone e bootstrap | Bloqueia M1 até administração, revogação e 403/404 estarem coerentes | Estática |
| Conversas privadas e timeline | Adaptar | Revisão dos contratos de acesso e atendimento | Validar autorização em banco descartável e na interface | M1/M3 | Estática + evidências históricas parciais |
| Contatos | Reaproveitar | `backend/app/api/v1/contacts.py:32-151` | Aplicar visibilidade M1 e manter telefone por workspace | Base do cadastro M2 | Estática + smoke histórico de CRUD |
| Lead, oportunidade, funil e tarefas | Implementar/adaptar | Ausentes na árvore; notificações internas existem em `stage9_extras.py:279-334` | M1, migração incremental e contatos | Núcleo de M2 | Estática |
| WhatsApp/inbox | Adaptar | `channel_accounts.py:16-104`; `conversations.py:136-255`; `messages.py:45-60` | Dois números, conta por item, dedupe, confirmação e acesso | Núcleo de M3 | Estática; WhatsApp real não testado |
| Mídia | Adaptar | Revisão dos contratos de acesso e atendimento | Validar autorização em banco descartável e na interface | M1/M3 | Estática + evidências históricas parciais |
| Webhook/replay | Adaptar | `webhook_event_service.py:27-61`; `webhook.py:12-50`; caminhos Meta/retry/legado | Assinatura antes de efeitos, conta validada por item e transação | Bloqueia lote/reentrega de M3 | Estática + persistência histórica |
| Redis/Celery/WebSocket | Adaptar | Revisão dos contratos de acesso e atendimento | Validar autorização em banco descartável e na interface | M1/M3 | Estática + evidências históricas parciais |
| Métricas comerciais | Implementar/adaptar | Página de reports e métricas de SLA existem; router comercial não existe | Eventos M2/M3, timezone e mesma seleção total/detalhe | Núcleo de M4 | Estática |
| Migrações | Reaproveitar com validação | `202611110001_merge_local_and_qa.py`; `test_migration_upgrade.py:1-92` | PostgreSQL descartável e preservação das linhagens conhecidas | Base para M1–M3 | Estática + 11 testes históricos; não executados nesta revisão |
| Deploy, backup e monitoramento | Adaptar | `deploy/README.md:1-47`; relatório de deployment | Ambiente aprovado, destino externo e responsáveis | Bloqueia M5 | Estática + smoke histórico; restauração ausente |
| Marketing/e-commerce/financeiro/IA/campanhas | Fora do MVP | Diagnóstico do legado e decisão do desenho | Nenhuma para o MVP comercial | Não bloqueiam M1–M5 | Decisão de escopo |
| Retirada de código | Sem candidato comprovado | PR altera 154 arquivos e integra migrações/consumidores | Inventário de runtime/dados antes de remover | Evita regressão por “limpeza” | Lacuna de prova |

## Tarefas derivadas nos cinco blocos

As tarefas abaixo reaproveitam os 30 IDs existentes. Status, responsáveis e histórico devem ser preservados; o alinhamento muda nome, descrição, aceite, dependências e janela. Não há exclusão nem comentário.

### M1 · Fundação, acesso e isolamento · 16–18/11

| ID | Tarefa | Aceite | Depende de |
| --- | --- | --- | --- |
| D00.1 | Validar jornadas comerciais reais e corte do legado | Três jornadas acompanhadas; rotinas legadas classificadas | Agência |
| D00.2 | Fechar matriz de papéis, visibilidade e transferência | Matriz admin/operador e individual/compartilhada aprovada | Agência |
| D00.3 | Definir responsáveis de produção, backup e alertas | Executor, destino separado, alerta e rollback nomeados | Ambiente |
| D00.4 | Confirmar dois números, modelos e sinal de anúncio | Evidência sanitizada distingue nova entrada, reentrega e continuidade | Acesso autorizado |
| D00.5 | Manter escopo e aceite do MVP comercial | Cinco blocos e não-objetivos registrados | Decisão já fechada |
| D01.1 | Fixar PR #1 como baseline e inventário de reuso | Hash, diff e matriz deste relatório ligados à tarefa | PR #1 |
| D01.2 | Unificar autorização por workspace e conversa privada | Lista/detalhe/mensagem/timeline/ação/WS respeitam a mesma decisão; 403/404 conforme contrato | D00.2 |
| D01.3 | Proteger upload, vínculo e download de mídia | Ownership, workspace, conversa, TTL e revogação testados; anexos antigos legíveis | D01.2 |
| D01.4 | Concluir onboarding e revogação de operadores | Admin provisiona/desativa; sessão aberta perde acesso; histórico preservado | D00.2 |
| D01.5 | Validar upgrades e migrações incrementais | Banco vazio e linhagens conhecidas sobem sem perda; comandos/evidência registrados | PR #1 |

### M2 · Comercial · 19–25/11

| ID | Tarefa | Aceite | Depende de |
| --- | --- | --- | --- |
| D02.1 | Modelar lead, etapa, oportunidade, evento e tarefa | Invariantes, FKs por workspace e migração incremental implementados | M1 |
| D02.2 | Entregar contatos, captação manual e atividades | CRUD autorizado, origem preservada e atividades auditáveis | D02.1 |
| D02.3 | Decidir e executar somente carga inicial aprovada | Reconciliação explícita ou decisão documentada de não carregar | D02.2 + agência |
| D03.1 | Entregar etapas e oportunidades com estados seguros | active/draining/archived; open/won/lost; arquivo ocupado exige destino | D02.1 |
| D03.2 | Entregar Kanban paginado e filtros coerentes | Mais de 500 itens acessíveis; total, página e busca usam os mesmos filtros | D03.1 |
| D03.3 | Entregar atividades, tarefas e lembretes internos | Conclusão/cancelamento impedem entrega; execução repetida gera uma notificação | D02.1 + notificações existentes |
| D03.4 | Implementar claim, move, close, resume e attribution | Ganho exige vendedor ativo; perda preservada; correção exige motivo e auditoria | D03.1 |
| D03.5 | Testar o fluxo comercial e isolamento | `test_commercial.py` cobre paginação, venda, retomada, atribuição e lembrete | D02.2–D03.4 |

### M3 · WhatsApp oficial · 26/11–02/12

| ID | Tarefa | Aceite | Depende de |
| --- | --- | --- | --- |
| D06.1 | Unificar despacho, identidade, dedupe e replay por conta | Cada item resolve conta ativa antes de efeitos; retry e legado usam o mesmo contrato | D00.4 + M1 |
| D06.2 | Corrigir inbox, transferência, timeline e tempo real | Dois números independentes; destinatário ativo no workspace; timeline funciona; worker aparece só a autorizados | D01.2 + D06.1 |
| D06.3 | Implementar confirmação de envio, janela, modelos e mídia | Estado pendente/confirmado/falho; recibo tardio idempotente; mídia segura | D01.3 + D06.1 |
| D06.4 | Homologar dois números oficiais | Envio, recebimento, filtro, transferência, janela, modelo e falha registrados; histórico retroativo fora do MVP | D06.1–D06.3 + agência |

### M4 · Indicadores verificáveis · 03–08/12

| ID | Tarefa | Aceite | Depende de |
| --- | --- | --- | --- |
| D04.1 | Implementar seleção e cálculos das métricas comerciais | Definição, evento, período, fuso, papel e denominador por indicador | M2 + M3 |
| D04.2 | Expor totais e composição autorizada | `/metrics` e `/metrics/{metric}/records` usam a mesma seleção e total | D04.1 |
| D04.3 | Entregar painel e drill-down | Rótulos distinguem período, estoque, conversão, ganho e valor vendido | D04.2 |
| D04.4 | Reconciliar métricas com casos sintéticos | Total, numerador, denominador e detalhe batem com fuso e permissão | D04.1–D04.3 |

### M5 · Homologação e produção · 09–14/12

| ID | Tarefa | Aceite | Depende de |
| --- | --- | --- | --- |
| D05.1 | Executar QA integrado dos fluxos do MVP | Jornada completa, erros visíveis, isolamento e não duplicação | M1–M4 |
| D05.2 | Executar suíte, frontend e roteiro desktop/mobile | Backend, type-check, lint, build e roteiro registrados separadamente | D05.1 |
| D05.3 | Publicar com backup, restauração, alertas e rollback | Backup automatizado separado; restauração e alerta reais; rollback exercitado | D00.3 + D05.2 |
| D05.4 | Homologar com a agência e registrar aceite | Evidência técnica, evidência manual, pendências e corte operacional assinados | D05.1–D05.3 |

## Evidência e limites da revisão

- **Teste executado nesta revisão:** nenhum. A instrução foi revisar a árvore Git sem alterar o checkout; executar a suíte contra `33a02ea` não validaria o PR #1.
- **Teste histórico verificável no PR:** 11 regressões PostgreSQL, migração a `202611110001`, build Webpack, type-check/lint, smoke HTTP/API, upload/presign, WSS ping/pong, token refresh e tarefa Celery, conforme `docs/reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md`.
- **Não comprovado:** WhatsApp com dois números reais, replay multi-conta, autorização por objeto privado, mídia entre workspaces, worker→browser autorizado, backup automatizado, restauração, alerta e rollback.
- **Revisão independente:** o inventário factual foi concluído. A leitura Goldfish enviou achados parciais sobre autorização, mídia, replay, confirmação e transporte. O revisor foi interrompido antes do relatório final.

## Resultado aplicado no ClickUp

Pasta CRM2 no ClickUp, conferida e atualizada pela API oficial após a conclusão da matriz e do plano acima.

- Sete listas preservadas e renomeadas para: dependências/aceite, M1, M2A, M2B, M4, M5 e M3.
- Trinta tarefas existentes reaproveitadas; nenhuma tarefa ou lista criada ou excluída.
- Cada tarefa preservou a descrição anterior e recebeu a seção `Realinhamento MVP comercial - 11/11/2026` com bloco, objetivo, aceite, dependências, evidência e hash auditado.
- Datas alinhadas às janelas do desenho: M1 `16–18/11`, M2 `19–25/11`, M3 `26/11–02/12`, M4 `03–08/12` e M5 `09–14/12/2026`.
- Status preservados: `D00.5` continua `Closed`; `D01.5` e `D05.3` continuam `in progress`; as demais continuam `Open`.
- Responsáveis preservados: nenhuma das 30 tarefas tinha responsável na leitura anterior ou posterior.
- Nenhum comentário foi publicado. Histórico e evidências anteriores foram mantidos no corpo das tarefas.
