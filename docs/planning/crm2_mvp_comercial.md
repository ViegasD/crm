# CRM2 — MVP comercial da agência

- **Autor** ViegasD
- **Estado** Revisado no EGM, com dependências de execução registradas
- **Data** 2026-11-11

## Overview

O CRM2 será entregue primeiro para a operação comercial interna da agência. Administradores configuram o acesso e o funil. Operadores cadastram leads, acompanham negócios e tarefas e atendem conversas individuais de WhatsApp. A equipe consegue conferir os indicadores a partir dos registros que os compõem. O MVP usa o workspace como unidade de isolamento e de configuração da empresa, com verificação de separação de dados desde a primeira entrega.

O plano segue os cinco blocos da proposta comercial, com estimativa de 20 dias úteis após aprovação do escopo e disponibilização dos acessos. A janela provisória é de 16/11 a 14/12/2026. A elegibilidade e a disponibilidade dos números oficiais precisam ser verificadas desde a fundação.

## The Problem

No CRM anterior, a contagem no cabeçalho do Kanban divergia da quantidade de cartões exibidos, e telas diferentes exibiam valores comerciais com rótulos e regras distintos. O MVP precisa tornar a paginação e a composição dos indicadores verificáveis.

O MVP deve permitir acompanhar cada negócio desde o lead até o desfecho e consultar o histórico das ações. A confiança nos dados precisa ser construída junto com a funcionalidade. Para cada indicador, a equipe deve saber quais registros entram no cálculo, qual recorte foi aplicado e por que o total tem aquele valor.

## Goals

| Entrega | Resultado verificável |
| --- | --- |
| **Fundação, login e usuários** | Um administrador cria e desativa um operador. A aplicação e o servidor aplicam as permissões de cada papel. Os eventos essenciais ficam registrados. |
| **Isolamento entre empresas** | Com dois workspaces fictícios, um usuário de uma empresa não consegue consultar, editar, receber em tempo real ou contabilizar registros da outra, mesmo quando as duas usam o mesmo telefone de contato. Cada empresa pode ter seu próprio funil e padrão de visibilidade. |
| **Leads, contatos, oportunidades e funil** | O CRM cria automaticamente o lead quando identifica uma entrada por anúncio. O operador também pode cadastrar, editar e localizar leads e contatos, informar a origem, vincular um lead a um negócio e mover o negócio no Kanban. Oportunidades têm valor, responsável e status. O administrador configura as etapas. Contagem, busca e acesso aos cartões respeitam os mesmos filtros, inclusive em uma etapa com mais de 500 oportunidades. |
| **Atividades e tarefas** | O operador registra observações, cria uma tarefa com responsável e prazo, recebe o lembrete no CRM e consegue consultar e concluir a tarefa. |
| **WhatsApp oficial multinúmero** | Com pelo menos dois números elegíveis conectados, a equipe envia e recebe mensagens individuais em ambos, identifica e filtra pelo número, vincula o contato, atribui e transfere atendimentos e acompanha seu status. O histórico começa na ativação. O envio respeita a janela e os modelos aprovados quando aplicáveis. |
| **Indicadores verificáveis** | O painel apresenta total de leads, oportunidades por etapa, negócios concluídos, valores registrados, conversão e indicadores básicos de atendimento por número e atendente. Cada métrica define fonte, regra, período, filtros e acesso. Durante a implementação, testes com dados conhecidos verificam o valor esperado e os registros que entram no total. Os registros podem ser conferidos no sistema sob os mesmos filtros. |
| **Produção e homologação** | A equipe acessa a aplicação publicada em computador e celular e executa os fluxos principais. A entrega inclui configuração inicial, backup automatizado, teste de restauração, monitoramento básico, correções da homologação e orientação inicial. |

## Non-Goals

- Financeiro completo, gestão de contratos, cobranças, integração com Asaas, projetos de marketing e e-commerce.
- Implantação comercial em outras empresas, portal de revenda, gestão de carteira de empresas e vendedor compartilhado entre empresas. O MVP tem uma agência em produção e testa o isolamento entre workspaces.
- Migração integral de dados e importação retroativa de conversas. Uma eventual carga inicial selecionada precisa de decisão própria.
- Chatbots de IA, automações avançadas, campanhas em massa e grupos de WhatsApp.
- Aplicativos nativos, suporte 24 horas e SLA avançado.

## Open Questions

- **M1 · Canal oficial.** A agência libera o acesso autorizado e indica os dois números e os modelos necessários. Obter a prova de identificação de captação por anúncio descrita no plano antes de congelar o contrato entre M2 e M3.
- Confirmar a revisão de partida antes da implementação. A base publicada `f6a9a22` foi inspecionada e usada no plano por arquivo. Preservar o trabalho local do Stage 5.
- **Validação com a agência.** Confirmar o tratamento de nova mensagem após atendimento concluído e o destino da carteira já em andamento. O aceite do MVP usa cadastro e captação nativos. Uma carga inicial selecionada, se necessária, exige escopo e reconciliação próprios.
- **M5 · Produção.** Confirmar executor e destino do backup e responsáveis pelos alertas no ambiente autorizado antes de fechar o plano de publicação.

## Critical User Journeys

### Do cadastro ao negócio

- **Dado** um operador com acesso e um funil configurado.
- **Quando** ele registra um lead, vincula uma oportunidade e move o negócio de etapa.
- **Então** a oportunidade aparece na etapa correta, com responsável e valor, e a movimentação pode ser conferida no histórico. Busca e contagem aplicam os mesmos filtros.

### Atendimento por dois números

- **Dado** que dois números elegíveis estão conectados e que o mesmo contato pode falar com ambos.
- **Quando** chegam mensagens, o operador responde em cada conversa e transfere um atendimento.
- **Então** a caixa de entrada permite distinguir e filtrar os números, as respostas saem pela conta correta e o histórico preserva os vínculos.

### Conferência dos indicadores de atendimento

- **Dado** um conjunto de atendimentos com início, encerramento, transferência, mensagens pendentes e tentativas de resposta aceitas e rejeitadas.
- **Quando** a equipe seleciona um período e filtra por número ou operador.
- **Então** o volume de atendimentos iniciados e concluídos confere com os respectivos eventos do período. A fila é identificada como a situação atual. O tempo de primeira resposta é medido entre a primeira mensagem recebida no atendimento e a primeira resposta humana aceita pelo WhatsApp. Tentativas rejeitadas não encerram a espera. Total e detalhe podem ser conferidos com os mesmos dados e permissões.

Se um operador é responsável no início, outro envia a primeira resposta aceita e um terceiro conclui, cada evento aparece no recorte do operador correspondente. A transferência muda a fila atual e preserva os créditos de eventos anteriores. Se houver uma venda, o crédito comercial segue a atribuição registrada na oportunidade.

### Captação por anúncio

- **Dado** um canal comercial da agência e uma entrada cuja origem por anúncio é identificável.
- **Quando** o CRM recebe uma entrada por anúncio, o provedor reentrega o mesmo evento e depois chega uma segunda entrada distinta por anúncio para o mesmo contato e serviço.
- **Então** existem dois leads vinculados ao mesmo contato, cada um com sua data e origem. A reentrega e as mensagens de continuidade ficam fora da contagem de novas captações. O teste deve cobrir também a segunda entrada enquanto o primeiro lead estiver aberto.

### Conferência de um indicador

- **Dado** um conjunto conhecido de registros com diferentes datas e responsáveis.
- **Quando** a equipe aplica um filtro no painel e consulta os registros que compõem o número.
- **Então** os registros respeitam o mesmo recorte e a regra de cálculo produz o valor mostrado. O teste é executado durante a implementação da métrica.

