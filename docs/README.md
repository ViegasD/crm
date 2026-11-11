# Documentacao

Comece por [Como retomar o CRM2](context/CONTINUIDADE_CRM2.md). O [escopo do MVP](../SCOPE.md) reúne CRM comercial, entregas de marketing e projetos de e-commerce. O [desenho comercial](planning/crm2_mvp_comercial.md) detalha a frente comercial.

Instancia compartilhada: [relatorio de deploy, acesso e validacao](reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md); [runbook EasyPanel](../deploy/README.md).

| Pasta | Conteudo | Como usar |
| --- | --- | --- |
| [context](context/) | Handoff e contexto de origem | Distinguir decisao confirmada de proposta do assistente |
| [planning](planning/) | Desenho vigente e registros de planejamento | Os JSONs em `planning/clickup/` são snapshots históricos |
| [reports](reports/) | Auditoria, integracao e verificacoes | Ler data e limitacoes antes de tratar como estado atual |
| [reference](reference/) | API e estrutura tecnica | API.md e mapa parcial; OpenAPI da aplicacao e a referencia executavel |
| [sources](sources/README.md) | WhatsApp ZIPs e proposta PDF originais locais | Material privado e historico; preservado, ignorado pelo Git |
| [archive](archive/README.md) | Escopo CRM anterior, snapshots e ferramentas antigas | Historico; nao reaplicar automaticamente |

## Registros anteriores

O [handoff anterior](context/HANDOFF_AGENTE_COLABORADOR_2026-11-11.md) registra a fase de integração da base.

1. [Handoff](context/HANDOFF_COMPLETO.md).
2. [Realinhamento anterior](planning/REALINHAMENTO_2026-11-11.md).
3. [Integracao e validacao](reports/INTEGRACAO_VALIDACAO_2026-11-11.md).
4. [Plano de tarefas](planning/clickup/CLICKUP_DELIVERY_PLAN_2026-11-11.json) e [datas](planning/clickup/CLICKUP_SCHEDULE_2026-11-11.json).

O relatorio de auditoria inicial retrata o checkout anterior ao fetch; o relatorio de integracao o complementa. Registros datados preservam o que aconteceu, inclusive mudancas de decisao. A [matriz de realocacao](reports/WORKSPACE_RELOCATION_2026-11-11.json) relaciona os caminhos anteriores e atuais.
