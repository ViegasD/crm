# Handoff para o agente do outro colaborador - CRM2

Atualizado em 11/11/2026, fuso America/Araguaina. Destinado ao agente do colaborador que tambem trabalha neste repositorio, incluindo a frente remota Stage 3/4/9. Os commits consultados usam o mesmo nome de autor; este documento nao atribui identidade pessoal a partir disso.

> Publicacao para colaboracao: usar a branch **`codex/delivery-first-integration`** como base compartilhada. Ela publica um snapshot integrado sobre `origin/main`, sem carregar o historico local que continha uma credencial antiga nem o arquivo `backend/.env.local`. Os hashes locais abaixo documentam a origem do trabalho e nao sao a referencia a buscar no remoto. Depois do push, a entrada correta e `git fetch origin` e uma branch propria derivada de `origin/codex/delivery-first-integration`. A validacao de banco/WhatsApp continua pendente; a proposta de integracao e draft.

## Missao e mudanca de direcao

O cliente corrigiu a prioridade em 09/11: o MVP precisa garantir **entregas de marketing e e-commerce**. Comercial/CRM de vendas fica em segundo plano. Nao retomar automaticamente a sequencia antiga de stages omnichannel.

Ha uma base CRM/atendimento ampla que pode ser reutilizada. O dominio novo de projetos/demandas de marketing, checklists de e-commerce, revisao/aprovacao e indicadores de entregas ainda nao foi implementado. E-commerce aqui significa gestao de implantacao/manutencao de lojas, sem compromisso de construir uma plataforma de loja propria.

A prioridade de entregas esta confirmada. O detalhamento de Kanban, papeis, portal do cliente, aprovacao, recorrencia e notificacoes ainda precisa de validacao com a agencia. As tarefas D00 registram essas decisoes. WhatsApp nao foi definitivamente excluido: seu papel no MVP e condicional a D00.4.

## Primeiro: obtenha a base certa

Repositorio: `https://github.com/ViegasD/crm`.

Base de codigo/documentacao deste handoff: **`1bcc187`**, em `main` no checkout de Fabio. O commit que acrescenta este handoff sera posterior. Em um fetch de 11/11, antes de escrever este arquivo:

| Referencia | Commit | Estado |
| --- | --- | --- |
| `origin/main` | `ca2616d` | Contido na base local |
| `origin/codex/stage-3-4-9-qa` | `33a02ea` | Contido na base local |
| Checkpoint de alteracoes locais | `dcce499` | Preservou codigo/documentacao antes do merge |
| Merge local | `382b97c` | Integrou QA e main, preservando WhatsApp/midia locais |
| Exclusao legada e datas | `ae779d2` | Registrou as operacoes no ClickUp |
| Reorganizacao do workspace | `1bcc187` | Documentos atuais, arquivo historico e ferramentas reorganizados |

**Retrato anterior a publicacao:** esses commits locais ainda nao estavam no remoto. Na consulta, `1bcc187` estava sete commits a frente de `origin/main` e cinco a frente da branch QA, sem commits remotos pendentes. A publicacao posterior usa o snapshot seguro da branch indicada no aviso acima. Apenas `git pull origin main` nao entrega essa branch; obtenha `origin/codex/delivery-first-integration` e derive sua branch de trabalho dela.

Depois de receber a base, preserve seu trabalho local, confira `git status` e crie sua branch de trabalho a partir dela. Nao reaplique a branch QA inteira como se ainda nao estivesse integrada; nao recrie arquivos nos caminhos antigos.

## Leitura obrigatoria, na ordem

1. [README](../../README.md), [escopo atual](../../SCOPE.md) e [status atual](../../ESCOPO_STATUS_CRM2.md).
2. [Modo de trabalho](../../MODO_DE_TRABALHO_CRM2.md): criterios de fechamento, evidencia tecnica e testes manuais.
3. [Handoff original](HANDOFF_COMPLETO.md): decisao do cliente versus requisitos propostos.
4. [Integracao e validacao](../reports/INTEGRACAO_VALIDACAO_2026-11-11.md): resolucoes do merge e limitacoes.
5. [Realinhamento](../planning/REALINHAMENTO_2026-11-11.md): trilha ativa e referencias WhatsApp de fabia.
6. [Plano](../planning/clickup/CLICKUP_DELIVERY_PLAN_2026-11-11.json), [resultado/IDs](../planning/clickup/CLICKUP_REWORK_RESULT_2026-11-11.json) e [datas](../planning/clickup/CLICKUP_SCHEDULE_2026-11-11.json).