O teste de conversão inclui um lead captado em outubro que recebe crédito por um negócio ganho em novembro. Ele contribui para a conversão das captações de outubro e para a taxa de ganho dos negócios encerrados em novembro. Duas oportunidades ganhas atribuídas ao mesmo lead contam como duas oportunidades e um lead convertido.

### Retomada de uma negociação perdida

- **Dado** que uma oportunidade foi encerrada como perdida em outubro.
- **Quando** a negociação volta em novembro e o operador a retoma até ganhar.
- **Então** a nova oportunidade fica vinculada à anterior. Outubro mantém o negócio perdido, novembro registra o novo negócio ganho e somente a tentativa ganha conta como venda.

### Atribuição comercial quando há mais de uma captação

- **Dado** um contato com duas captações anteriores à abertura da oportunidade.
- **Quando** o operador abre a oportunidade e depois seleciona outra captação do mesmo contato.
- **Então** a seleção inicial usa a captação anterior mais recente, a troca fica no histórico e cada captação preserva a data e a origem registradas. A troca muda o crédito de origem do negócio e a contagem continua sendo uma oportunidade.

### Correção da origem após o fechamento

- **Dado** um negócio concluído com crédito atribuído a uma captação incorreta.
- **Quando** o administrador escolhe outra captação do mesmo contato e informa o motivo.
- **Então** a correção registra autor, horário, motivo e atribuições anterior e nova. A venda é reatribuída no relatório do seu período original, com a mesma data e o mesmo total de vendas. Um operador ou uma solicitação sem motivo não consegue aplicar a correção.

### Crédito do vendedor no fechamento

- **Dado** uma oportunidade aberta e um usuário autorizado a encerrá-la.
- **Quando** ele marca o negócio como ganho.
- **Então** precisa escolher explicitamente quem recebe o crédito comercial. Sem essa seleção, o fechamento não é confirmado. O indicador de vendas por vendedor mostra um único crédito, mesmo que outra pessoa seja responsável pela oportunidade ou tenha feito o atendimento.

### Operação com carteira individual ou visão compartilhada

- **Dado** um operador com visibilidade individual ou compartilhada, um registro atribuído a outra pessoa e um item sem responsável.
- **Quando** ele consulta o funil e a inbox em cada modo, tenta editar o registro alheio e assume o item sem responsável.
- **Então** a carteira individual oculta o registro alheio, enquanto a visão compartilhada permite consultá-lo sem editar. Uma exceção individual substitui o padrão da agência nos dois sentidos. Ao remover a exceção, o operador volta a herdar o padrão vigente. Nos dois modos, o operador pode assumir o item sem responsável, e os indicadores e seus detalhes aplicam o mesmo escopo de acesso.

### Isolamento entre duas empresas

- **Dado** dois workspaces de teste com equipes, contas de canal simuladas, etapas e padrões de visibilidade diferentes, e um mesmo telefone registrado como contato nos dois.
- **Quando** um usuário lista ou consulta registros por identificador, abre um indicador ou recebe uma atualização da inbox, e o sistema processa um evento de WhatsApp ou uma tarefa agendada.
- **Então** o acesso, as consultas, as gravações e as atualizações respeitam o workspace da operação. Um vínculo de usuário, um lead ou um contato de outra empresa não pode ser usado para ligar registros entre os dois workspaces. Cada empresa aplica suas próprias configurações e seus totais reconciliam somente com seus registros autorizados.

### Desativação de uma etapa ocupada

- **Dado** uma etapa que o administrador quer remover do quadro, com oportunidades abertas.
- **Quando** o administrador bloqueia novas entradas, os operadores podem continuar trabalhando nas oportunidades existentes até esvaziá-la. Se o administrador quiser remover a etapa antes disso, ele pode escolher uma etapa ativa de destino e mover as oportunidades restantes na mesma operação.
- **Então** a etapa deixa de receber novos negócios, e só sai do quadro ativo depois de esvaziada. O histórico continua consultável. A movimentação em massa feita para remover a etapa é registrada como ajuste administrativo, sem contar como avanço comercial.

## Technical Plan (Architecture)

A proposta é evoluir a base existente. A revisão publicada `f6a9a22` tem autenticação, vínculo por workspace, contatos, conversas, contas de canal, transferência, filtro de conversas por conta e envio pelo adaptador de WhatsApp. O plano detalhado usa a árvore publicada. A validação em execução, incluindo dois números oficiais, continua como parte do aceite.

### Empresa, identidade e captação

**Isolamento e configuração por empresa.** Um workspace representa uma empresa. Contatos, captações, oportunidades, tarefas, etapas, conversas, números, eventos e indicadores operam dentro desse escopo. O papel de administrador vale para o workspace ao qual pertence. A API verifica o vínculo do usuário, as rotinas em segundo plano usam o workspace do registro ou da conta validada e as atualizações em tempo real aplicam o mesmo acesso da inbox. Vínculos e identificações comerciais são resolvidos dentro do workspace, inclusive ao localizar um contato pelo telefone. No WhatsApp, a conta do número identifica o workspace que recebe o evento.

O funil, o fuso e o padrão de visibilidade são configurados no workspace. O MVP aplica a política de captação por anúncio da agência no serviço de captação, com escopo de workspace. A configuração dessa política para canais mistos fica para uma etapa futura. A definição comum de venda, seu fechamento e sua composição permanecem verificáveis mesmo quando as empresas usam regras de captação diferentes.

O **contato** representa a pessoa ou empresa. O **lead** representa uma captação comercial, com data e origem próprias. Um contato pode ter vários leads. A **oportunidade** representa o negócio no funil e guarda o vínculo com o lead que a originou, quando houver. Assim, uma segunda captação mantém sua origem e data sem duplicar o contato nem sobrescrever a captação anterior.

**Criação automática por anúncio.** No uso atual da agência, a entrada de WhatsApp serve à captação comercial. Cada entrada distinta com origem de anúncio identificada cria um lead sem depender de confirmação do operador, mesmo com outro lead aberto para o contato e serviço. A data e a origem de cada captação ficam preservadas. Reprocessar o mesmo evento produz uma única captação, e mensagens de continuidade ficam no histórico. A contagem de leads mede captações; a contagem de oportunidades mede negócios.

**Atribuição de oportunidade.** Ao abrir uma oportunidade, o CRM associa a captação mais recente do mesmo contato ocorrida antes da abertura, quando houver. O operador pode escolher ou trocar a captação atribuída. Cada troca registra a seleção anterior, a nova, o responsável e o horário. A seleção fica salva na oportunidade, de modo que uma captação posterior não mude o crédito automaticamente. O indicador por origem usa a captação atribuída, com um único crédito por oportunidade.

**Correção após o fechamento.** Enquanto o negócio está aberto, o operador pode trocar a atribuição. Depois do fechamento, apenas o administrador pode corrigi-la, com motivo obrigatório. A alteração audita o autor, o horário, o motivo e as captações anterior e nova. A data de fechamento e a contagem da venda são preservadas. Consultar novamente o relatório do período original mostra a distribuição por origem corrigida e permite rastrear a alteração.

No fechamento e em qualquer correção posterior, a captação atribuída deve pertencer ao contato da oportunidade, no mesmo workspace, e ter ocorrido até o horário de fechamento. Uma tentativa de creditar um anúncio recebido depois da venda é rejeitada. Se não houver captação elegível, a oportunidade pode ser fechada com origem não atribuída.

### Permissões e visibilidade

