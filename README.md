# CRM2

O MVP do CRM2 reúne CRM comercial, gestão de entregas de marketing e gestão de projetos de e-commerce para a agência.

Instancia compartilhada de desenvolvimento: [abrir app](https://hermes-crm2-dev.5tpiot.easypanel.host). EasyPanel: projeto `hermes`, servico Compose `crm2-dev`. [Acesso privado, validacoes e limites](docs/reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md) e [runbook](deploy/README.md). WhatsApp permanece sem pareamento por escolha do usuario.

## Comece aqui

1. [Como retomar o CRM2](docs/context/CONTINUIDADE_CRM2.md) — entrada para contribuidores e agentes.
2. [Escopo do MVP](SCOPE.md) e [desenho da frente comercial](docs/planning/crm2_mvp_comercial.md).
3. [Revisão de código e realinhamento](docs/reports/crm2_code_review_e_realinhamento_2026-11-11.md).
4. [Índice da documentação](docs/README.md).

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

O andamento atual fica na pasta CRM2 do ClickUp. As listas MVP 03 e MVP 04 cobrem marketing e e-commerce. Os [snapshots do planejamento](docs/planning/clickup/) e a [revisão da base comercial](docs/reports/crm2_code_review_e_realinhamento_2026-11-11.md) registram decisões e evidências datadas.

Ferramentas de ClickUp: [scripts/USAGE.md](scripts/USAGE.md). Material privado de origem fica em `docs/sources/`; saidas temporarias locais ficam em `var/`. Historico de CRM e ferramentas obsoletas ficam em `docs/archive/`.
