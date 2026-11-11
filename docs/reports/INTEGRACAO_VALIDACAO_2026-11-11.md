# Integracao e validacao - 11/11/2026

## Estado e escopo

O usuario autorizou atualizar o checkout, integrar branches remotas, reorganizar ClickUp e, depois, excluir as tarefas legadas e aplicar datas a partir de 16/11/2026.

Origem: `https://github.com/ViegasD/crm`. A branch QA em `33a02ea` inclui `origin/main` em `ca2616d`. O checkout original tinha o commit local `e6f8b36`, alem de alteracoes nao commitadas. Essas alteracoes de codigo/documentacao foram preservadas no checkpoint local `dcce499` antes da integracao. Segredos locais, arquivos de ambiente reais e ZIPs/PDF de origem ficaram fora desse checkpoint. Nada foi enviado ao remoto.

Merge local concluido em `382b97c`. Novo fetch apos o merge confirmou zero commits remotos pendentes de ambas as branches. Mudancas posteriores de planejamento/exclusao do ClickUp sao registradas separadamente.

Backup adicional dos arquivos locais alterados: `C:/Users/fabio/.codex/backups/crm2-before-sync-20261111-102906`. Referencia Git do HEAD original: `backup/pre-delivery-sync-20261111`.

Foram integrados os commits remotos de macros, categorias, snooze, mencoes, views, operacao/retry de webhooks, capacidade/SLA, supervisor, presenca e timeline/reabertura. As resolucoes preservam envio WhatsApp real, anexos/midia, preview de mensagem, links de contato e atualizacoes de mensagem locais, junto dos recursos remotos. O dominio de entregas de marketing/e-commerce ainda e trabalho futuro.

## Ajustes de compatibilidade da integracao

- `WebhookEvent.payload` e `raw_payload` passam a acessar a mesma coluna de payload local. Retry operacional e dispatch inicial leem o mesmo evento.
- Persistencia grava hash da assinatura e apenas headers permitidos (`content-type`/`user-agent`), preservando metadados sem salvar authorization/apikey.
- Backfill de webhook acrescenta colunas operacionais em tabelas locais ja existentes antes de criar indices que dependem delas.
- Migration de merge `202611110001` junta os dois heads, preserva payloads do schema remoto quando presentes e acrescenta campos/status de compatibilidade.
- Celery registra o dispatch local e os workers remotos. Somente a agenda remota de retry e mantida, evitando duas agendas periodicas concorrentes para replay.
- Cleanup dos timeouts do inbox usa a referencia capturada pelo effect.
- Revisao independente encontrou a chamada de liberacao de lock apos envio ausente na resolucao de conflito; ela foi restaurada junto do reset de anexos.

## Validado tecnicamente

| Checagem | Resultado |
| --- | --- |
| `npm run type-check` | Passou apos a integracao |
| `npm run lint` | Passou com zero erros/warnings apos corrigir cleanup |
| `npm run build` (Turbopack) | Falhou por falta de memoria no processo de compilacao CSS |
| `NODE_OPTIONS=--max-old-space-size=4096 npm run build -- --webpack` | Passou: compilacao, TypeScript e geracao das 11 paginas |
| Parse AST de 126 arquivos backend/migrations | Passou |
| Import, `configure_mappers()`, OpenAPI | Passou: 57 tabelas e 110 caminhos OpenAPI |
| TestClient `/health` e `/openapi.json` | Passou; smoke sem operacoes de negocio/banco |
| Registro de workers e 9 tarefas periodicas Celery | Passou; nenhum worker/Redis foi executado |
| 3 testes unittest de regressao | Passaram: head unico, payload compartilhado e persistencia segura de metadados |
| `alembic heads` | Um head: `202611110001` |
| `git diff --check` | Sem erros de whitespace |
| Upgrade de banco, Docker, provider real | Nao executados: Docker Desktop Linux engine indisponivel |

Os testes de head e metadados foram observados falhando antes das correcoes e passando depois. Comandos backend usam override de processo `DEBUG=false` porque o ambiente herdado contem `DEBUG=release`; arquivos de ambiente nao foram alterados para mascarar esse problema.

## Limite de migrations e criterio de fechamento

Head unico nao comprova que toda a historia sobe em banco vazio. O projeto tem duas raizes historicas, uma com `Base.metadata.create_all()` dependente dos modelos atuais, outra com criacao explicita. Isso pode duplicar tabelas em instalacao limpa e ao atualizar um banco que tenha apenas a linhagem remota. A revisao confirmou compatibilidade dos ajustes de webhook para a base local no head `202605221215`, mas **nenhum upgrade de banco foi executado**. Resolver/validar isso em banco descartavel e tarefa D01.5; nao considerar deploy ou stage concluido apenas por estas verificacoes.