**Visibilidade e responsabilidade.** O MVP oferece carteira individual com fila comum e visão compartilhada com edição por responsável. Na configuração inicial, o administrador escolhe o padrão da agência. Para cada operador, pode manter a opção de herdar esse padrão ou definir uma exceção individual ou compartilhada. Quando há exceção, ela prevalece sobre o padrão, mesmo após uma alteração no modo da agência. Remover a exceção volta a aplicar o padrão vigente. O escopo resultante vale para funil, inbox e indicadores. Nos dois modos, um operador pode assumir itens sem responsável. Registros atribuídos podem ser alterados pelo responsável ou pelo administrador. A transferência atualiza quem assume o registro. O administrador tem visão geral. Alterações de visibilidade registram o escopo anterior, o novo, o autor e o horário.

| Modo | O que o operador consulta |
| --- | --- |
| Carteira individual com fila comum | Registros sob sua responsabilidade e itens sem responsável. |
| Visão compartilhada com edição por responsável | Registros da equipe e itens sem responsável. Registros atribuídos a outro operador ficam somente para consulta até a transferência. |

| Registro | Consulta por operador | Alteração por operador |
| --- | --- | --- |
| Captação, oportunidade e tarefa | O modo efetivo é aplicado ao responsável do próprio registro. A fila comum contém itens sem responsável. | Apenas o responsável. Assumir um item da fila exige que ele continue sem responsável no momento da gravação. |
| Contato | No modo individual, dados do contato ficam disponíveis por vínculo com uma captação, oportunidade ou atendimento visível. Cada registro relacionado passa pela própria verificação. No modo compartilhado, a consulta continua dentro do workspace. | Quem pode editar ao menos um registro comercial ou atendimento vinculado pode atualizar os dados cadastrais. Outros registros e suas permissões permanecem separados. |
| Atendimento e mídia | A conversa privada mantém as restrições de responsável e participante autorizado, inclusive na visão compartilhada. O acesso à mídia depende de autorização sobre a conversa ou de propriedade temporária do upload. | O responsável pode atender e transferir; assumir exige item sem responsável. A transferência altera apenas a responsabilidade do atendimento. |
| Evento histórico de atendimento | Quem recebe o crédito pode conferir tipo, horário, número e duração, quando aplicável. Abrir a conversa exige autorização própria. | O crédito do evento fica no histórico após a transferência. |

A API aplica essas regras a listas, consulta direta, alterações, mídia, detalhamento e tempo real. Desativar o vínculo corta o acesso e as inscrições no workspace; os demais vínculos válidos do usuário permanecem. O administrador redistribui os itens abertos e os créditos históricos permanecem com seus autores.

**Permissões propostas para fechar o MVP.** O administrador gerencia usuários, exceções de visibilidade, configuração da agência, números de WhatsApp e etapas do funil. Também pode redistribuir registros e corrigir a atribuição à origem após o fechamento, com motivo. O operador trabalha nos registros que pode editar segundo sua responsabilidade, assume itens da fila sem responsável e pode transferir os atendimentos sob sua responsabilidade. Consulta compartilhada concede leitura. A escolha de vendedor no fechamento registra o crédito comercial e não transfere a responsabilidade pela oportunidade.

### Funil e indicadores comerciais

**Desativação de etapas.** O administrador pode bloquear novas entradas numa etapa ocupada e deixá-la visível até que os negócios saiam pelo fluxo normal. Para retirá-la do quadro antes disso, pode escolher uma etapa ativa de destino e mover as oportunidades restantes na mesma operação. A remoção do quadro é um arquivamento que preserva a referência da etapa no histórico. Movimentos feitos nessa operação são identificados como administrativos, separados dos avanços comerciais.

**Conversão e taxa de ganho.** O painel apresenta as duas métricas com nomes, recortes e listas de origem próprios. Os cálculos e seus detalhes respeitam o acesso do usuário.

| Métrica | Numerador | Denominador e período |
| --- | --- | --- |
| Conversão de captação | Leads do recorte que receberam crédito por pelo menos um negócio ganho. Cada lead convertido conta uma vez, mesmo com mais de uma oportunidade ganha. | Leads captados no período selecionado, pela data da captação. Uma venda posterior pode atualizar o resultado das captações daquele período. |
| Taxa de ganho de oportunidades | Oportunidades do recorte encerradas como ganhas. | Oportunidades encerradas como ganhas ou perdidas no período selecionado, pela data de fechamento. Inclui negócios abertos em períodos anteriores. |

Quando não há registros no denominador, o painel indica ausência de base para cálculo. O detalhamento permite conferir quais registros compõem a base e quais entram no numerador.

**Retomada de negócio perdido.** Retomar uma negociação encerrada como perdida cria uma nova oportunidade vinculada à anterior. O fechamento perdido e sua data são preservados no histórico e no indicador do período original. A nova oportunidade tem seu próprio fechamento. Se for ganha, conta como uma venda no novo período. A regra de atribuição da oportunidade nova segue o fluxo de abertura já definido.

### Inbox e indicadores de atendimento

O contato tem identidade comercial por workspace. A conversa tem identidade por workspace, conta do número oficial e identidade do interlocutor. Assim, o mesmo contato pode ter duas conversas independentes e enviar e receber no número correto. O atendimento é uma unidade de trabalho dentro da conversa. Seu início e seu encerramento têm eventos próprios. A regra sobre o que caracteriza um novo atendimento após o encerramento será confirmada com a agência antes de fechar o aceite de volume e tempo.

**Indicadores de atendimento.** O MVP apresenta volume, fila atual e tempo de primeira resposta, com recortes por número oficial e operador. O volume separa atendimentos iniciados e concluídos pelos horários dos eventos. A fila mostra atendimentos aguardando ação da equipe no momento da consulta. Uma primeira mensagem que requer ação entra na fila, uma primeira resposta humana aceita ou um encerramento sai da espera inicial, e uma nova mensagem que requer ação volta à fila do atendimento vigente. O tempo de primeira resposta mede da primeira mensagem daquele atendimento à primeira resposta humana aceita pelo WhatsApp.

Uma tentativa de envio com confirmação perdida fica inconclusiva até confirmação correlacionável. O CRM não conta essa tentativa como resposta nem repete o envio automaticamente. Quando confirmada, usa o horário comprovado da aceitação. Despacho e retry aplicam a conta validada de cada evento. A deduplicação antecede qualquer abertura, reabertura ou captação.

**Atribuição por evento.** O início pertence ao responsável no momento da abertura, ou ao grupo Sem responsável. A primeira resposta pertence a quem enviou a primeira resposta aceita. O encerramento pertence a quem encerrou o atendimento. A fila pertence ao responsável atual, ou ao grupo Sem responsável. Uma transferência altera o responsável atual e preserva as atribuições históricas. O tempo até a primeira resposta inclui a espera desde a primeira mensagem do atendimento, inclusive o tempo em fila.

### Crédito da venda e recortes do painel

**Crédito da venda.** Ao marcar uma oportunidade como ganha, o usuário precisa selecionar explicitamente um vendedor com vínculo ativo naquele workspace. O fechamento exige essa seleção, que fica registrada na oportunidade. Créditos existentes permanecem mesmo após desativação. A atribuição ao vendedor é distinta da origem da captação e dos créditos do atendimento. A venda continua contando uma vez.

**Recortes do painel.** A configuração inicial registra o fuso IANA do workspace. O início do período é inclusivo e o fim é exclusivo, calculados no fuso do workspace e convertidos para UTC na consulta. Totais de captação usam a data de entrada do lead, fechamentos usam a data de encerramento da oportunidade e atendimentos iniciados ou concluídos usam a data do evento correspondente. Estoque do funil e fila são rotulados como dados atuais. Ao abrir a composição, a API devolve o total e a primeira página sob a mesma leitura. A tela atualiza o total se o recorte tiver mudado desde a consulta do painel.

