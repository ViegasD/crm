# CRM2

Gestao de entregas de marketing e projetos de e-commerce para a operacao interna da agencia. CRM comercial e atendimento sao uma base existente, com prioridade secundaria no novo MVP.

Instancia compartilhada de desenvolvimento: [abrir app](https://hermes-crm2-dev.5tpiot.easypanel.host). EasyPanel: projeto `hermes`, servico Compose `crm2-dev`. [Acesso privado, validacoes e limites](docs/reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md) e [runbook](deploy/README.md). WhatsApp permanece sem pareamento por escolha do usuario.

## Comece aqui

Diretriz reconfirmada em 11/11: **marketing e e-commerce estão no MVP; comercial é secundário**. A exclusão dessas áreas no novo desenho comercial está superada. Leia a [correção de escopo](docs/planning/CORRECAO_ESCOPO_2026-11-11.md).

1. [Escopo atual](SCOPE.md): prioridade confirmada e decisoes ainda pendentes.
2. [Status atual](ESCOPO_STATUS_CRM2.md): implementacao, validacoes e riscos.
3. [Modo de trabalho](MODO_DE_TRABALHO_CRM2.md): regras de stages, evidencia e aceite.
4. [Documentacao](docs/README.md): contexto, planejamento, referencias, relatorios e historico.
5. [Estrutura do repositorio](docs/reference/STRUCTURE.md): localizacao de codigo e ferramentas.

## Desenvolvimento local

Stack: Next.js/React/TypeScript; FastAPI/SQLAlchemy; PostgreSQL, Redis, MinIO e Celery. Configuracoes locais ficam em `backend/.env`, `backend/.env.local`, `frontend/.env*` e `scripts/.env`.

Os launchers existentes continuam na raiz:

```powershell
.\dev-deps.ps1
.\dev-backend.ps1 -SkipDocker
.\dev-frontend.ps1 -SkipDocker
```

`dev.ps1` combina os launchers. Eles podem instalar dependencias, iniciar servicos e aplicar migrations; revise as opcoes antes de executar. O seed canonico e `backend/seed.py`, executado a partir de `backend/`. O seed duplicado da raiz foi preservado no arquivo historico de ferramentas.

## Verificacoes

```powershell
# Na pasta frontend/
npm run type-check
npm run lint
npm run build -- --webpack

# Na pasta backend/, com configuracao valida
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m alembic heads
```

Os comandos de verificacao nao substituem upgrade em banco descartavel nem testes reais de WhatsApp. Consulte as limitacoes no status atual.

## Planejamento

ClickUp: folder CRM2 `901318283724`, 30 tarefas nas listas `MVP 00` a `MVP 06`, com cronograma provisorio de 16/11 a 14/12/2026. Consulte o ClickUp para status atuais e a [correcao de escopo](docs/planning/CORRECAO_ESCOPO_2026-11-11.md) para interpretar o realinhamento comercial anterior. Fontes locais do plano e dos resultados ficam em [docs/planning/clickup](docs/planning/clickup/).

Ferramentas de ClickUp: [scripts/USAGE.md](scripts/USAGE.md). Material privado de origem fica em `docs/sources/`; saidas temporarias locais ficam em `var/`. Historico de CRM e ferramentas obsoletas ficam em `docs/archive/`.
