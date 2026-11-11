# Realinhamento do CRM2 - 11/11/2026

> Decisao posterior do usuario: excluir tarefas legadas e definir datas com inicio em 16/11/2026. A preservacao descrita abaixo registra a primeira etapa; a exclusao autorizada tem backup externo e registro em `docs/archive/clickup/CLICKUP_LEGACY_DELETION_2026-11-11.json`. A trilha ativa passa a conter apenas as sete listas MVP, com 30 tarefas. Cronograma provisorio de 20 dias uteis: 16/11 a 14/12/2026, conforme `docs/planning/clickup/CLICKUP_SCHEDULE_2026-11-11.json`.

## Diretriz e organizacao do trabalho

Confirmado pela conversa de 09/11: priorizar gestao de entregas de marketing e e-commerce; comercial fica em segundo plano. O usuario autorizou reorganizar ClickUp e integrar trabalho remoto em 11/11.

O plano `docs/planning/clickup/CLICKUP_DELIVERY_PLAN_2026-11-11.json` preserva as 23 listas existentes com prefixo `[LEGADO CRM]`, sem apagar tarefas ou mudar seus estados. Cria sete listas e 30 tarefas com codigos estaveis, criterios de aceite e dependencias documentadas. As tarefas novas ficam abertas; nao recebem prazo ou responsavel presumido. O resultado com IDs/URLs sera salvo em `docs/planning/clickup/CLICKUP_REWORK_RESULT_2026-11-11.json`.

As listas sao: MVP 00 diretriz/validacao; MVP 01 fundacao/seguranca; MVP 02 clientes/servicos; MVP 03 marketing; MVP 04 e-commerce; MVP 05 painel/homologacao/producao; MVP 06 WhatsApp condicionado ao fluxo. O detalhamento do handoff continua proposto ate validacao das tarefas D00. Portal de cliente, recorrencia, regras de aprovacao e WhatsApp nao se tornam compromissos por constarem no backlog.

Decisao operacional: manter o historico e adicionar trilha nova no mesmo folder CRM2. Substituir ou excluir tarefas antigas perderia rastreabilidade; manter as duas trilhas sem rotular a antiga perpetuaria prioridades conflitantes. O fechamento continua condicionado a implementacao integrada, validacao tecnica e aceite manual quando necessario.

## Atualizacao importante da auditoria anterior

A auditoria inicial avaliou apenas o checkout entao disponivel. O fetch posterior encontrou `origin/main` em `ca2616d` (tres commits remotos novos, um commit local exclusivo) e `origin/codex/stage-3-4-9-qa` em `33a02ea`. A branch QA contem os commits novos de main, `sla_service.py`, workers SLA, `ConversationAssignment`, supervisor, migrations e timeline/reabertura. Assim, as divergencias Stage 9 eram reais no checkout auditado, mas nao demonstram ausencia do trabalho no repositorio remoto. Nao reabrir tarefas apenas com base nessa ausencia local; validar a branch integrada e os criterios de aceite.

O usuario autorizou integrar as mudancas necessarias preservando trabalho local. O registro de integracao/validacao deve identificar os commits e manter separados disponibilidade do codigo, verificacao tecnica e aceite manual. A existencia da branch QA nao comprova funcionamento em producao.

## Referencias WhatsApp em Work/fabia

Checkout de referencia inspecionado: `C:/Users/fabio/Work/fabia`, commit local `c0bb817`. Nao foi atualizado nem modificado. O AGENTS.md desse projeto foi lido. Nenhum segredo, banco ou dado de cliente foi importado.

| Referencia local em fabia | Padrao reutilizavel | Adaptacao para CRM2 |
| --- | --- | --- |
| `server/app/official_whatsapp_client.py` | `MetaAPIError`, classificacao transitoria/permanente, Retry-After, timeout, leitura de midia limitada | Preservar adapters/httpx do CRM2; separar erros de provider e politica de retry, sem copiar stack aiohttp por inercia |
| `server/app/whatsapp_security.py` | HMAC em bytes originais, comparacao constante, digest de verify token | Aproveitar testes e regras aplicaveis por channel/workspace; nao copiar restricao de grupos de fabia para CRM2 automaticamente |
| `server/app/routers/official_whatsapp_webhook.py` | Identidade publica da conexao, validacao phone_number_id, persistencia duravel, deduplicacao e history generation | Adaptar tenancy `firm_id` para workspace/channel; preservar transacoes AsyncSession e worker Celery |
| `server/app/whatsapp_delivery_policy.py` | Escopo destinatario/conexao, controle antes do envio, janela de servico, tratamento de resultado ambiguo | Reutilizar conceitos necessarios ao fluxo aprovado; regras juridicas/IA/consentimento especificas exigem avaliacao propria |
| `server/app/whatsapp_media_ingestion.py` | Jobs de ingestao com claim, token e timeout; storage separado | Revisar fila e leases CRM2 sem importar tabelas juridicas |
| `server/tests/test_whatsapp_stage0.py` | Casos de HMAC, schema, normalizacao, status monotono, segredos, payloads e erros | Adaptar casos a modelos, contratos e providers CRM2 |
| `server/tests/test_whatsapp_coexistence.py`, `test_whatsapp_history_*.py` | Coexistencia, identidade antes da assinatura, processamento de historico | Executar somente se o fluxo aprovado exigir; validar requisitos atuais do provider e elegibilidade real |

Esses arquivos sao exemplos locais, nao documentacao atual oficial da Meta. Versao Graph, elegibilidade, janela e coexistencia precisam ser verificadas em fontes oficiais na implementacao. Nenhum codigo de produto foi copiado nesta etapa de planejamento.

## Limites e operacao

Chave ClickUp validada. Folder correto: `901318283724`; o valor anterior era um workspace ID. O script de realinhamento usa o folder explicitamente, faz preview por padrao e so escreve com `--apply`. Ele nao fecha tarefas nem envia comentarios/mensagens. Ao retomar apos falha, consulta nomes/codigos existentes para evitar duplicacao. Estados e tarefas legadas devem ser conferidos por leitura apos a alteracao.

Plano em JSON e descricoes contem dependencias por codigo; isso nao implica que dependencias nativas do ClickUp foram criadas. Nenhuma estimativa comercial ou data garantida foi adicionada.