| Indicador | Registros que compõem o valor |
| --- | --- |
| Total de leads | Uma linha por captação no período. Cada entrada distinta por anúncio conta, e a reentrega do mesmo evento é deduplicada. |
| Oportunidades por etapa | Oportunidades abertas na etapa atual. Contagem e acesso aos cartões usam os mesmos filtros. Uma mudança administrativa altera a etapa atual e preserva o histórico comercial. |
| Negócios concluídos e vendas | Oportunidades encerradas no período, separadas em ganhas e perdidas. Vendas usam apenas as ganhas. O filtro por vendedor usa o crédito registrado no fechamento. |
| Valor vendido | Soma do valor registrado nas oportunidades ganhas no período. O painel usa o nome Valor vendido e apresenta os negócios que somam o total. |
| Conversão de captação e taxa de ganho | As duas regras já definidas neste plano, com períodos e bases próprios. |
| Volume e fila de atendimento | Inícios e encerramentos no período, separados da fila atual. Número e operador seguem a atribuição por evento. |
| Tempo até a primeira resposta | Proposta de mediana do tempo até a primeira resposta humana aceita para os atendimentos iniciados no período e respondidos até a consulta. O painel informa o tamanho da amostra. Atendimentos ainda sem resposta aparecem na fila quando aguardam ação da equipe. |

O teste de cada indicador verifica os limites do período, os filtros, os valores esperados e a composição. Se um registro de origem estiver fora do acesso do usuário, ele também fica fora do agregado. Para a conversão de captação, só contam ganhos visíveis no mesmo escopo. A autorização é testada tanto no total quanto no detalhe.

**Uso futuro em canais mistos.** Em uma eventual oferta a clientes, um número pode receber mensagens operacionais e comerciais. Nesse cenário, a criação automática deve depender de um sinal comercial, como origem de anúncio identificada. O uso atual da agência serve de premissa para o MVP interno. A política de canais mistos fica para um desenho posterior.

### Integração dos fluxos

```text
Operador / Administrador → aplicação web → API com verificação de papel e workspace
                                              ├─ CRM e tarefas → contatos, negócios e histórico
WhatsApp oficial ↔ conta do número ↔ inbox ────┤
                                              └─ Indicadores → total e registros do mesmo recorte
```

| Área | Base identificada por leitura estática da revisão f6a9a22 | Mudança proposta |
| --- | --- | --- |
| Autorização e isolamento | Login, vínculo por workspace e verificação de papéis. | Cobrir administração de operadores e aplicar o workspace, a visibilidade e as regras de responsabilidade na API, na inbox, nos processos em segundo plano e nos indicadores. Verificar com dois workspaces de teste. |
| Contatos e comercial | Contatos, telefones, e-mails e vínculo de conversa com contato. | Reaproveitar a identidade de contato e acrescentar leads de captação, oportunidades, etapas configuráveis, histórico de movimentação e tarefas. A API distingue cadastro de contato, registro de captação e movimentação de oportunidade. |
| Inbox oficial | Contas de canal, transferência, filtro por conta e adaptador Meta. | Conferir o envio real na base integrada, identificar a conta de cada evento recebido e manter conversa e envio vinculados ao número correto. Usar a origem de anúncio identificada como gatilho de captação. Testar reentrega, falha de envio, filtro e transferência antes do aceite com dois números. |
| Indicadores | Eventos e horários de conversa que podem alimentar métricas de atendimento. | Cada indicador tem uma regra para selecionar registros por workspace, acesso e período. A agregação e o detalhamento usam essa mesma seleção. Os testes conferem tanto os valores quanto os registros incluídos e excluídos. |
| Produção | Imagens de aplicação, migrações e processos de execução em segundo plano. | Preparar a configuração do ambiente, a migração de publicação, o backup, a restauração e a observação de falhas que afetem mensagens ou lembretes. |

O plano técnico consolidado foi aprovado nesta conversa. A preparação para empresas futuras foi acrescentada após o brief e preserva a primeira entrega para a agência. As dependências de validação estão em Open Questions.

## Alternatives Considered

### Priorizar entregas de marketing e e-commerce

- **Benefício.** Reaproveitaria a organização do backlog descrita no handoff.
- **Limite.** Colocaria em segundo plano o funil, o atendimento comercial e a conferência dos números de vendas.
- **Decisão.** O autor escolheu o MVP comercial da proposta. O backlog vigente será conferido no ClickUp antes do realinhamento.

### Reconstruir o CRM do zero

- **Benefício.** Daria liberdade para desenhar os fluxos sem carregar módulos da direção anterior.
- **Limite.** Reexigiria autenticação, usuários, contatos, inbox e integração de canal, com mais trabalho de implementação e validação.
- **Decisão.** O plano aprovado evolui a base atual. A revisão integrada publicada foi conferida estaticamente. O reaproveitamento de cada módulo continua condicionado aos testes dos seus fluxos.

### Calcular o painel e o detalhamento de forma independente

- **Benefício.** Cada tela poderia ter uma consulta própria para o seu formato.
- **Limite.** Fórmulas, filtros e permissões poderiam divergir. No CRM anterior, telas que concordavam na contagem de vendas exibiam valores com definições diferentes.
- **Decisão.** Total e detalhe usam a mesma seleção de registros e a mesma regra de cálculo. Testes com dados conhecidos validam a composição.

### Confirmar a elegibilidade e os acessos ao WhatsApp só no bloco de integração

- **Benefício.** Concentraria a atividade no bloco planejado para a inbox.
- **Limite.** Uma dependência externa poderia aparecer no meio dos 20 dias úteis e impedir o aceite com dois números.
- **Decisão.** A fundação verifica números e acessos. O desenvolvimento e o aceite de envio, recebimento, filtro e transferência continuam no bloco de WhatsApp.

### Tratar lead como uma fase do cadastro de contato

- **Benefício.** Haveria menos registros para localizar e deduplicar.
- **Limite.** Um cadastro por pessoa ou empresa perderia a data e a origem de captações distintas. Contar contatos novos responderia a uma pergunta diferente de contar entradas por anúncio.
- **Decisão.** O autor escolheu lead como registro de captação. Cada entrada distinta por anúncio mantém sua origem e seu horário, e todas podem se vincular ao mesmo contato.

### Usar a visibilidade da agência como limite máximo para cada operador

- **Benefício.** A regra geral sempre limitaria o acesso individual.
- **Limite.** Uma agência com carteira individual teria de ampliar o padrão de toda a equipe para permitir cobertura compartilhada a um operador específico.
- **Decisão.** O autor escolheu um padrão por workspace com exceções por operador. A exceção pode ampliar ou reduzir a visibilidade dentro da própria empresa, e fica registrada no histórico.

### Reabrir a mesma oportunidade depois de uma perda

- **Benefício.** A equipe teria um único registro para acompanhar as duas tentativas.
- **Limite.** Se o indicador usasse apenas o fechamento vigente, reabrir ou ganhar depois poderia retirar a perda do mês original. Preservar fechamentos como eventos também é viável, mas exige distinguir tentativas, resultado atual e contagem histórica no mesmo registro de negócio.
- **Decisão.** O autor escolheu uma nova oportunidade vinculada à perdida. Cada tentativa tem seu fechamento. O histórico conserva a perda original e somente a oportunidade ganha conta como venda.

## Detailed Implementation Plan

### Base e ordem de trabalho

