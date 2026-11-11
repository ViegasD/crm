# Reorganizacao local - 11/11/2026

Objetivo: separar a diretriz atual de entregas do historico CRM, dar uma entrada clara ao projeto e reduzir arquivos pontuais na raiz. Nao houve mutacao remota no ClickUp nem mudanca de configuracao local durante esta reorganizacao.

## Resultado

- `README.md` orienta leitura, desenvolvimento e verificacao.
- `SCOPE.md` e `ESCOPO_STATUS_CRM2.md` agora resumem a diretriz e o estado atuais. As versoes extensas anteriores foram preservadas em `docs/archive/crm/`.
- Documentacao agrupada em `context/`, `planning/`, `reports/`, `reference/`, `sources/` e `archive/`, com indice em `docs/README.md`.
- Plano/datas/resultados ClickUp atuais em `docs/planning/clickup/`; snapshot e registro de exclusao legada em `docs/archive/clickup/`.
- Importador/fechamento CRM obsoletos e seed duplicado da raiz preservados como texto no arquivo historico. O plano antigo de fechamento foi arquivado; atualizacoes novas usam um plano local explicito e exemplo vazio.
- Diagnosticos pontuais em `backend/tools/`; seed canonico mantido em `backend/seed.py`.
- PDF/ZIPs originais locais em `docs/sources/`; relatorio temporario TypeScript em `var/reports/frontend/`. Fontes privadas e `var/` ignorados pelo Git.
- Scripts ClickUp e referencias atuais apontam para os novos caminhos. Launchers e pastas de runtime permanecem no lugar.

## Verificacao

23 arquivos movidos, com SHA-256 conferido antes/depois. Fontes binarias, documentos arquivados e relatorio temporario foram novamente comparados com o [manifesto](WORKSPACE_RELOCATION_2026-11-11.json). Arquivos ativos editados receberam atualizacao de caminho/conteudo; o hash inicial no manifesto registra o momento da movimentacao.

Passaram: verificacao de links Markdown locais da documentacao ativa; sintaxe dos sete scripts PowerShell ativos; parse/imports das ferramentas Python; previews offline do plano e da exclusao; calculo de datas; tres testes backend de regressao; head Alembic unico `202611110001`; `git diff --check`.

As alteracoes preexistentes em `backend/.env.local` e `frontend/.env.example` foram preservadas byte a byte em comparacao ao backup anterior. Nenhum seed, diagnostico de banco, atualizador de datas ou comando de escrita ClickUp foi executado.

Sem alteracao de codigo frontend/runtime nesta tarefa; o build nao foi repetido. Migrations em banco e WhatsApp real continuam com as limitacoes registradas no [relatorio de integracao](INTEGRACAO_VALIDACAO_2026-11-11.md).
