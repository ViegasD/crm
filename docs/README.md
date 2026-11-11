# Documentacao

**Diretriz vigente:** marketing e e-commerce estão no MVP, com comercial em segundo plano. A [correção de escopo de 11/11](planning/CORRECAO_ESCOPO_2026-11-11.md) supera a exclusão dessas áreas no desenho comercial publicado pelo colaborador.

A entrada principal e o [README do projeto](../README.md). Para decidir o que construir, leia [escopo](../SCOPE.md), [status](../ESCOPO_STATUS_CRM2.md) e [modo de trabalho](../MODO_DE_TRABALHO_CRM2.md).

Instancia compartilhada: [relatorio de deploy, acesso e validacao](reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md); [runbook EasyPanel](../deploy/README.md).

| Pasta | Conteudo | Como usar |
| --- | --- | --- |
| [context](context/) | Handoff e contexto de origem | Distinguir decisao confirmada de proposta do assistente |
| [planning](planning/) | Realinhamento e trilha atual do MVP | Planejar entregas; JSONs ClickUp ficam em `planning/clickup/` |
| [reports](reports/) | Auditoria, integracao e verificacoes | Ler data e limitacoes antes de tratar como estado atual |
| [reference](reference/) | API e estrutura tecnica | API.md e mapa parcial; OpenAPI da aplicacao e a referencia executavel |
| [sources](sources/README.md) | WhatsApp ZIPs e proposta PDF originais locais | Material privado e historico; preservado, ignorado pelo Git |
| [archive](archive/README.md) | Escopo CRM anterior, snapshots e ferramentas antigas | Historico; nao reaplicar automaticamente |

## Ordem de leitura recomendada

Para outro colaborador/agente entrando em paralelo: [handoff de colaboracao](context/HANDOFF_AGENTE_COLABORADOR_2026-11-11.md), incluindo baseline Git, tarefas candidatas e limites de trabalho compartilhado.

1. [Handoff](context/HANDOFF_COMPLETO.md).
2. [Realinhamento atual](planning/REALINHAMENTO_2026-11-11.md).
3. [Integracao e validacao](reports/INTEGRACAO_VALIDACAO_2026-11-11.md).
4. [Plano de tarefas](planning/clickup/CLICKUP_DELIVERY_PLAN_2026-11-11.json) e [datas](planning/clickup/CLICKUP_SCHEDULE_2026-11-11.json).

O relatorio de auditoria inicial retrata o checkout anterior ao fetch; o relatorio de integracao o complementa. Registros datados preservam o que aconteceu, inclusive mudancas de decisao. A [matriz de realocacao](reports/WORKSPACE_RELOCATION_2026-11-11.json) relaciona os caminhos anteriores e atuais.