Planejar sobre a revisão publicada `f6a9a22` de `codex/delivery-first-integration`, consultada pelo Git sem trocar o checkout. Ela contém a integração publicada em `29de6ce`, o ambiente de desenvolvimento em `03036b1` e o envio da inbox pelo adaptador de WhatsApp. O commit local `1bcc187` do handoff não apareceu como objeto publicado nessa consulta. Para este plano, vale a revisão publicada e inspecionada. A branch de trabalho local permanece em `33a02ea` com o Stage 5 preservado.

A publicação de desenvolvimento registra testes em PostgreSQL real para bancos vazios e para as linhagens local e QA, além de smoke do ambiente compartilhado. Esses resultados são evidência da base. As novas migrações, a autorização do MVP, a restauração e o WhatsApp com números reais terão sua própria verificação.

| Bloco | Dias úteis | Datas provisórias | Depende de | Resultado que fecha o bloco |
| --- | --- | --- | --- | --- |
| M1 Fundação | 1–3 | 16–18/11 | Base publicada, decisões de acesso e responsáveis pelos acessos | Administrador gerencia operadores e o isolamento passa com dois workspaces. Verificar acessos, números e modelos e obter evidência sanitizada do sinal de anúncio antes de fechar o contrato M2/M3. |
| M2 Comercial | 4–8 | 19–25/11 | M1 | Cadastrar, vincular e movimentar negócios, fechar ganho com vendedor explícito, retomar perda e concluir tarefa com lembrete. |
| M3 WhatsApp | 9–13 | 26/11–02/12 | M1 e cadastro de captação de M2 | Enviar, receber, filtrar e transferir com dois números oficiais. Captação identificada por anúncio e atribuição por evento verificadas. |
| M4 Indicadores | 14–16 | 03–08/12 | Registros e testes de M2 e M3 | Totais e detalhes reconciliam para os mesmos filtros, períodos e permissões. |
| M5 Homologação e publicação | 17–20 | 09–14/12 | M1–M4 e ambiente aprovado | Fluxos principais em produção, backup automatizado com restauração exercitada, monitoramento e aceite manual. |

Datas em 2026, condicionadas à aprovação e à disponibilidade dos acessos. Testes dos dados de origem começam nos blocos M2 e M3, antes de montar o painel. Cada entrega registra a evidência técnica, o roteiro manual e o que ainda falta validar.

### Target Files to Create/Modify

Os caminhos são relativos ao repositório na revisão indicada. As tabelas separam arquivos existentes a modificar de arquivos novos propostos. Antes da execução, conferir se surgiram mudanças na branch base e encadear cada migração ao head vigente. Revisões históricas permanecem como evidência da origem dos dados. A área local de Flow Builder fica fora das alterações deste plano.

#### M1. Fundação, acesso e isolamento

| Arquivo | Ação | Mudança e motivo |
| --- | --- | --- |
| `backend/app/models/workspace.py` | Modificar | Registrar o padrão de visibilidade por workspace, a exceção por vínculo de usuário e o estado do operador naquele workspace. Desativar em uma empresa preserva vínculos válidos em outras. |
| `backend/app/schemas/workspace.py` | Modificar | Expor os modos individual, compartilhado e herdar onde couber, bem como o estado do vínculo, com validação da configuração inicial. |
| `backend/app/api/v1/workspaces.py` | Modificar | Completar gestão de operadores, escolha inicial e edição de padrão e exceções. Auditar autor, data e valores anterior e novo. |
| `backend/app/core/dependencies.py` | Modificar | Concentrar o vínculo ativo, o papel e o escopo efetivo. Aplicar a mesma regra a listas, consultas diretas, alterações e ações de administração. |
| `backend/app/api/v1/auth.py`, `backend/app/services/auth_service.py` | Modificar | Ligar login e provisionamento à gestão administrativa, validar vínculo ativo nas operações e impedir que cadastro público conceda acesso ao workspace. Preservar o bootstrap de administrador. |
| `backend/app/websocket/handlers.py`, `backend/app/websocket/manager.py` | Modificar | Conferir vínculo na conexão e aplicar a visibilidade efetiva na distribuição de eventos. Atualizações de permissão invalidam acesso ou inscrição já aberta. |
| `backend/app/api/v1/media.py` | Modificar | Verificar workspace e acesso ao objeto nas operações de envio e obtenção de mídia. |
| `backend/migrations/versions/202611160001_workspace_access.py` | Criar | Acrescentar configurações e dados de vínculo de forma incremental. Exercitar base vazia e bases já migradas. |
| `frontend/src/types/workspace.ts`, `frontend/src/lib/api.ts` | Modificar | Tipar os contratos de vínculo, configuração e equipe, e conectar as ações administrativas. |
| `frontend/src/components/settings/team-tab.tsx`, `frontend/src/app/(dashboard)/settings/page.tsx` | Modificar | Configuração inicial, convite ou criação de operador conforme o fluxo de acesso da base, desativação e edição de exceções. |
| `backend/tests/test_workspace_access.py` | Criar | Cobrir dois workspaces, consulta por ID, escrita, mídia e eventos da inbox. Testar padrão, exceções nos dois sentidos, remoção de exceção e revogação após desativar operador. |
| `backend/tests/test_migration_upgrade.py` | Modificar | Estender a verificação de head e preservação de dados nas três origens de banco já exercitadas pela base. |

#### M2. Contato, captação, oportunidade e tarefas

| Arquivo | Ação | Mudança e motivo |
| --- | --- | --- |
| `backend/app/models/contact.py`, `backend/app/schemas/contact.py`, `backend/app/api/v1/contacts.py` | Modificar | Reusar cadastro e pesquisa de contatos. Conferir telefones e vínculos no workspace e preservar histórico ao retirar um contato de uso. |
| `backend/app/models/commercial.py` | Criar | Modelar captação, etapa, oportunidade, movimentação, atividade e tarefa. Cada objeto tem workspace. A oportunidade registra contato, responsável, captação atribuída, valor, estágio, resultado e, no ganho, vendedor e horário de fechamento. |
| `backend/app/models/__init__.py`, `backend/app/main.py` | Modificar | Registrar modelos e rotas novas uma vez. Coordenar este ponto compartilhado entre blocos. |
| `backend/app/schemas/commercial.py`, `backend/app/api/v1/commercial.py` | Criar | Expor leads, etapas, oportunidades e tarefas sob o workspace. Listagem paginada por etapa usa o mesmo filtro da contagem. Expor ações distintas de assumir, mover, concluir, retomar, arquivar etapa e corrigir atribuição. |
| `backend/app/services/commercial_service.py` | Criar | Concentrar as regras de captação e oportunidade. Ao abrir, usar a captação mais recente anterior do mesmo contato, com troca auditada. No ganho, exigir vendedor explícito. Depois de fechar, aceitar correção de origem apenas pelo administrador com motivo. Ao retomar uma perda, vincular nova oportunidade à anterior. Validar vínculos, estados e papéis no servidor. Ao arquivar uma etapa com oportunidades, movê-las para outra etapa e arquivar numa operação indivisível, registrando o movimento como administrativo. |
| `backend/migrations/versions/202611190001_commercial_mvp.py` | Criar | Criar tabelas, vínculos e índices dos registros comerciais e das tarefas. Proteger integridade de vínculos entre registros da mesma empresa. |
| `backend/app/workers/tasks/commercial.py`, `backend/app/workers/celery_app.py` | Criar, modificar | Agendar a verificação de tarefas com lembrete devido e registrar o lembrete no CRM para o responsável. Processamento repetido não pode criar outro lembrete para a mesma ocorrência. |
| `frontend/src/types/commercial.ts`, `frontend/src/lib/api.ts` | Criar, modificar | Tipar e conectar cadastro, quadro, movimentações, atribuição, fechamento e tarefas. |
| `frontend/src/app/(dashboard)/opportunities/page.tsx`, `frontend/src/app/(dashboard)/tasks/page.tsx` | Criar | Apresentar Kanban paginado com filtros, criação e ações de negócio. Mostrar tarefa, prazo, lembrete e conclusão. |
| `frontend/src/app/(dashboard)/contacts/page.tsx`, `frontend/src/app/(dashboard)/contacts/[id]/page.tsx` | Modificar | Usar o cadastro existente como identidade e expor captações e oportunidades vinculadas conforme as permissões. |
| `frontend/src/components/settings/pipeline-tab.tsx`, `frontend/src/app/(dashboard)/settings/page.tsx`, `frontend/src/components/layout/sidebar.tsx` | Criar, modificar, modificar | Editar etapas no painel administrativo e incluir navegação para oportunidades e tarefas. |
| `backend/tests/test_commercial.py` | Criar | Testar fila, visibilidade, mais de 500 registros em uma etapa, arquivamento de etapa com remanejamento, auditoria de origem, vendedor obrigatório, retomada da perda e execução repetida de lembrete. |

