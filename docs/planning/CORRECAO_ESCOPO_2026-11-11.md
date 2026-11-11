# Correção de escopo — 11/11/2026

O usuário confirmou nesta sessão: **“marketing and ecom should be in the mvp”**. Marketing e e-commerce fazem parte do MVP. A prioridade continua sendo a gestão de entregas; comercial fica em segundo plano, conforme a correção de Ruan de 09/11 registrada em [HANDOFF_COMPLETO](../context/HANDOFF_COMPLETO.md).

A revisão do colaborador e o desenho `docs/planning/crm2_mvp_comercial.md`, publicados na branch `codex/crm2-contexto-mvp` (`883130e`), inverteram essa prioridade ao excluir marketing/e-commerce. Essa exclusão está superada pela confirmação do usuário. Não usar o desenho comercial como contrato do MVP.

Atualização posterior: o colaborador publicou `aaf08df`, incluindo marketing/e-commerce no escopo. A divergência de exclusão foi corrigida nessa revisão. O desenho comercial detalha uma frente; a prioridade de entregas e a [divisão Fabio/Thiago](DIVISAO_TRABALHO_2026-11-11.md) orientam a execução conjunta.

## Diretriz para execução

- Incluir clientes/serviços, demandas e etapas de marketing, responsáveis, prazos, comentários, anexos, revisão e conclusão.
- Incluir projetos de implantação/manutenção de e-commerce, etapas, checklists, pendências e evidências de entrega. Isso não significa desenvolver uma plataforma própria de loja.
- Definir os detalhes com a agência: jornadas reais, permissões, aprovadores, recorrência e eventual acesso externo. A inclusão das áreas não aprova automaticamente todas as funcionalidades propostas.
- Reaproveitar a base CRM/atendimento. Funcionalidades comerciais novas continuam secundárias.
- Manter WhatsApp condicionado aos fluxos aprovados. A instância de desenvolvimento continua sem pareamento, por instrução do usuário.
- Preservar os achados técnicos da revisão: isolamento de conversas, WebSocket e mídia, destinatários de transferência, timeline, replay, confirmação de envio, transporte entre processos e operação. Eles não justificam alterar a prioridade de produto.

## Backlog e calendário

As fontes para as definições e datas de entregas são [o plano de 30 tarefas](clickup/CLICKUP_DELIVERY_PLAN_2026-11-11.json) e [o cronograma](clickup/CLICKUP_SCHEDULE_2026-11-11.json). A janela de 16/11 a 14/12/2026 é provisória, com 20 dias úteis, excluindo fins de semana e 20/11.

A reconciliação do ClickUp usa os mesmos IDs e preserva status, responsáveis e descrições anteriores. Uma seção posterior de correção identifica a orientação vigente. Não apaga tarefas, listas nem publica comentários. A evidência de aplicação fica em `clickup/CLICKUP_SCOPE_CORRECTION_2026-11-11.json` depois da execução e releitura.

Esta correção registra uma decisão de produto, não comprova implementação nem homologação. As correções locais de código ainda precisam de validação e publicação separadas.
