# HANDOFF COMPLETO — Agência de marketing, CRM e gestão de entregas
Atualização: 09/11/2026. Idioma: português brasileiro.

> Organizacao local em 11/11: os ZIPs originais e o PDF disponivel estao em `docs/sources/`. Os caminhos `fontes/`, `propostas/` e o manifesto mencionados no handoff abaixo pertencem ao pacote de origem; nao estao todos presentes neste checkout. O TXT das conversas pode ser lido dentro dos ZIPs. Para o estado posterior, consulte `SCOPE.md`, `ESCOPO_STATUS_CRM2.md` e `docs/README.md` a partir da raiz.

## Leia primeiro
A decisão MAIS RECENTE é a prioridade do MVP: **gestão de entregas de marketing e e-commerce**. CRM comercial fica em segundo plano. A proposta é comercial, não contrato; PDF detalhado, sem cabeçalho identificando destinatário/proponente e SEM valores. Não incluir revenda/distribuição agora.

## Arquivos entregues
- `fontes/Conversa do WhatsApp com Ruan Moreira.zip`: arquivo original INTEGRAL, incluindo conversa exportada e anexos (áudios, vídeos, imagens). Não foi alterado. É grande (~370 MB).
- `fontes/Conversa do WhatsApp com Ruan Moreira.txt`: texto extraído da conversa, para busca rápida.
- `propostas/`: quatro PDFs anteriores, preservados como histórico, NÃO necessariamente atualizados à prioridade de 09/11.
- `inventario_arquivos.json`: manifesto.
**Atenção:** os áudios e vídeos não foram transcritos/analisados integralmente. Não afirmar que o resumo esgota os requisitos.

## Contexto e origem
Contato: Ruan Moreira; interlocutor técnico nas mensagens: Fábio. Agência de marketing e consultoria comercial, com aproximadamente 46 clientes, que também implementa CRMs para clientes. Serviços mencionados: redes sociais, tráfego pago, sites, fotos/vídeos, treinamento comercial; contratos de 6 ou 3 meses, parcelamentos, recorrência e avulsos. Sistema anterior associado ao perfil Avancer CRM, com relatos de lentidão, manutenção insatisfatória, dependência do fornecedor e falta de integração com Asaas. Fonte principal: conversa de 05 e 06/11/2026 no TXT.

## Histórico das necessidades (NÃO confundir com MVP aprovado)
05/11: Ruan listou CRM comercial (leads, Kanban, carteira, WhatsApp com coexistência e origem), financeiro, equipe de marketing, métricas de anúncio e performance de marketing/tráfego/comercial. Também mencionou operação de 'aluguel de vendedor': vendedor na agência atendendo até ~5 lojistas, conversas segmentadas e métricas. Em 06/11: financeiro com entradas/saídas, contratos, Asaas em paralelo; e-commerce demonstrado em vídeos anexos.
Inicialmente o assistente propôs MVP de CRM comercial + WhatsApp multinúmero, coexistência no aplicativo WhatsApp Business, dashboards e usuários.

## CORREÇÃO MAIS RECENTE — 09/11
Ruan enviou ao usuário:
> ficou invertido
> comentei cntg q o mvp
> tem q garantir a parte de entrega
> marketing e ecom
> comercial a gente deixa de segundo plano
> pq isso precisa ta rodando

Consequência: inverter prioridades. O MVP é operação e entrega de marketing/e-commerce, não CRM de vendas. **Não existe confirmação de que WhatsApp multinúmero/coexistência tenha sido definitivamente excluído: confirmar se necessário para fluxo de entregas.**

## Escopo de MVP PROPOSTO (a validar com a agência)
1. Clientes e serviços: cadastro, contratos/serviços associados em nível operacional, responsáveis e projetos.
2. Marketing: demandas de artes, vídeos, conteúdo, campanhas/tráfego; Kanban, tarefas, prioridades, responsáveis, prazos, comentários, anexos, revisão, ajustes, aprovações internas, histórico e conclusão.
3. E-commerce: projetos de implantação/manutenção de lojas virtuais, etapas, checklists, pendências, responsáveis, prazos, revisão e entregas. Não significa desenvolver a própria plataforma de e-commerce.
4. Usuários: autenticação e perfis básicos (admin, gestor, colaborador).
5. Painel: demandas abertas, em execução, concluídas, atrasadas e aguardando revisão, filtradas por cliente/responsável/período.
Esses itens foram organizados pelo assistente e ainda NÃO foram todos confirmados por Ruan.

## Critérios de aceite propostos
Cadastrar cliente e serviços; criar e atribuir demandas; mover etapas; anexar arquivos/comentar; solicitar revisão, aprovar e concluir; criar projeto de e-commerce e checklist; restringir acessos por perfil; visualizar indicadores coerentes; implantar em ambiente de produção. Definir cenários testáveis antes do contrato.

## Posterior / fora do compromisso inicial
CRM comercial, funis de vendas, automações, WhatsApp multinúmero com coexistência (salvo revisão de prioridade), financeiro completo e Asaas, IA, e-commerce avançado, módulo de vendedor compartilhado, revenda/sublicenciamento/white-label e distribuição a terceiros.

## Modelo de negócios acordado em princípio
Licenciamento SaaS; desenvolvedor mantém propriedade intelectual. Não fazer sociedade com agência neste momento. Desenvolvimento/implantação sem taxa inicial, absorvidos no licenciamento. Foi debatido R$ 2.000/mês, mas usuário pediu expressamente **proposta SEM valores**. Fidelidade de 12 meses foi sugerida, NÃO confirmada. Distribuição para os 46 clientes foi debatida e deixada para o futuro: NÃO incluir direitos de revenda agora. Custos de APIs, infraestrutura, limites de suporte e expansão precisam ser definidos.

## Prazo
Usuário desenvolverá do zero com agentes de programação IA e considerou 8–14 semanas excessivo. Meta preliminar discutida: 20 dias úteis. Cronograma sugerido para novo MVP: dias 1–4 base/usuários/clientes; 5–10 marketing; 11–15 e-commerce; 16–18 dashboard/revisões; 19–20 testes/implantação. Estimativa condicional, não garantia; reavaliar após mapear fluxos reais.

## Preferências do documento
Português do Brasil; PDF profissional e detalhado; sem cabeçalho de identificação e sem valores; contrato só depois. PDFs anteriores em `propostas/` são histórico e podem conter escopo ou valores desatualizados. Não copiá-los sem revisão.

## Perguntas a esclarecer
- Portal para clientes acompanharem/aprovarem entregas ou operação apenas interna?
- Fluxos concretos e etapas de marketing e e-commerce?
- Quais serviços e equipes serão usados inicialmente?
- Permissões, quantidade de usuários, anexos, armazenamento, notificações, indicadores?
- WhatsApp multinúmero/coexistência será necessário para entregas no MVP ou fica totalmente depois?
- Critérios de aceite e cronograma final?
- Regras de suporte, infraestrutura, licenciamento e rescisão quando chegar a hora do contrato?

## Próxima ação
Revisar as mensagens originais, principalmente 05–06/11 e a correção de 09/11 (esta última consta neste handoff, não necessariamente no ZIP exportado); mapear requisitos; confirmar dúvidas essenciais com o usuário/Ruan; atualizar proposta em PDF SEM valores e SEM cabeçalho; não redigir contrato ainda.

## Limitações
Não presumir que todos os 46 clientes pagam CRM. Não confundir desejos históricos com requisitos aprovados. Não inventar razão social, valores, prazos garantidos ou funcionalidades da Meta. Material de WhatsApp pode conter dados pessoais e arquivos privados: tratar como confidencial.
