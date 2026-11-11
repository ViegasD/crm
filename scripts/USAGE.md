# Ferramentas ClickUp

A trilha ativa e MVP 00-06 no folder CRM2 `901318283724`. Dados de planejamento ficam em `docs/planning/clickup/`; snapshots e registros legados ficam em `docs/archive/clickup/`.

## Configuracao local

Copie `.env.example` para `.env` nesta pasta e configure `CLICKUP_API_TOKEN`. O arquivo `.env` existente foi preservado e e ignorado pelo Git.

## Consultas

Da raiz do repositorio:

```powershell
.\scripts\clickup_check.ps1 -IncludeClosed
```

Para salvar um retrato local sem poluir arquivos versionados:

```powershell
.\scripts\clickup_check.ps1 -IncludeClosed -OutputJsonPath .\var\clickup-report.json
```

Crie `var/` antes de usar esse destino. O check e somente leitura, salvo o arquivo de saida solicitado. Token invalido retorna `OAUTH_025`; folder incorreto pode retornar 404 mesmo com chave valida.

## Plano delivery-first

Para a correcao confirmada em 11/11, `python scripts/clickup_correct_scope.py` faz uma leitura e preview. `--apply` reconcilia os mesmos 30 IDs, preserva status, responsaveis e descricoes e registra backup privado em `var/backups/`. A execucao ja concluida consta em `docs/planning/clickup/CLICKUP_SCOPE_CORRECTION_2026-11-11.json`; nao repetir sem necessidade. O script interrompe se encontrar a correcao ja aplicada ou edicao concorrente.

Preview local, sem requests nem mudancas remotas:

```powershell
backend/.venv/Scripts/python.exe scripts/clickup_rework_delivery.py
```

Com `--apply`, cria apenas listas/tarefas ausentes previstas no plano. As listas legadas excluidas nao fazem mais parte do plano. Tarefas existentes sao identificadas por codigo Dxx e seu progresso nao e sobrescrito. Nao executar mutacoes sem tarefa autorizada pelo usuario.

## Atualizacoes explicitas

Copie `clickup_update_plan.example.json` para `clickup_update_plan.local.json` e preencha apenas alteracoes autorizadas. O exemplo esta vazio. Cada item usa `listId`, `taskId` ou `taskName`, e opcionalmente `status`/`comment`.

```powershell
.\scripts\clickup_update.ps1 -PlanPath .\scripts\clickup_update_plan.local.json
```

Este comando altera ClickUp e pode publicar comentarios. A reorganizacao local nao o executou.

## Manutencao de uso pontual

- `clickup_schedule_delivery.py`: reaplica imediatamente as datas fixas de 16/11 a 14/12/2026 quando executado; nao e consulta nem scheduler generico.
- `clickup_remove_legacy.py`: preview por padrao; `--apply` foi usado para a exclusao autorizada de 138 tarefas. Usa registros historicos e nao deve ser reaplicado a outro backlog.
- `clickup_common.ps1`: configuracao e helpers dos scripts PowerShell; nao e um comando de mutacao por si so.

Os antigos `clickup_import.ps1`, `clickup_close_done.ps1` e o plano de fechamento anterior foram arquivados em `docs/archive/clickup/`. Os scripts historicos estao como texto e nao fazem parte do fluxo ativo. Credenciais continuam somente em `scripts/.env`.

Dependencias de tarefas sao descritas por codigo nos registros; links nativos de dependencia nao foram criados. O backup externo de tarefas excluidas e documentado no registro historico de exclusao.