#### M3. WhatsApp oficial e captação identificada

| Arquivo | Ação | Mudança e motivo |
| --- | --- | --- |
| `backend/app/channels/base.py`, `backend/app/channels/whatsapp/meta_cloud.py` | Modificar | Carregar no evento normalizado o número, a identidade externa e o sinal de anúncio quando presente no payload validado. Completar envio de modelo aprovado e traduzir aceitação e falha para estados observáveis. |
| `backend/app/webhooks/whatsapp/meta.py`, `backend/app/services/webhook_service.py`, `backend/app/services/webhook_retry.py` | Modificar | Resolver conta e workspace por evento no despacho e no reprocessamento. A base atual ainda lê o número do primeiro item. Manter validação de origem e assinatura, deduplicação e evidência de falhas recuperáveis, incluindo lote de teste com números distintos. |
| `backend/app/services/message_service.py`, `backend/app/models/conversation.py`, `backend/app/schemas/message.py` | Modificar | Reusar o envio existente. Correlacionar mensagem com resultado do adaptador e registrar primeira resposta humana aceita. Registrar eventos de início e encerramento com o operador que deve receber o crédito. Associar captação à entrada identificada e preservar histórico de mensagens sem atribuição confirmada. |
| `backend/app/services/commercial_service.py` | Modificar | Reusar a criação de captação do bloco M2 no gatilho de anúncio. Distinguir entrada nova de reentrega pela identidade confirmada do evento. Uma conversa existente pode gerar outra captação sem duplicar o contato. |
| `backend/app/api/v1/channel_accounts.py`, `backend/app/api/v1/conversations.py`, `backend/app/api/v1/messages.py` | Modificar | Restringir configuração dos canais a administrador. Aplicar filtro, transferência e envio somente nas contas e registros autorizados. Validar janela e modelo para a mensagem solicitada. |
| `backend/migrations/versions/202611260001_whatsapp_event_attribution.py` | Criar | Acrescentar persistência das identidades e eventos que o aceite exige, reutilizando a estrutura existente onde já comporta o contrato. |
| `frontend/src/lib/api.ts`, `frontend/src/types/conversation.ts`, `frontend/src/types/channel.ts` | Modificar | Tipar filtro por número, estado de envio e seleção de modelo permitido. |
| `frontend/src/app/(dashboard)/inbox/page.tsx`, `frontend/src/components/inbox/conversation-list.tsx`, `frontend/src/components/inbox/conversation-header.tsx`, `frontend/src/components/inbox/reply-box.tsx` | Modificar | Propagar filtro por número, identificar a conta do atendimento, distinguir envio aceito de falha e permitir envio de modelo aprovado quando exigido. Mostrar claramente o efeito de transferir. |
| `backend/tests/test_whatsapp_official_mvp.py` | Criar | Simular duas contas, mesmo contato, reentrega, entrada distinta por anúncio, lote com números distintos, falha e aceitação. Verificar que envio usa o número da conversa e que a transferência mantém atribuições históricas. |
| `backend/tests/test_worker_transport.py` | Modificar | Confirmar que reprocessamento e eventos de tarefas chegam apenas a sessões autorizadas e que alterações vindas do worker ficam visíveis na inbox. |

Usar a evidência sanitizada de M1 para fechar o mapeamento do sinal de anúncio, sem guardar credenciais ou conteúdo privado no repositório. No M3, a agência homologa envio e recebimento nos dois números, filtro, transferência, janela e modelos. A seleção dos números precisa permitir esse teste sem depender de importação retroativa.

#### M4. Indicadores verificáveis

| Arquivo | Ação | Mudança e motivo |
| --- | --- | --- |
| `backend/app/services/metrics_service.py` | Criar | Definir seleção, fonte, período, fuso, filtros e cálculo por indicador. Reusar a mesma seleção no total e no detalhe paginado. Aplicar workspace e acesso antes do cálculo, inclusive em vínculos usados pela conversão. |
| `backend/app/schemas/metrics.py`, `backend/app/api/v1/metrics.py`, `backend/app/main.py` | Criar, criar, modificar | Expor totais e composição sob o mesmo contrato de filtro. Distinguir período, fila atual e estoque atual. Expor a amostra da mediana e indicar quando uma taxa não tem denominador. |
| `frontend/src/types/metrics.ts`, `frontend/src/lib/api.ts`, `frontend/src/app/(dashboard)/reports/page.tsx` | Criar, modificar, modificar | Exibir as métricas definidas no plano, com nome, recorte, filtros e acesso à composição. Valor vendido, conversão de captação e taxa de ganho têm rótulos e bases próprios. |
| `backend/tests/test_metrics.py` | Criar | Conferir captação em outubro e fechamento em novembro, perda retomada como outro negócio, múltiplas vendas de um lead, correção de origem, vendedor diferente do operador, transferência, recorte por número, falha no envio, período sem dados e isolamento. Reconciliar total, numerador, denominador e detalhe. |

#### M5. Produção e homologação

| Arquivo | Ação | Mudança e motivo |
| --- | --- | --- |
| `deploy/compose.production.yml`, `deploy/production.env.example` | Criar | Descrever a produção com configurações sem segredos, migração antes de abrir tráfego, persistência, serviços de aplicação e verificações de saúde. Usar o Compose de desenvolvimento como referência de implantação. |
| `deploy/README.md` | Modificar | Documentar implantação, responsáveis, agendamento de backup, restauração de banco e mídia, critérios de reversão, monitoramento de disponibilidade, fila e falha de backup. |
| `deploy/smoke_development.py` | Modificar | Estender smoke para os contratos do MVP em ambiente de teste com dados descartáveis, sem dependência de credenciais de WhatsApp real. |
| `docs/reports/ACEITE_MVP_COMERCIAL.md` | Criar | Registrar roteiro manual, revisão testada, evidências, pendências e aceite da agência. Incluir fluxo comercial, conferência de indicadores, dois números e restauração. |

### Contratos para execução

A nomenclatura da API usa **lead** para o registro de captação e **opportunity** para o negócio do funil. As regras abaixo completam os arquivos e as ações da lista por bloco. O escopo de escrita inclui as extensões explicitadas aqui.

#### Persistência e upgrade · M1–M3

O head da base f6a9a22 é `202611110001`, que integra as linhagens `202605221215` e `202605250001`. A sequência proposta é `202611160001` → `202611190001` → `202611260001`. Se a base ganhar outra revisão, atualizar a sequência no plano antes de escrever a migração. O upgrade usa revisões incrementais. Asserções verificam dados e vínculos antes e depois, incluindo mensagem e payload do webhook, sem apagar ou remarcar o banco para fazer o teste passar.

