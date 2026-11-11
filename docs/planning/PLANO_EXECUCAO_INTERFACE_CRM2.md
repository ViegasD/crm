# CRM2 — Estudo de produto e plano de execução da nova interface

11/11/2026 · Documento complementar para revisão dos contribuidores.

A **lista e a ficha de clientes** são o primeiro corte proposto para integrar dados reais. A navegação prioriza Marketing e E-commerce, com Comercial no escopo do MVP em prioridade secundária. Cada frente tem sua própria área de trabalho. A inbox é a área para atender conversas. A interface nova pode usar contratos do projeto anterior depois de validar a compatibilidade e a autorização de cada um.

## 1. Base da decisão

| Fonte | Como usar |
| --- | --- |
| [Escopo geral](../../SCOPE.md) | Define as três frentes do MVP e as decisões ainda pendentes da agência. |
| [Desenho comercial](crm2_mvp_comercial.md) e [resolução do EGM](../reports/egm-mvp-comercial/goldfish_review_report.md) | Definem os contratos de acesso, captação, oportunidades, atendimento, indicadores e verificação. Os blocos M1–M5 pertencem a essa frente. |
| [Revisão da base antiga](../reports/crm2_code_review_e_realinhamento_2026-11-11.md) e [mapa de reaproveitamento](REFERENCIAS_UI_E_REUSO_CRM2.md) | Classificam o código existente. Use a revisão `f6a9a22` como referência histórica do [PR #1](https://github.com/ViegasD/crm/pull/1). Confirme a branch comum e o commit antes de implementar. |
| ClickUp, pasta CRM2 | Fila de execução e aceite atual. MVP 02 é clientes e serviços, MVP 03 é marketing, MVP 04 é e-commerce, MVP 07 é auditoria e contratos, e MVP 08 reúne o rework do frontend. Confirme títulos e dependências antes de usar códigos de relatórios históricos. |

A visita à VPS mostrou o produto anterior à reformulação, com login, contatos, inbox, supervisão e configuração. O estudo dos concorrentes usa os guias públicos e seus exemplos de interface. Os fluxos internos de cada produto não foram testados em contas autenticadas. As escolhas de interface abaixo complementam o EGM. Onde o escopo ainda depende da agência, a proposta está marcada como tal.

## 2. Estudo das oito referências

### Attio — ficha de cliente e navegação entre registros

**Interface.** A tabela e o Kanban abrem uma prévia à direita e mantêm o item selecionado visível. A ficha completa separa atributos, atividade, tarefas e relações em áreas distintas.

**Funcionamento.** Lista, quadro, prévia e ficha representam o mesmo registro. Relações como empresa, pessoa e negócio podem ser percorridas sem duplicar os dados do cadastro.

**Aplicação.** No CRM2, abrir o cliente da lista ou de um item vinculado, manter a origem da navegação e permitir voltar ao mesmo recorte. A ficha tem identificação no cabeçalho e seções de trabalho relacionadas. A API continua aplicando a permissão de cada registro relacionado. O primeiro corte terá seções fixas.

Material visual e fluxo: [registros, prévia e relações](https://attio.com/help/reference/managing-your-data/records/create-and-view-records).

### monday.com — funil e quadros de operação

**Interface.** O quadro comercial mostra oportunidade, etapa, responsável, cliente e valor. O Kanban organiza as oportunidades por etapa. Os detalhes permanecem acessíveis a partir do quadro. No Work Management, pedidos podem entrar por formulário e passar por revisão antes de virar trabalho.

**Funcionamento.** A mudança de coluna atualiza a etapa do negócio. Tabela e Kanban são visões da mesma oportunidade. Projetos operacionais têm seus próprios fluxos.

**Aplicação.** Adotar lista e quadro sobre a mesma consulta autorizada no Comercial. Adotar o padrão visual de colunas também no Marketing, com regras próprias de demanda. Mostrar total por etapa e permitir carregar a continuação. No Comercial, oferecer uma ação de mudança de etapa acessível pelo teclado, além de arrastar. Previsão ponderada e editor de automações ficam para uma decisão posterior.

Material visual e fluxo: [quadro de vendas](https://support.monday.com/hc/en-us/articles/360013348719-Sales-pipeline-management-with-monday-CRM) e [fluxo de projetos](https://support.monday.com/hc/en-us/articles/360014437599-Project-management-with-monday-com).

### ClickUp — revisão de entregáveis de marketing

**Interface.** A tarefa reúne descrição, anexos e atividade. A prévia do arquivo permite deixar comentários no contexto da peça. O status informa se ela está em produção, em revisão ou aprovada.

**Funcionamento.** A pessoa responsável envia a peça para revisão. O revisor devolve com feedback ou aprova. O ciclo se repete enquanto houver ajustes.

**Aplicação.** O detalhe da demanda reúne briefing, responsável, prazo, anexo e histórico. Proposta inicial: apontar qual versão foi revisada e oferecer **Pedir ajuste** e **Aprovar** conforme o papel. Preservar a versão anterior quando houver reenvio. Validar com a agência se aprovação e conclusão são momentos separados. Comentários ancorados na imagem, edição colaborativa e portal externo ficam fora do primeiro recorte.

Material visual e fluxo: [fluxo de revisão](https://help.clickup.com/hc/en-us/articles/6328033402007-Use-ClickUp-for-design-reviews) e [prévia de anexos](https://help.clickup.com/hc/en-us/articles/6325985679383-Annotate-images-videos-and-PDFs-with-Proofing).

### Linear — visão geral e marcos de projeto

**Interface.** A visão geral concentra responsável, status, prazo, recursos e marcos. A lista de trabalho dá acesso às tarefas. O progresso do marco aparece junto das tarefas vinculadas.

**Funcionamento.** Um marco representa uma entrega intermediária. O progresso reflete o trabalho relacionado, e a visão de projeto mostra onde a equipe está no percurso.

**Aplicação.** Na ficha de e-commerce, mostrar status, responsável, prazo, próximo marco e pendências do marco. Deixar o checklist por fase em uma área própria. Se houver progresso numérico, mostrar a composição por itens e manter a decisão de entrega explícita. Gráficos de projeção, ciclos e portfólio avançado ficam para depois.

Material visual e fluxo: [visão de projeto](https://linear.app/docs/projects) e [progresso por marco](https://linear.app/docs/project-milestones).

### Teamwork — hierarquia de cliente, projeto e checklist

**Interface.** A área de projetos agrupa trabalho por cliente. Dentro do projeto, listas de tarefas organizam as fases e podem ser ligadas a marcos. A criação a partir de modelo reaproveita uma estrutura definida.

**Funcionamento.** Um cliente pode ter vários projetos simultâneos. As tarefas permanecem vinculadas à sua fase. Um modelo oferece uma estrutura de partida para projetos repetidos.

**Aplicação.** Todo projeto de loja aponta para um cliente e, quando a regra da MVP 02 exigir, para o serviço contratado. Validar primeiro um checklist de implantação ou manutenção com a agência. Uma estrutura inicial reutilizável pode entrar depois de confirmadas as fases comuns. Faturamento, horas faturáveis e gestão de capacidade permanecem fora deste recorte.

Material visual e fluxo: [hierarquia de trabalho](https://support.teamwork.com/projects/efficiency/hierarchy-of-information-in-teamwork) e [modelos de projeto](https://support.teamwork.com/projects/project-templates/creating-project-templates).

### Intercom — caixa de entrada com contexto

**Interface.** As filas ficam na navegação de atendimento. A conversa ocupa o centro. O painel de detalhes mostra contexto do contato e da empresa ao lado da conversa. A pessoa operadora pode consultar esses dados enquanto responde.

**Funcionamento.** Uma conversa tem estado e responsável. Pode entrar na fila de uma equipe, ser assumida ou transferida. A caixa permite voltar ao conjunto de conversas filtrado.

**Aplicação.** Manter as três áreas no desktop dentro de Atendimento. No celular, passar de fila para conversa e abrir detalhes sob demanda. Mostrar responsável, status e acesso à ficha do cliente. O modo de visibilidade, a conversa privada e o histórico autorizado seguem o EGM. Personalização de painéis e automações de suporte ficam para avaliação futura.

Material visual e fluxo: [layouts da inbox](https://www.intercom.com/help/en/articles/7911926-customize-the-inbox-to-suit-you-and-how-you-work-best) e [painel de detalhes](https://www.intercom.com/help/en/articles/6546031-customize-the-inbox-with-apps).

### HighLevel — WhatsApp com múltiplos números

**Interface.** O campo de resposta deixa o número de saída visível. Em uma conversa com sessão ativa, o número vinculado aparece como a identidade de envio.

**Funcionamento.** O produto escolhe a identidade para a conversa ativa, mantém estados separados e apresenta o envio por modelo quando a regra do canal exige. Isso reduz troca acidental de remetente.

**Aplicação.** Mostrar o número da conta na fila e no compositor. O filtro muda quais conversas são vistas. O servidor escolhe a conta de envio a partir da conversa e valida janela e modelo. Uma tentativa inconclusiva aparece como pendente de confirmação, conforme o desenho. O teste de interface usa contas sintéticas. A homologação exige dois números oficiais autorizados.

Material visual e fluxo: [seleção de remetente e destinatário](https://help.gohighlevel.com/support/solutions/articles/155000007598).

### HubSpot — indicadores que abrem os registros

**Interface.** Um ponto do gráfico permite abrir os registros que compõem o resultado e seguir para o detalhe de uma linha.

**Funcionamento.** A interação transforma um agregado em uma lista de registros. A investigação parte do período e do recorte do relatório.

**Aplicação.** Cada indicador do CRM2 mostra seu recorte e oferece **Ver registros**. No Comercial, a API retorna base, total e composição conforme o desenho. Para Marketing e E-commerce, primeiro definir o evento ou estado que cada indicador mede. Separar fila atual de eventos do período. Quando não houver denominador, informar que não há base para a taxa.

Material visual e fluxo: [detalhamento de relatórios](https://knowledge.hubspot.com/dashboards/drill-down-into-dashboard-reports).

## 3. Organização da interface e jornadas

### Navegação proposta

| Entrada | Tela inicial | Como o usuário segue |
| --- | --- | --- |
| Clientes | Lista com busca e ficha do cliente | Abrir serviço, pessoa de contato, oportunidade, demanda ou projeto autorizado. |
| Marketing | Quadro de demandas | Abrir briefing, editar trabalho, enviar peça para revisão e ver a decisão. |
| E-commerce | Lista de projetos | Abrir visão geral, conferir próximo marco e concluir itens de checklist. |
| Comercial | Leads, funil e tarefas | Registrar captação, vincular ao cliente/contato, movimentar negócio e registrar desfecho. |
| Atendimento | Fila de conversas | Selecionar conversa, identificar o número, responder ou transferir, abrir a ficha. |
| Indicadores | Comercial e operação | Aplicar recorte, abrir composição e navegar ao item. |
| Configurações | Acesso e administração | Gerenciar equipe, regras e contas conforme as permissões do workspace. |

O ponto de partida recomendado para o primeiro corte é **Clientes**, que já tem um contrato de leitura na base antiga. A navegação mostra os módulos conforme forem integrados. O protótipo pode usar dados fictícios das três frentes e deve identificar as telas simuladas. A primeira versão integrada mostra apenas informações persistidas, autorizadas e compatíveis com a versão da API.

### Estrutura da ficha

```text
Workspace / Clientes / Cliente
Nome do cliente                         Ação principal conforme permissão

Visão geral | Comercial | Marketing | E-commerce | Atendimento

Contatos e serviços                     Trabalho em andamento
Pessoas de contato                      Negócio e próximo passo
Serviços vinculados                     Peça aguardando revisão
                                        Próximo marco do projeto
```

A ficha começa com identificação e contatos. A seção de serviços entra assim que o vínculo da MVP 02 estiver definido. As demais abas entram conforme seus contratos forem entregues. Cada linha relacionada aponta para uma tela com endereço próprio. No desktop, a prévia pode abrir ao lado da lista. No celular, o detalhe ocupa a tela e oferece retorno à lista, preservando o filtro.

### Comportamentos compartilhados

- **Consulta.** Exibir carregamento, ausência de registros, nenhum resultado para o filtro e falha de carregamento de maneiras distintas. Oferecer nova tentativa em caso de erro e criação apenas quando autorizada.
- **Edição.** Mostrar a ação primária no contexto, validar campos antes do envio e exibir a resposta do servidor junto ao formulário. Em conflito, recarregar o estado atual e explicar o que mudou. O estado persistido vem da API.
- **Acesso.** Mostrar leitura ou edição conforme a permissão. Ao trocar workspace ou revogar vínculo, limpar o estado anterior, inclusive listas, detalhes e inscrições de eventos. Relações visíveis na ficha não concedem acesso aos registros ligados.
- **Navegação e acessibilidade.** Preservar busca e filtros ao voltar. Garantir foco e retorno de foco, rótulos para ícones, alternativa a arrastar e significado de status além da cor. Testar teclado, desktop e celular.

## 4. Como implementar sobre a fundação existente

| Camada | Reaproveitar | Adaptar ou construir |
| --- | --- | --- |
| Sessão e acesso | Login, refresh, vínculo de workspace, cliente HTTP e chamadas de sessão. | Rever tipos, estados de sessão, autorização de detalhe/lista, mídia e revogação. O [contrato M1](crm2_mvp_comercial.md#contratos-de-acesso-e-api--m1m4) governa o comportamento. |
| Contatos e cadastro operacional | Modelo de contato e CRUD da base. | Alinhar o formulário a `person` e `organization`, que são os valores do backend auditado. Fechar a ligação cliente–contato–serviço antes da migração. O campo textual `company` não identifica uma organização por chave. |
| Navegação e componentes | Cliente HTTP, tipos e funções que passarem na verificação. Componentes neutros podem ser aproveitados quando atenderem ao novo padrão de interação. | Refazer layout autenticado, sidebar, lista e ficha. Organizar os componentes novos em torno das telas das três frentes. Usar um único padrão de tabela, filtros, estados e detalhe até que haja motivo verificável para separar. |
| Comercial | Contato, timeline de atendimento como base parcial e notificações internas como infraestrutura a avaliar. | Implementar a captação, o funil, as oportunidades e tarefas com os contratos M2. O tipo antigo `Lead` no formulário não é um evento de captação. |
| Marketing e e-commerce | Identidade de usuário, workspace, cliente/serviço quando disponível, infraestrutura de mídia depois dos ajustes de autorização. | Criar dados, operações e telas próprios de demanda, revisão, projeto, marco e checklist. Etapas, ações e responsabilidades dependem da validação operacional. Reusar padrões de UI entre quadros sem unificar suas máquinas de estado. |
| Atendimento | Contas de canal, conversas, mensagens, identidade do provedor e adaptadores existentes. | Refazer a UI, corrigir autorização e histórico, verificar a seleção de conta no recebimento/envio e aplicar o contrato M3. Conferir a compatibilidade do cliente de tempo real antes de reaproveitar. |
| Relatórios e implantação | Migrações, smoke e infraestrutura de desenvolvimento. | Construir indicadores e composição. Entregar evidência de upgrade, backup, restauração, alertas e reversão conforme M5. |

Os arquivos e contratos comerciais já estão listados no [plano técnico do EGM](crm2_mvp_comercial.md#detailed-implementation-plan). Para iniciar a nova UI, os pontos a conferir na base são `frontend/src/lib/api.ts`, `frontend/src/stores/auth-store.ts`, o layout em `frontend/src/app/(dashboard)/layout.tsx`, as páginas de contato e `backend/app/api/v1/contacts.py`. Marketing e e-commerce devem ganhar contratos e arquivos próprios após a agência confirmar seus estados e permissões. Registrar na tarefa de cada PR os arquivos, rotas e migrações a alterar.

### Dados que a UI precisa receber

| Tela | Dados mínimos | Regra do contrato |
| --- | --- | --- |
| Lista e ficha de cliente | Identificador, nome, contatos, serviços autorizados e referências aos itens relacionados disponíveis. | Preservar a identidade do contato existente. Escolher a identidade de cliente na MVP 02 antes de consolidar vínculos. |
| Quadro comercial | ID, etapa, cliente/contato, responsável, valor, total por etapa e paginação. | Usar as rotas de oportunidade e etapa previstas em M2. O servidor valida o movimento e sua autoria. Lista e total usam o mesmo conjunto autorizado. |
| Demanda | ID, vínculo com cliente/serviço conforme regra aprovada, etapa, responsável, prazo, briefing, comentários, anexos e decisão da revisão. | Associar decisão a quem revisou e à peça revisada. A transição válida é definida após observar o fluxo real. |
| Projeto | ID, cliente/serviço conforme regra aprovada, estado, prazo, responsável, marcos, itens do checklist e evidências. | Cada item pertence ao projeto e à fase pertinente. A regra que permite concluir o projeto deve ser aprovada antes da escrita. |
| Conversa | ID, contato, conta do número, responsável, estado, mensagens, permissões e status de envio. | A API valida conta, visibilidade e transição. Confirmar um envio apenas com evidência correlacionável. |
| Indicador | Valor, período ou posição atual, filtros, total de registros e página de composição. | Usar o mesmo recorte e autorização na consulta e no detalhe. A definição comercial já consta no EGM. As métricas operacionais dependem de estados e eventos aprovados. |

## 5. Ordem de entrega e divisão entre contribuidores

| Passo | Frontend | Backend e dados | Saída verificável |
| --- | --- | --- | --- |
| 1. Validar jornadas e base | Desenhar um caso de cliente que percorra as três frentes, com estados vazio, erro e permissão insuficiente. | Confirmar commit comum, rodar verificações da base, conferir papéis e validar o caminho de migração em banco descartável. | Roteiros da MVP 00 anotados, base de trabalho confirmada e decisões pendentes identificadas. |
| 2. Entregar lista e ficha | Implementar shell, lista de clientes e detalhe usando a leitura existente. Conectar edição conforme contrato. | Fechar a relação cliente–contato–serviço, corrigir a incompatibilidade do formulário e validar autorização em lista e detalhe. | Operador abre uma ficha real de teste, volta ao filtro e vê apenas os dados autorizados. |
| 3. Entregar o primeiro fluxo ligado ao cliente | Construir lista/quadro e detalhe para o fluxo validado. Exibir o vínculo na ficha. | Criar os contratos e eventos mínimos desse fluxo. Sugestão de primeiro recorte: demanda de marketing ligada a um serviço com criação, atribuição e revisão interna, se os papéis já estiverem definidos. | Um item pode ser criado, encontrado na área de trabalho e aberto pela ficha. A alteração autorizada fica registrada. |
| 4. Completar os fluxos das três frentes | Aplicar os padrões de lista e detalhe ao funil e ao projeto de loja, e completar as ações de marketing aprovadas. | Entregar M2 comercial, completar o fluxo de demanda e entregar projetos, marcos e checklist conforme as listas correspondentes. | Homologar um negócio, uma peça que volta para ajuste e um projeto de loja com checklist. |
| 5. Integrar atendimento | Implementar fila e conversa, número de saída, filtro e estados do compositor. | Implementar os contratos M3 após validação dos acessos, do fluxo de canal e das regras de conta/evento. | Interface verificada com dados sintéticos. Homologação em dois números oficiais registrada à parte. |
| 6. Integrar indicadores e publicar | Exibir indicadores e composição, validar navegação e responsividade em dados reais de teste. | Implementar consultas com as regras de cada frente, preparar migrações e operação conforme M4/M5. | Valores reconciliados com registros, ambiente homologado e evidências de restauração e reversão registradas. |

A numeração representa dependências de implementação. Priorizar a integração de Marketing e E-commerce depois da ficha compartilhada. O Comercial permanece no MVP e pode avançar em paralelo conforme capacidade e contratos estáveis. A escolha do primeiro fluxo do passo 3 depende da agência e do ClickUp. A busca de evidência sobre os números oficiais começa junto da fundação. As janelas do backlog são provisórias e a reestimativa passa por UI01 e AUD08.

Cada PR deve ligar uma tarefa, um fluxo e sua evidência. O colaborador do frontend pode desenhar e preparar estados simulados enquanto o outro fecha a API. A integração usa o mesmo cenário de teste. Na troca de tarefa, registrar o PR, o que já foi verificado e a próxima ação. Evitar dois PRs concorrentes alterando o mesmo contrato.

## 6. Aceite mínimo e decisões antes de implementar

### Roteiro de homologação

| Cenário | Resultado esperado |
| --- | --- |
| Cliente comum | Abrir o mesmo cliente da lista e de um item vinculado. Voltar à lista com o filtro preservado. Exibir apenas relações autorizadas. |
| Isolamento | Usar dois workspaces e perfis diferentes. Conferir lista, URL direta, alteração e mídia. Para Atendimento, incluir sessão aberta e eventos após revogação. |
| Comercial | Registrar captação, vincular negócio, mover etapa e fechar conforme o desenho. Conferir contagem e acesso em etapa com mais de 500 oportunidades. |
| Marketing | Criar demanda, atribuir, anexar, solicitar revisão, pedir ajuste e conferir a decisão da versão final. Validar as ações com os papéis acordados. |
| E-commerce | Criar um projeto de teste, localizar o próximo marco, executar o checklist e registrar uma evidência de entrega. |
| Atendimento | Demonstrar separação de contas e número correto no compositor, status de envio e transferência. Registrar em separado o resultado com dois números oficiais. |
| Indicadores | Comparar valor, base e lista sob o mesmo filtro. Verificar que um registro oculto também fica fora do agregado. |
| Nova interface | Rodar type-check, lint e build. Fazer o roteiro em desktop e celular, com teclado e estados vazios, de erro e de acesso insuficiente. |

Durante a transição, conservar a navegação antiga no ambiente de desenvolvimento até a nova rota equivalente passar no roteiro. Publicar por fluxo validado conforme o plano de implantação. A retirada de rotas, componentes e dados do legado exige conferência de consumidores e evidência de regressão em mudança própria.

### Decisões que o estudo não fecha

- **Cliente e serviços.** Definir se o cliente operacional é um contato de organização ou um cadastro próprio ligado a contatos. Confirmar serviços iniciais e vínculos obrigatórios antes de criar migrações.
- **Marketing.** Confirmar etapas, quem revisa, quando a entrega é concluída, recorrência e eventual participação externa. O primeiro protótipo pode mostrar revisão interna como hipótese.
- **E-commerce.** Confirmar fases, checklist real, evidência de entrega e quando um marco pode ser considerado concluído.
- **WhatsApp.** Confirmar números, modelos, regra de retorno após encerramento e evidência do sinal de anúncio conforme a resolução do EGM.
- **Operação.** Confirmar definições dos indicadores de entrega, corte dos registros antigos, ordem de homologação e responsáveis por backup, restauração e alertas.

As decisões pendentes entram nas tarefas correspondentes. Este documento é um plano de execução e referência de interface. A evidência de funcionamento virá dos testes e da homologação de cada frente.

## 7. Vínculo com as tarefas de UI no ClickUp

Os critérios e as dependências de cada tarefa ficam no ClickUp. A aprovação do protótipo na UI01 e a liberação da base na AUD08 são verificações distintas.

| Tarefa | Onde aplicar este estudo |
| --- | --- |
| UI01 · Jornadas e direção visual | Usar o estudo de produto e o [mapa de reaproveitamento](REFERENCIAS_UI_E_REUSO_CRM2.md) para validar a matriz e preparar o protótipo desktop/mobile de navegação, marketing, e-commerce, inbox e painel. |
| UI02 · Shell e navegação | Implementar a hierarquia e os comportamentos compartilhados da seção 3. Priorizar Marketing e E-commerce e usar os estados de carregamento, vazio, erro e permissão. |
| UI03 · Login, perfil e equipe | Aplicar o contrato de sessão da seção 4. A UI distingue ausência de workspace, sessão expirada e acesso insuficiente. Revogação e provisionamento seguem as tarefas de fundação. |
| UI04 · Contatos e timeline | Usar a ficha inspirada no Attio e preservar busca, paginação e histórico autorizado. A UI04 trata contatos e timeline. O cadastro operacional de clientes e serviços segue em D02.2. |
| UI05 · Inbox | Usar os padrões Intercom/HighLevel da seção 2. Combinar conta, status, busca e paginação no servidor. O aceite da tarefa também cobre visões salvas, ações em lote e eventos do worker. |
| UI06 · Notificações | Consumir listagem e marcação como lida existentes. Usar estado vazio, erro, paginação e limpeza ao mudar de workspace. Cada link abre um registro autorizado. Menções continuam como fluxo próprio. |
| UI07 · Configurações | Agrupar administração por tarefa do usuário. Preservar as capacidades existentes verificadas e expor os diagnósticos previstos no aceite conforme papel. |
| UI08 · Flow Builder | A tarefa é secundária e se aplica se a tela for mantida. Preservar grafo e status no contrato de ida e volta. Se o executor estiver indisponível, mostrar o rascunho e a indisponibilidade da ativação. |
| UI09 · Supervisor | Usar os padrões de filtro, estado e composição de indicadores. Distinguir supervisão de atendimento e recursos existentes de SLA/CSAT/heatmap dos novos indicadores de entrega em D05.1/API01. |
| UI10 · Revisão de marketing | Aplicar o padrão ClickUp da seção 2 às transições e permissões reais de D03.3/D03.4. Confirmar ajuste, aprovação, reabertura e conclusão conforme D00.2. |
| D02.2 · Clientes e serviços | Aplicar a lista e ficha operacional após fechar o vínculo cliente–contato–serviço. |
| D03.2 · Quadro de demandas | Usar o padrão de quadro e detalhe para criação, atribuição e Kanban de Marketing. |
| D04.2 · Projeto e checklist | Aplicar a visão de projeto do Linear e o agrupamento por fase e marco do Teamwork. |
| D05.1 · Indicadores de entregas | Aplicar o padrão de composição do HubSpot à operação. A API e a reconciliação ficam na API01. |