## Testes manuais obrigatorios antes do aceite

1. Thiago: iniciar dependencias, fazer backup e executar migrations em banco descartavel vazio e copia do banco existente. Conferir head/schema e payloads historicos antes/depois.
2. Login, workspace e inbox: abrir conversa real, navegar ao contato, recarregar, enviar texto/anexo e confirmar que o lock de digitacao e liberado; outro agente deve conseguir atuar sem aguardar TTL.
3. Timeline: concluir/reabrir, gerar nova mensagem dentro/fora da janela de reabertura configurada e conferir protocolo, autor e historico sem duplicacao.
4. SLA/capacidade: dois agentes tentam assumir a mesma conversa; verificar atribuicao, limite, presenca/pausa, escalonamento e painel supervisor com workers ativos.
5. Webhooks: enviar evento assinado, repetir, provocar falha temporaria e testar retry/observabilidade. Confirmar integridade do payload e que evento de outro numero/workspace nao e atribuido incorretamente.
6. WhatsApp real, quando aprovado como necessario ao MVP: Meta/Evolution, texto, anexo e recibos. Coexistencia/historico apenas se aprovados e elegiveis. Validar erros de credencial e entrega sem duplicar mensagens.
7. Validar papel administrativo e acesso de midia entre workspaces; os gaps identificados anteriormente seguem nas tarefas D01.2 e D01.3.

Aceite: comportamentos e dados correspondem aos contratos aprovados; erros sao visiveis; nenhuma perda/duplicacao de dados; logs sem segredos; evidencias tecnicas e resultado manual registrados antes de fechar tarefa.

## ClickUp e cronograma

O realinhamento criou sete listas e 30 tarefas. A verificacao inicial confirmou preservacao das 138 tarefas antigas. Em seguida o usuario pediu exclui-las: backup externo e resultado em `docs/archive/clickup/CLICKUP_LEGACY_DELETION_2026-11-11.json`; anexos binarios nao sao copiados, apenas metadados/URLs. A trilha ativa permanece MVP 00-06. Nenhuma tarefa nova foi fechada por inferencia.

Exclusao concluida: 138 tarefas e 23 listas que ficaram vazias. Backup em `C:/Users/fabio/.codex/backups/crm2-clickup-legacy-20261111/tasks.json`: detalhes de todas as tarefas e 62 comentarios; nenhum comentario referenciava respostas em thread. O backup nao e um mecanismo de restauracao automatica nem inclui os binarios anexados.

O usuario escolheu 16/11/2026 como inicio. A proposta, secao 5, fornece envelope de 20 dias uteis, condicionado a escopo/acessos; suas fases comerciais foram superadas. As datas aplicam a distribuicao do handoff revisado: dias 1-4 fundacao/clientes, 5-10 marketing, 11-15 e-commerce, 16-18 painel/revisoes, 19-20 QA/implantacao. WhatsApp e condicional a D00.4.

Calendario: segunda a sexta, excluindo 20/11, feriado nacional. Resultado: **16/11 a 14/12/2026**. Nao foram presumidas folgas da agencia nem feriados municipais/estaduais. Fonte nacional: https://agenciagov.ebc.com.br/noticias/202512/confira-o-calendario-oficial-de-feriados-nacionais-e-pontos-facultativos-em-2026 . As datas sao planejamento provisorio, nao garantia contratual.

IDs, URLs e evidencias: `docs/planning/clickup/CLICKUP_REWORK_RESULT_2026-11-11.json`, `docs/planning/clickup/CLICKUP_SCHEDULE_2026-11-11.json` e `docs/archive/clickup/CLICKUP_LEGACY_DELETION_2026-11-11.json`. Dependencias sao descritas por codigo; nao foram criadas dependencias nativas. Fontes WhatsApp de fabia estao mapeadas em `docs/planning/REALINHAMENTO_2026-11-11.md`; nenhum segredo ou regra juridica daquele produto foi copiado.

Leitura final da API confirmou: sete listas MVP, 30 tarefas abertas, todas com data de inicio e vencimento conforme o plano, zero tarefas/listas legadas restantes. Os criterios de aceite e a ressalva de cronograma provisorio continuam nas descricoes; nenhum responsavel foi presumido. O plano reaplicavel foi atualizado para nao recriar listas legadas excluidas.