A [auditoria inicial](../reports/AUDITORIA_DIRECIONAMENTO_2026-11-11.md) foi anterior ao fetch: suas observacoes de ausencia de Stage 9 no checkout nao significam ausencia de implementacao remota. O merge passou a incluir esse trabalho. Nao reabrir ou reimplementar recursos apenas com base naquele retrato.

## ClickUp: o planejamento foi substituido

Folder CRM2: **`901318283724`**, no espaco `viponline`. O token local foi validado em 11/11; isso nao garante que estara valido no seu ambiente. O ID anterior `9013086181` era de workspace e gerava 404 quando usado como folder; nao confundir esse erro com chave expirada.

O usuario pediu explicitamente a exclusao das **138 tarefas legadas e 23 listas vazias**. A operacao terminou e tem registro em `docs/archive/clickup/CLICKUP_LEGACY_DELETION_2026-11-11.json`. Nao recriar esse backlog nem usar seus IDs como tarefas ativas.

Ultimo retrato verificado: sete listas, 30 tarefas abertas, todas com inicio/vencimento. Consulte live antes de assumir tarefa ou alterar status; os JSONs sao snapshots, nao locks nem prova de estado atual.

| Lista | Frente |
| --- | --- |
| MVP 00 | Diretriz e validacao de escopo |
| MVP 01 | Fundacao e seguranca |
| MVP 02 | Clientes e servicos |
| MVP 03 | Entregas de marketing |
| MVP 04 | Projetos de e-commerce |
| MVP 05 | Painel, homologacao e producao |
| MVP 06 | WhatsApp condicionado ao fluxo |

Datas escolhidas pelo usuario: **16/11 a 14/12/2026**, envelope provisorio de 20 dias uteis. Exclui fins de semana e 20/11; feriados locais/capacidade precisam ser confirmados. A proposta PDF antiga fornece a duracao, mas suas fases comerciais foram superadas pelo handoff revisado. Nao tratar essas datas como garantia contratual. Dependencias sao descritas por codigo; links nativos de dependencia nao foram criados.

## Frente inicial recomendada para este agente

