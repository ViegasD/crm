# Estrutura atual do repositorio

Mapa atualizado em 11/11/2026. Descreve pastas existentes; nao presume que todas as funcionalidades estejam prontas.

```text
crm2/
  README.md                     Entrada do projeto e desenvolvimento local
  SCOPE.md                      Diretriz e escopo atual
  ESCOPO_STATUS_CRM2.md          Status atual e pendencias
  MODO_DE_TRABALHO_CRM2.md       Regras operacionais
  dev*.ps1                      Launchers locais existentes
  docker-compose.yml            Servicos do ambiente
  backend/
    app/                        API, modelos, schemas, servicos, adapters e workers
    migrations/                 Historico Alembic
    tests/                      Testes de regressao
    tools/                      Diagnosticos e manutencao pontual
    seed.py                     Seed canonico de desenvolvimento
    alembic.ini
    requirements.txt
    Dockerfile
  frontend/
    src/app/                    Rotas Next.js
    src/components/             UI de inbox, configuracoes e componentes comuns
    src/lib/                    API e WebSocket
    src/stores/                 Estado de autenticacao/conversas
    src/types/                  Contratos TypeScript
    package.json
  docker/postgres-init/         Inicializacao de bancos locais
  scripts/                      Ferramentas ClickUp e configuracao local
    USAGE.md                    Instrucoes e limites
  docs/
    context/                    Handoff de origem
    planning/clickup/           Plano, datas e resultados da trilha atual
    reports/                    Auditorias e evidencias de validacao
    reference/                  Referencias tecnicas
    sources/                    Fontes privadas locais (ignoradas pelo Git)
    archive/crm/                Escopo, status e mapa antigos
    archive/clickup/            Snapshot legado, exclusao e ferramentas obsoletas
    archive/tools/              Seed duplicado antigo, preservado como texto
  var/                          Saidas temporarias locais (ignoradas pelo Git)
```

`.venv/`, `node_modules/`, `.next/` e caches permanecem junto de suas ferramentas, ignorados pelo Git. Configuracoes `.env` existentes nao foram realocadas.

O [mapa arquitetural anterior](../archive/crm/STRUCTURE_PLANEJADA.md) inclui arquivos e recursos previstos que nao necessariamente existiam. Para inspecionar rotas reais, use `/docs` ou `/openapi.json` no backend em execucao.
