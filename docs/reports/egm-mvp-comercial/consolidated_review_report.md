# Revisão Goldfish consolidada · CRM2

**Alvo** crm2_mvp_comercial.md, versão de 356 linhas. **Resultado** cinco etapas executadas. O desenho ainda requer resolução de achados antes de ser tratado como pronto para implementação.

| Etapa | Revisores concluídos | Relatório |
| --- | ---: | --- |
| 5 · Visão geral inicial | 2 | [Relatório inicial](zoom_out_report.md) |
| 6 · Compreensão independente | 1 | [Paráfrase e achados](comprehension_report.md) |
| 7 · Crítica da especificação | 3 | [Crítica](critic_report.md) |
| 8 · Visão geral intermediária | 1 | [Relatório intermediário](intermediate_zoom_out_report.md) |
| 9 · Prontidão de implementação | 3 | [Prontidão](implementation_readiness_report.md) |

A primeira tentativa de compreensão com Luna atingiu o limite de uso. A nova revisão com Sol low concluiu. Sol low também cobriu estrutura e estilo nesta rodada. As demais personas usaram Sol medium. O desenho permaneceu fixo durante a revisão.

## Achados consolidados e rastreabilidade

| ID | Prioridade | Ação para o desenho | Achados de origem |
| --- | --- | --- | --- |
| A01 | Blocker | Antecipar a prova da captação por anúncio para M1. Exigir amostra sanitizada ou teste autorizado que distinga entrada por anúncio, reentrega, continuação e nova entrada. Fixar identidade, disponibilidade, responsável e critério de passagem antes de congelar M2/M3. | 5-Z3, 5-C2, 6-C5, 7-D1, 9-R3 |
| A02 | Blocker | Especificar modelos e migrações com campos, valores iniciais, restrições por workspace, chaves e preservação das linhagens. Incluir matriz de testes de upgrade. | 9-R1 |
| A03 | Blocker | Fixar executor, agenda, armazenamento e evidência de backup, restauração, alerta e reversão. Separar smoke parametrizável por ambiente do aceite em produção. | 9-R5, 9-C8 |
| A04 | Major | Definir autorização por tipo de registro e preservar restrições de conversas privadas. Conferir evento próprio após transferência sem conceder acesso à conversa. Aplicar às listas, detalhe, mídia, indicadores e tempo real. Ampliar o conjunto de arquivos de M1. | 5-Z1, 5-C1, 6-C2, 7-D3, 9-C1, 9-C4 |
| A05 | Major | Especificar provisionamento, revogação e recuperação de itens do operador desativado. Fixar transporte worker→API e destinatários autorizados. | 7-D4, 9-R2, 9-C2, 9-C3, 9-S2 |
| A06 | Major | Manter contato por workspace e identidade da conversa por conta. Definir unidade de autenticação, gravação e retry por evento, com deduplicação antes de efeitos comerciais ou reabertura. | 7-D2, 8-Z1, 9-C6, 9-C7 |
| A07 | Major | Definir atendimento, retorno após encerramento, fila e reaproveitamento dos eventos. Explicitar o estado inconclusivo do envio e que o indicador exige evidência de aceitação. | 5-Z2, 5-C3, 6-C1, 7-D5, 9-C7 |
| A08 | Major | Fixar elegibilidade do vendedor e limite temporal da atribuição a uma captação, inclusive na correção. Preservar créditos históricos e testar a fronteira. | 6-C3, 8-Z2 |
| A09 | Major | Fechar dicionário dos indicadores com fuso de origem, intervalo, amostra e paginação. Total e primeira página da composição devem corresponder à mesma leitura. | 5-C4, 6-C6, 9-R4 |
| A10 | Major | Especificar corte para dados em andamento, começo dos indicadores oficiais e rotinas legadas habilitadas. Atualizar documentação de entrada quando o escopo estiver fechado. | 5-Z4, 5-Z5, 5-Z6 |
| A11 | Major | Fixar os contratos de API e os testes executáveis por bloco. Nomear ações e estados, contratos reaproveitados e a regra de lembrete único. | 9-R2, 9-R6, 9-C5 |
| A12 | Major | Organizar a arquitetura por área, padronizar a referência f6a9a22 e corrigir a descrição do diagnóstico do legado para distinguir contagem igual de métricas diferentes. | 6-C4, 7-E1, 7-E3, 7-S1, 7-S2, 9-S1 |
| A13 | Major | Completar a alternativa de reabertura com eventos históricos, preservando a decisão do autor por nova oportunidade vinculada. | 7-E2 |
| A14 | Nit | Remover redundâncias e padronizar termos de configuração, atribuição, primeira resposta e desativação de etapa. Identificar as referências legadas e mover as ressalvas para o escopo correspondente. | 6-C7, 7-E4, 7-S3, 7-S4, 7-S5, 9-S3, 9-S4 |

Não há reavaliação após correções. Os três bloqueadores consolidados tratam da prontidão para execução. A prova externa da origem de anúncio e a escolha do executor operacional seguem como dependências explícitas.
