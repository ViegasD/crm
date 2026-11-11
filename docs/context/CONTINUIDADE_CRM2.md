# Como retomar o CRM2

**Marketing e e-commerce estão no MVP.** A prioridade é gestão de entregas; comercial permanece secundário, conforme Ruan e a reconfirmação do usuário em 11/11/2026. Não adotar a exclusão dessas áreas no desenho comercial do colaborador.

## Ordem de leitura

1. [Correção de escopo](../planning/CORRECAO_ESCOPO_2026-11-11.md): decisão vigente e interpretação da revisão anterior.
2. [SCOPE.md](../../SCOPE.md) e [handoff de origem](HANDOFF_COMPLETO.md): prioridades confirmadas e detalhes ainda propostos.
3. [Status da implementação](../../ESCOPO_STATUS_CRM2.md), [runbook](../../deploy/README.md) e [evidências de deploy](../reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md): separar código existente, testes executados e homologação.
4. ClickUp, pasta CRM2 `901318283724`: fila atual, status, responsáveis e dependências. A [reconciliação verificada](../planning/clickup/CLICKUP_SCOPE_CORRECTION_2026-11-11.json) registra a correção de 7 listas e 30 tarefas.

## Próximas frentes

- Validar as jornadas reais de marketing/e-commerce e suas permissões com a agência. Portal, recorrência, regras de aprovação e integrações precisam de decisão específica.
- Corrigir e testar isolamento por workspace e objeto, mídia, WebSocket, administração e migrations. Preservar os achados técnicos úteis do review; não tratar revisão estática como teste executado.
- Implementar clientes/serviços, demandas de marketing e projetos/checklists de e-commerce com critérios testáveis. O domínio de entregas ainda não está implementado na base auditada.
- Reaproveitar o CRM/atendimento existente. Novas funcionalidades comerciais são secundárias.
- Manter WhatsApp sem pareamento na instância compartilhada até autorização do usuário. Não exigir dois números oficiais como condição geral para o MVP de entregas sem validação das jornadas.

Antes de iniciar código, conferir a revisão compartilhada, o estado do PR e o trabalho em andamento. Preservar alterações locais e usar branches separadas. Registrar evidência técnica e aceite manual separadamente. Não repetir a reorganização do ClickUp nem apagar o histórico de escopo.