IDs novos seguem UUID e a convenção de timestamps da base. Instantes são armazenados com fuso em UTC. Colunas marcadas como opcionais aceitam nulo; as demais são obrigatórias. Chaves de referência de negócio validam o par workspace e ID, inclusive nos vínculos criados pelo worker. Uma origem ou um vendedor desativado continua referenciável nos registros históricos.

| Registro e revisão | Campos e invariantes |
| --- | --- |
| Workspace e vínculo · M1 | Workspace guarda `visibility_default` opcional até a configuração inicial e `timezone` IANA opcional até essa configuração. O vínculo guarda `visibility_override` opcional e `is_active` booleano, padrão verdadeiro. `herdar` na API grava nulo. Para workspaces existentes, preservar papéis e membros, exigir configuração antes de abrir o acesso do operador aos fluxos novos e usar a visão individual enquanto a configuração estiver incompleta. |
| Objeto temporário de mídia · M1 | Registro com workspace, chave única do objeto, autor, horário de upload e vínculo de mensagem opcional. O upload sem mensagem pertence ao autor. Vincular exige autorização sobre a conversa, propriedade do temporário e correspondência do workspace. A emissão de URL verifica o vínculo novamente. URL emitida tem prazo curto, configurado em até cinco minutos para a interface; revogação impede nova emissão. |
| Lead · M2 | Contato, instante de captação, origem, responsável opcional e referência externa opcional. Para captação automática, origem e identidade do evento são obrigatórias. A origem registrada fica preservada quando chega outro evento do mesmo contato. |
| Etapa · M2 | Workspace, nome, posição e estado `active`, `draining` ou `archived`. Etapa em esvaziamento aceita saída; entradas novas exigem etapa ativa. Arquivamento de etapa com oportunidades abertas exige destino ativo do mesmo workspace, aplicado numa transação. |
| Oportunidade · M2 | Contato, etapa, abertura, valor decimal de duas casas, responsável opcional, lead atribuído opcional e estado `open`, `won` ou `lost`. Valor inicial zero. Fechamento exige data; ganho também exige vendedor com vínculo ativo. Retomada de perda cria outra oportunidade com referência opcional à anterior. Origem atribuída pertence ao mesmo contato e, no fechamento, tem data igual ou anterior ao fechamento. |
| Evento comercial · M2 | Oportunidade, tipo, instante e autor. Mudanças de etapa guardam origem/destino e distinção comercial/administrativa. Correção após ganho guarda atribuições anterior/nova e motivo obrigatório. Alterar a atribuição não altera venda, valor nem fechamento. |
| Atividade, tarefa e lembrete · M2 | Atividade registra autor, contato, oportunidade opcional, nota e instante. Tarefa registra responsável, prazo, estado aberto/concluído e horário opcional do lembrete. Concluir grava data. A entrega do lembrete é identificada pelo par tarefa e instante devido, com unicidade e publicação no CRM somente após a gravação. Reagendar cria outra ocorrência; cancelar ou concluir impede entregas futuras. |
| Atendimento e identidade de mensagem · M3 | Reutilizar contas de canal e eventos de conversa. A identidade da conversa inclui workspace, conta e interlocutor. A identidade técnica de uma mensagem considera provedor, conta validada e ID externo. Eventos de início, resposta aceita e conclusão preservam instante, conta e ator ou responsável correspondente. Mensagens existentes e payloads brutos permanecem legíveis. |
| Registro de entrada por anúncio · M3 | Vincular a captação ao evento validado e garantir unicidade no workspace e conta pelo identificador de entrada confirmado em M1. A verificação de duplicidade ocorre antes da alteração comercial e sob a mesma transação da captação. O mapeamento de campos do provedor e o tratamento de entradas sem sinal conclusivo são fechados com a evidência de M1. Até lá, casos inconclusivos podem aparecer na inbox, mas ficam sem criação automática por anúncio. |

#### Contratos de acesso e API · M1–M4

As novas rotas ficam em `/api/v1/workspaces/{workspace_id}`, com vínculo ativo e papel validados no servidor. Uma consulta direta retorna 404 para registro inexistente ou fora da visibilidade. Operação administrativa para papel sem permissão retorna 403. Alteração incompatível com estado concorrente, como assumir item que já ganhou responsável, retorna 409. Campos e vínculos inválidos retornam 422. Listas novas usam `page` a partir de 1 e `page_size` padrão 50, máximo 100, com ordenação estável por instante e ID. A consulta do quadro por etapa retorna itens e total sob os mesmos filtros.

| Bloco | Rotas e comportamento |
| --- | --- |
| M1 · Configuração e equipe | `PATCH /settings` recebe padrão e fuso; só administrador. `GET /members` lista vínculos conforme a regra de equipe. `POST /members` provisiona um operador pela administração, usando o mecanismo de credenciais do projeto; `PATCH /members/{user_id}` altera estado e exceção. Provisionar um usuário existente liga sua conta ao workspace sem reescrever credencial. Somente o bootstrap autorizado cria workspace no MVP. Remover exceção grava `herdar`. |
| M2 · Cadastro | `GET/POST /leads`, `GET/PATCH /leads/{id}` e rotas existentes de contato. Criar lead recebe contato e origem e registra o instante no servidor. Alterações seguem responsabilidade. `GET/POST /pipeline/stages` e `PATCH /pipeline/stages/{id}` gerenciam etapas; escrita pelo administrador. `POST /pipeline/stages/{id}/archive` recebe destino quando houver oportunidades abertas. |
| M2 · Negócios e tarefas | `GET/POST /opportunities` e `GET/PATCH /opportunities/{id}` consultam e editam oportunidades. Ações `POST /opportunities/{id}/claim`, `/move`, `/close`, `/resume` e `/attribution` tratam, respectivamente, assunção, mudança de etapa, resultado, retomada de perda e atribuição. Fechamento recebe resultado e vendedor se ganho. Correção após fechamento recebe lead e motivo e é administrativa. `GET/POST /tasks`, `PATCH /tasks/{id}` e `POST /tasks/{id}/complete` cobrem tarefa e conclusão. `GET/POST /contacts/{id}/activities` lista e registra notas autorizadas. |
| M3 · Inbox | Usar as rotas existentes de contas, conversas e mensagens. `channel_account_id` identifica o número no filtro; o envio usa a conta da conversa autorizada. A transferência recebe o destinatário no mesmo workspace e preserva número e créditos anteriores. Modelos aprovados e janela são validados no servidor. Uma tentativa inconclusiva fica pendente de confirmação e aparece com estado distinto na resposta. |
| M4 · Indicadores | `GET /metrics` retorna totais e recortes. `GET /metrics/{metric}/records` devolve base, total, itens paginados e quais compõem o numerador quando aplicável. Parâmetros de período usam início inclusivo e fim exclusivo no fuso do workspace. Filtros têm nomes por papel no cálculo: responsável, vendedor ou operador do evento, além de origem, etapa ou número conforme a métrica. A primeira página e seu total usam a mesma leitura. |

Arquivos adicionais ao limite por bloco:

- **M1.** Modificar `backend/app/api/v1/conversations.py`, `backend/app/api/v1/messages.py`, `backend/app/api/v1/contacts.py`, `backend/app/services/conversation_service.py` e `backend/app/services/timeline_service.py` para aplicar a mesma decisão a listas, detalhe, mensagens, ações e histórico relacionado. Modificar `backend/app/schemas/message.py` e `frontend/src/components/inbox/reply-box.tsx` para aplicar a regra de mídia no upload, no vínculo e na exibição. Criar `backend/app/models/media_upload.py` e registrar em `backend/app/models/__init__.py` para persistir propriedade e vínculo do upload. Atualizar `deploy/bootstrap_development.py` para exercitar o bootstrap designado, sem dados reais.
- **M1 e M3.** Usar Redis existente para levar avisos do worker à API. O aviso contém workspace, tipo e identificador, com reconsulta autorizada antes da exibição. Publicar após confirmação da gravação. Modificar `backend/app/core/redis.py`, `backend/app/main.py` e `backend/app/websocket/manager.py` para publicação, assinatura e ciclo de vida. Antes de distribuir, verificar vínculo e visibilidade atuais; remover inscrição revogada e validar novamente no próximo pedido. Testar um worker e uma API em processos distintos. A notificação em tempo real não substitui a consulta persistida.
- **M2.** Reaproveitar o registro/API de notificação interna em `backend/app/models/stage9_extras.py` e `backend/app/api/v1/stage9_extras.py`. Alterar o modelo se necessário para armazenar a referência única da ocorrência. O agendador verifica vencimentos a cada minuto. Gravar apenas entrega interna na mesma transação da ocorrência. O lembrete pode ser conferido na consulta de notificações do responsável mesmo se o aviso em tempo real falhar.
- **M3.** Modificar `backend/app/services/webhook_event_service.py`, `backend/app/models/webhook.py`, `backend/app/services/conversation_service.py` e `backend/app/services/timeline_service.py` para o contrato de autenticação, despacho por item, persistência e reaproveitamento dos eventos de atendimento. Validar assinatura do corpo com a configuração aplicável antes de encaminhar qualquer item. Contas desconhecidas, ambíguas ou desativadas ficam sem gravação de atendimento ou lead. Preservar corpos históricos e testar seu retry com a conta validada de cada item. O mesmo contrato vale para despacho e reprocessamento.
- **M5.** Incluir `README.md` na atualização de entrada do projeto, para identificar o MVP comercial e o destino do planejamento anterior. Criar os caminhos de execução e armazenamento de backup apenas após definir o executor no ambiente. Se for externo ao repositório, registrar a configuração e o responsável no runbook.

#### Checkpoints executáveis e dependências externas

| Bloco | Verificação e resultado esperado |
| --- | --- |
| M1 | Em `backend/`, executar `python -m unittest discover -s tests -p test_workspace_access.py -v` e `python -m unittest discover -s tests -p test_migration_upgrade.py -v`. Para upgrades, `CRM2_MIGRATION_TEST_URL` aponta para PostgreSQL descartável com permissão de criar bancos de teste; registrar que os testes realmente rodaram. Testar revogação em sessão aberta, mídia, consulta direta e mesmo telefone em dois workspaces. |
| M2 | Em `backend/`, executar `python -m unittest discover -s tests -p test_commercial.py -v`. Conferir paginação de etapa com mais de 500 oportunidades, fechamento sem vendedor rejeitado, perda preservada após retomada e uma entrega interna após executar o lembrete duas vezes. Exercitar o quadro e as tarefas pela interface. |
| M3 | Em `backend/`, executar `python -m unittest discover -s tests -p test_whatsapp_official_mvp.py -v` e `python -m unittest discover -s tests -p test_worker_transport.py -v`. Verificar lote com duas contas, reentrega concorrente antes de efeitos, independência das duas conversas, perda de confirmação, evento tardio e reprocessamento de histórico. Repetir roteiro manual com dois números oficiais autorizados. |
| M4 | Em `backend/`, executar `python -m unittest discover -s tests -p test_metrics.py -v`. Caso de referência: dois leads de outubro, um com crédito de ganho em novembro, conversão de outubro de 1/2. Em novembro, um ganho e uma perda elegíveis dão taxa de ganho de 1/2. Comparar total e detalhe com e sem permissão para um dos registros e com eventos nas fronteiras do fuso. |
| M5 | Rodar a suíte completa no banco descartável, smoke parametrizado no ambiente designado e o roteiro em computador e celular. Restaurar uma cópia de banco e mídia em ambiente separado, conferir leitura e registrar revisão, duração, resultado e responsável. Um teste real do alerta de falha e um exercício de reversão documentado fecham o bloco. |

Em cada bloco que muda a aplicação web, executar em `frontend/` `npm run type-check`, `npm run lint` e `npm run build`. Os nomes de testes novos acima são alvos previstos de implementação. Registrar comandos e asserções executadas, além das evidências manuais, no aceite.

**Passagem de M1 para o contrato de captação.** A agência indica os dois números elegíveis e libera acesso autorizado. Obter uma amostra sanitizada ou uma prova acompanhada que diferencie entrada por anúncio, a mesma entrada reentregue, continuidade e outra entrada distinta do mesmo contato. Registrar versão, campos de identidade, vínculo com o número, modelos necessários e estado de cada evidência. Se o sinal estiver ausente ou inconclusivo, registrar o impacto no aceite e manter o contrato automático pendente de decisão. M2 pode implementar captação manual e seus testes usando dados sintéticos.

**Corte operacional e M5.** Antes da ativação, registrar o destino de negócios e atendimentos que já estão em andamento. Indicadores oficiais começam no marco de ativação aprovado, com o recorte visível. Uma carga inicial selecionada entra somente com reconciliação explícita. O responsável da implantação confirma quais rotinas legadas ficam habilitadas. Envios externos, CSAT e autoencerramento legado só são habilitados se fizerem parte do aceite e tiverem autorização específica. O runbook registra executor, frequência, destino separado do ambiente principal, responsáveis por alerta e gatilhos de reversão. Backup automatizado e restauração precisam de evidência própria, além do smoke. Executor, destino e responsáveis continuam dependentes do ambiente de produção autorizado.

### Verification Plan

- **Backend e banco.** Rodar a suíte de `unittest` já usada no projeto e os novos testes em PostgreSQL descartável. Validar instalação vazia, upgrades das linhagens cobertas pela base e preservação de dados. Conferir os contratos de API e executar smoke dos fluxos do MVP.
- **Frontend.** Executar verificação de tipos, lint e build. Homologar Kanban, contatos, tarefas, inbox, permissões e painel em computador e celular.
- **Indicadores.** Usar registros sintéticos desde cada entrega. O teste do painel compara a consulta ao resultado esperado e verifica que o detalhe usa os mesmos registros autorizados.
- **Operação.** Exercitar restauração em ambiente de teste e verificar leitura de registros e mídia restaurados. Testar alerta de indisponibilidade e falhas no processamento. Homologar dois números oficiais de forma acompanhada, com os acessos autorizados pela agência.
- **Critério de fechamento.** Publicar evidência técnica e resultado de aceite manual separadamente. Um teste automatizado de adaptador ou smoke do ambiente compartilhado não comprova o teste com dois números.

### Realinhamento no ClickUp

A revisão do código publicado precedeu o realinhamento do ClickUp. O [relatório da revisão e realinhamento](../reports/crm2_code_review_e_realinhamento_2026-11-11.md) registra a matriz, a ordem dos cinco blocos e o resultado aplicado. Consulte a pasta CRM2 no ClickUp para o andamento atual.

**Evidência da base consultada.** Branch `codex/delivery-first-integration`, revisão `f6a9a22`. Referências na árvore consultada: `docs/reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md`, `deploy/README.md`, `backend/tests/test_migration_upgrade.py` e `docs/planning/clickup/CLICKUP_REWORK_RESULT_2026-11-11.json`. O documento é um plano. Os testes novos e a homologação descritos acima ainda não foram executados.

*Rascunho elaborado com EGM.*