**Sugestao, ainda nao atribuida:** assumir [D01.5 - migrations](https://app.clickup.com/t/wdpu2yt81n) e a validacao da integracao Stage 3/4/9, aproveitando o contexto da branch QA. Primeiro confirme que outro agente nao esta trabalhando nos mesmos arquivos. O handoff nao reserva arquivos nem atribui a tarefa a uma pessoa.

O risco concreto e o historico Alembic: existe um unico head, `202611110001`, mas ha raizes antigas com criacao explicita de tabelas e `Base.metadata.create_all()` dependente do modelo atual. Banco vazio e banco que tenha apenas a linhagem remota podem encontrar colisoes. Nao corrigir isso com `stamp head`, exclusao de dados ou recriacao do banco de trabalho para apenas fazer o comando passar.

Para D01.5, a entrega proposta e:

1. Reproduzir upgrade em banco descartavel vazio e em copias/fixtures das bases local e QA; identificar a revisao de partida real.
2. Corrigir com estrategia que preserve dados e historia implantada; coordenar com o outro agente antes de alterar revisoes existentes ou criar novos heads.
3. Verificar schema resultante e payloads de webhook historicos. Testar tanto a linhagem `202605221215` quanto a `202605250001` quando representadas nas bases de teste.
4. Registrar comandos, resultados, riscos de upgrade/rollback e roteiro de aceite manual. Nao executar alteracoes contra producao.

Outras tarefas ativas, caso uma delas seja combinada como sua frente:

| Tarefa | Contexto |
| --- | --- |
| [D01.2](https://app.clickup.com/t/wdpu2yt81h) | Enforce de papeis administrativos; `require_roles` existe, mas a cobertura de rotas e insuficiente |
| [D01.3](https://app.clickup.com/t/wdpu2yt81j) | Membership/autorizacao de upload e presign de midia |
| [D01.4](https://app.clickup.com/t/wdpu2yt81m) | Onboarding para usuario sem workspace e gerenciamento de equipe |
| [D00.4](https://app.clickup.com/t/wdpu2yt81e) | Decidir o papel de WhatsApp no MVP antes de ampliar sua implementacao |
| [D06.1](https://app.clickup.com/t/wdpu2yt82c) | Mapear reuso de fabia para a arquitetura CRM2, condicionado ao fluxo aprovado |

Nenhuma dessas tarefas e considerada concluida por este documento. A frente do dominio novo deve ser coordenada com o agente principal; nao iniciar uma segunda implementacao de clientes/projetos/tarefas sem combinar contratos e ownership.

## Coordenacao entre dois agentes

- Preferir o checkout/branch proprio do colaborador. No mesmo computador, usar clones ou worktrees separados; duas branches nao isolam trabalho se ambos editarem o mesmo diretorio. Nao criar nada no ambiente do outro agente sem combinar.
- Antes de editar, comunicar ao responsavel do projeto: codigo Dxx, objetivo, branch/base, arquivos/migrations previstos e dependencias. Se a tarefa estiver assumida, combinar divisao concreta ou escolher outra tarefa.
- Tratar migrations e arquivos centrais como pontos compartilhados: `models/__init__.py`, `models/enums.py`, `main.py`, `workers/celery_app.py`, contratos API/schemas e `frontend/src/lib/api.ts`. Coordenar a alteracao; nao impor uma segunda versao em paralelo.
- No mesmo checkout, nao trocar branch, fazer stash/reset/clean, aplicar migrations, criar commits com `git add -A` ou sobrescrever alteracoes alheias. Incluir somente os caminhos da sua entrega.
- No checkout de Fabio ha alteracoes locais preexistentes em `backend/.env.local` e `frontend/.env.example`; foram preservadas. Nao copia-las para o seu ambiente nem sobrescreve-las. O fato de um arquivo estar modificado nao significa que pertence ao seu trabalho.
- Evitar reformatacao ampla, renomeacoes gerais e refactors fora da tarefa: o workspace acabou de ser reorganizado. Descrever mudancas de contrato antes de consumi-las em outra frente.
- Ao entregar, informar branch/commit, tarefas afetadas, arquivos compartilhados, migrations, evidencias e limitacoes. Nao presumir aprovacao tecnica de outro agente nem aceite do usuario.

## Compatibilidades do merge a preservar

- `WebhookEvent.payload` e `raw_payload` acessam o mesmo armazenamento local via synonym. Dispatch inicial e retry operacional devem processar o mesmo payload.
- Persistencia grava hash da assinatura e headers permitidos, sem salvar Authorization/apikey.
- O backfill de webhook acrescenta colunas operacionais em tabelas locais existentes antes dos indices; a migration de merge preserva payloads da variante remota.
- Celery registra o dispatch local e workers remotos, com uma unica agenda periodica de retry.
- Envio WhatsApp real, ingestao/preview de midia e atualizacao de mensagens locais foram preservados junto de routing, timeline e recursos remotos.
- A liberacao do lock apos envio foi restaurada na revisao; preservar isso junto do reset de anexos no reply box.

## Validacao conhecida e reproducao local

Na integracao passaram TypeScript, lint, build Webpack, import/mapeamento backend, OpenAPI, smoke de health, registro das tarefas Celery e tres testes de regressao. O backend importado expunha 57 tabelas e 110 caminhos OpenAPI. Isso nao comprova operacao real de todos os endpoints.

Nao foram validados upgrade em banco, workers/Redis ativos, WhatsApp real nem aceite manual: Docker Desktop Linux engine estava indisponivel. Turbopack falhou por falta de memoria; Webpack passou. O ambiente herdado `DEBUG=release` nao e um booleano valido; nos checks foi usado override de processo `DEBUG=false`, sem editar arquivos locais.

PowerShell, a partir da raiz do checkout correto:

```powershell
git status --short
git log -5 --oneline

# Backend: na pasta backend/, com dependencias/configuracao do seu ambiente
$env:DEBUG = 'false'
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m alembic heads

# Frontend: na pasta frontend/
npm run type-check
npm run lint
$env:NODE_OPTIONS = '--max-old-space-size=4096'
npm run build -- --webpack
```

Adapte os caminhos de virtualenv ao seu sistema. Nao executar o launcher backend como primeira verificacao cega: ele pode aplicar migrations. Use banco descartavel para o trabalho D01.5.

Para dados/configuracao de ClickUp, consulte `scripts/USAGE.md`; `scripts/.env` nao e versionado e nao deve aparecer em logs/handoff. O preview `backend/.venv/Scripts/python.exe scripts/clickup_rework_delivery.py` e local. Os scripts de datas e exclusao sao ferramentas de uso pontual, nao um procedimento de inicializacao; nao executa-los para obter contexto.

## WhatsApp: referencia adicional de fabia

O usuario autorizou consultar `C:/Users/fabio/Work/fabia` como fonte de exemplos. Esse checkout pode nao existir no computador do colaborador; nao e dependencia de runtime e nao autoriza acesso a segredos ou dados privados. A referencia local inspecionada estava em `c0bb817`.

Arquivos relevantes em `server/app/`: `official_whatsapp_client.py`, `whatsapp_security.py`, `routers/official_whatsapp_webhook.py`, `whatsapp_delivery_policy.py`, `whatsapp_media_ingestion.py`. Testes: `server/tests/test_whatsapp_stage0.py`, `test_whatsapp_coexistence.py` e `test_whatsapp_history_*.py`.

Reutilizar conceitos de classificacao de erros, Retry-After, assinatura em bytes originais, escopo por numero, idempotencia, resultado ambiguo de envio e midia limitada. Adaptar a `AsyncSession`/httpx/Celery e workspace/channel do CRM2. Nao copiar modelos `firm_id`, regras juridicas/IA especificas, segredos, toda a stack aiohttp ou restricoes de grupos por inercia. Verificar requisitos atuais oficiais da Meta quando implementar coexistencia/Graph/janelas, sem tratar o codigo de referencia como garantia atual de provider.

## Arquivos e contexto que nao viajam pelo Git

Fontes WhatsApp e PDF original ficam em `docs/sources/`, ignorados pelo Git. O PDF ainda e anterior ao pivot; nao usar como escopo atual. Audios/videos nao foram integralmente analisados. Backups de arquivos locais e tarefas excluidas ficam fora do repositorio no computador de Fabio; os relatorios versionados registram sua localizacao, mas nao garantem acesso pelo colaborador.

O mapa atual esta em `docs/reference/STRUCTURE.md`. `docs/reference/API.md` e parcial; OpenAPI da aplicacao correta e o contrato executavel. Ferramentas pontuais ficam em `backend/tools/`; o seed canonico e `backend/seed.py`. Scripts obsoletos de importacao/fechamento foram arquivados como texto em `docs/archive/`.

## Criterio de entrega

Seguir `MODO_DE_TRABALHO_CRM2.md`: implementado e integrado; contratos conferidos; validacao tecnica executada; roteiro manual para Thiago quando aplicavel; resultados e pendencias registrados no ClickUp dentro da autorizacao da tarefa. Codigo que apenas compila nao basta para fechar feature. Confirmar autorizacao antes de publicar comentarios/mensagens se o ambiente do agente a exigir; nenhuma mensagem foi enviada ao outro colaborador por este handoff.

Resposta inicial esperada do agente receptor: confirmar a base recebida, resumir a nova prioridade, informar a tarefa/frente que pretende assumir e os arquivos compartilhados que ela toca. Isso permite coordenar sem duplicar trabalho.
