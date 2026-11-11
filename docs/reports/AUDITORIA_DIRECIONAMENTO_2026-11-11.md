# Auditoria de direcionamento e implementação - CRM2

Data: 11/11/2026. Avaliação do checkout local, incluindo alterações ainda não commitadas. Esta auditoria não altera código de produto nem status no ClickUp.

> Atualizacao posterior no mesmo dia: a auditoria abaixo preserva o retrato anterior ao fetch. Foram encontrados commits remotos com implementacao Stage 9 e timeline, ausentes daquele checkout. O usuario autorizou integracao e realinhamento do ClickUp. Consulte `docs/planning/REALINHAMENTO_2026-11-11.md` e `docs/reports/INTEGRACAO_VALIDACAO_2026-11-11.md` para o estado posterior; ausencia local nao deve ser interpretada como ausencia nas branches remotas.

## Parecer

O MVP mudou para gestão de entregas de marketing e e-commerce. O repositório e o planejamento no ClickUp ainda representam principalmente atendimento omnichannel/CRM. Há uma fundação reutilizável, mas o fluxo principal do novo produto ainda não foi implementado. Percentuais de conclusão do roadmap antigo não medem o avanço do novo MVP.

## Fontes e precedência

1. A conversa de 09/11/2026, às 09:22-09:23, no ZIP menor em `docs/`, confirma diretamente a inversão: garantir entregas de marketing/e-commerce e deixar comercial em segundo plano.
2. `docs/context/HANDOFF_COMPLETO.md`, de 09/11, registra essa decisão e distingue prioridade confirmada de detalhamento proposto.
3. O TXT dentro do ZIP de Ruan contextualiza as necessidades históricas de 05-06/11: marketing, tráfego, comercial, financeiro e e-commerce. Áudios e vídeos não foram transcritos nem analisados nesta auditoria.
4. `docs/sources/Proposta.pdf`, seção 1, prioriza o núcleo comercial; seção 7 exclui gestão de projetos de marketing, aprovações e e-commerce. Portanto, está superada pela decisão de 09/11 e precisa ser revisada antes de novo uso comercial.
5. `SCOPE.md` é um escopo extenso de CRM omnichannel com IA. `STRUCTURE.md` mistura estrutura prevista com arquivos efetivos: não comprova implementação. `API.md` documenta APIs de atendimento, sem domínio de entregas.
6. `ESCOPO_STATUS_CRM2.md` tem auditoria datada de 21/05/2026: token inválido, contagens antigas e ausência de outbound não descrevem integralmente o estado atual.
7. `MODO_DE_TRABALHO_CRM2.md` exige confrontar stages com código integrado e validado antes de considerá-los concluídos.

A prioridade de entregas está confirmada. Kanban, revisão, checklists, papéis, painel e demais itens detalhados no handoff são uma proposta de solução, ainda pendente de validação com a agência. Não tratá-los como um contrato aprovado. E-commerce significa gestão de implantação/manutenção de lojas no escopo proposto; não há confirmação de construção de uma plataforma de comércio eletrônico própria.

## Cobertura do novo MVP proposto

| Área | Evidência no código | Avaliação |
| --- | --- | --- |
| Autenticação, workspace e equipe | `backend/app/models/workspace.py`, APIs de auth/workspaces/setores | Fundação reutilizável; onboarding e autorização incompletos |
| Clientes e serviços operacionais | Contatos com empresa, documento, telefones e e-mails | Cadastro reaproveitável; faltam serviços contratados, responsáveis operacionais e vínculo com projetos |
| Demandas de marketing | Sem modelos, migrations, APIs ou telas de demandas/projetos | Não implementado |
| Etapas/Kanban, prioridade, responsável e prazo de entregas | Status/atribuição existentes pertencem a conversas; prazo existente em SLA é de atendimento | Não implementado para entregas |
| Comentários, anexos e histórico de entregas | Notas, mídia e eventos vinculados a conversas | Componentes reaproveitáveis; vínculo e regras de tarefas ainda ausentes |
| Revisão, ajustes e aprovação | Sem domínio de revisão/aprovação de entregas | Não implementado |
| Projetos de e-commerce e checklists | Sem modelos, migrations, APIs ou telas correspondentes | Não implementado |
| Indicadores de entregas por cliente/responsável/período | `frontend/src/app/(dashboard)/reports/page.tsx` retorna apenas `Reports` | Não implementado |
| Produção e aceite do novo MVP | Não foi executado fluxo integrado de entregas; domínio ausente | Não demonstrado |

A inspeção incluiu inventário de modelos, migrations, rotas registradas, páginas e busca de termos do novo domínio. A aplicação importada registra 28 tabelas e 47 caminhos OpenAPI; nenhum corresponde a projetos/tarefas/checklists/aprovações de entregas. A navegação principal continua Inbox, Contacts, Flows, Reports e Settings; login encaminha para `/inbox`.

## ClickUp: autenticação, configuração e retrato live

- `GET /api/v2/user` respondeu com sucesso: a chave atual é válida. Não há evidência de expiração.
- A configuração local resolve `CLICKUP_FOLDER_ID=9013086181`. Esse identificador pertence a um workspace ClickUp e retorna HTTP 404 / `SHARD_006` ao ser usado como folder.
- A pasta CRM2 acessível está no espaço `viponline`, com ID **901318283724**. A consulta funcionou passando esse ID explicitamente. A configuração local não foi alterada.
- Retrato coletado com `include_closed=true`, `subtasks=true` e paginação: **23 listas, 138 tarefas, 32 com tipo de status `closed`, 106 não fechadas**. As não fechadas incluem tarefas em revisão.
- Snapshot sem credenciais: `docs/archive/clickup/CLICKUP_SNAPSHOT_2026-11-11.json`. Inclui IDs, nomes, estados e URLs para rastreabilidade.
- As listas ainda seguem o roadmap antigo. Referências a Shopify, vertical packs e e-commerce no inbox não equivalem a gestão de entregas de projetos e-commerce.
- Nenhuma tarefa foi criada, comentada, reaberta ou encerrada nesta revisão.

### Divergências concretas entre tarefas encerradas e checkout

| Tarefa ClickUp encerrada | ID | Evidência / ressalva |
| --- | --- | --- |
| Middleware de autenticação e autorização | `86ahmdnwq` | Autenticação e membership existem; `require_roles` não é aplicado às rotas. Não representa autorização completa |
| CRUD de workspaces, setores e membros | `86ahmdnx0` | API de membros lista/remove; falta inclusão/convite nessa API. Remoção exige apenas membership |
| Atribuição atômica de conversas | `86ahmdp8y` | Serviço de conversas atribui IDs diretamente, sem mecanismo de capacidade/locking correspondente |
| Cálculo de status SLA por Celery | `86ahmdpac` | Worker registra módulos de mídia e webhooks; beat agenda apenas replay de webhooks. Sem worker de cálculo SLA no checkout |
| Escalonamento automático ao estourar SLA | `86ahmdpaj` | Modelo contém campos de SLA, mas não foi localizado motor de escalonamento |
| Ocupação em tempo real para supervisores | `86ahmdp9j` | API de capacidade expõe limites; não foi encontrado fluxo operacional de ocupação |
| Pausa e redistribuição ao atingir limite | `86ahmdp9a` | Não foi localizado mecanismo de pausa/redistribuição integrado |
| Tabelas agent_capacity e conversation_assignments | `86ahmdp8h` | `agent_capacity` existe; `conversation_assignments` não aparece nos modelos nem nas migrations |

Stage 9 tem 7 tarefas encerradas e 2 não encerradas; o QA manual (`86ahnewwv`) está em `review`. Essas divergências exigem reconciliação antes de confiar no fechamento do stage. Pode existir trabalho em outro branch ou ambiente, mas ele não está demonstrado neste checkout.

Stage 3 tem backend e componentes de UI para participantes/timeline, além de canned responses; o relatório antigo subestima essa cobertura. Isso não equivale a validação integrada de todas as tarefas encerradas. Stage 4 tem implementação de segurança de webhooks, mas esta auditoria não certificou todas as garantias operacionais.

## Riscos técnicos para reutilizar a fundação

### Alta prioridade: autorização administrativa incompleta

`backend/app/api/v1/workspaces.py`, função `remove_member`, exige `require_workspace_member`, sem verificação de administrador. Qualquer membro pode solicitar remoção de outro membro, inclusive administrador. O helper `require_roles` existe em `backend/app/core/dependencies.py`, mas a busca não encontrou uso nas rotas. A diferenciação admin/gestor/colaborador do novo produto ainda precisa ser definida e aplicada.

### Alta prioridade: mídia sem isolamento por workspace na API

`backend/app/api/v1/media.py` autentica o usuário, mas upload aceita `workspace_id` sem conferir membership; presign assina uma `key` arbitrária sem conferir o workspace proprietário. Um usuário autenticado que conheça uma chave de outro workspace pode solicitar sua URL de acesso. Antes de reutilizar mídia em entregas, validar pertencimento e autorização do recurso nos dois endpoints.

### Onboarding incompleto

`backend/app/services/auth_service.py` registra apenas o usuário. O layout do dashboard seleciona o primeiro workspace quando existe, mas não oferece criação/onboarding quando a lista está vazia. Um usuário novo pode autenticar sem conseguir operar o produto.

### Migrações: head único não comprova instalação limpa

O grafo tem head único `202605221215`, mas duas raízes históricas. A raiz `202605210001` usa `Base.metadata.create_all()`/`drop_all()` importando o modelo atual; a outra raiz cria tabelas explicitamente. A ordem de execução e futuras mudanças nos modelos podem causar duplicação ou histórico não determinístico. Não foi feita instalação em banco descartável, upgrade ou downgrade; a correção do schema em ambiente novo continua sem comprovação.

### Correção do diagnóstico antigo de WhatsApp

`backend/app/services/message_service.py`, `send_agent_message`, agora instancia adapter, envia texto/mídia e persiste identidade outbound. Portanto, a afirmação antiga de que o envio só grava no banco está desatualizada. A implementação existe; envio real, credenciais, recibos e comportamento dos providers não foram testados nesta rodada. A utilidade/prioridade de WhatsApp para o novo MVP ainda precisa ser confirmada.

## Validação técnica executada

- Parse AST de 86 arquivos Python em `backend/app` e `backend/migrations`: passou.
- `npm run type-check` em `frontend`: passou, sem diagnóstico TypeScript.
- `python -m alembic heads`: passou com override de processo `DEBUG=false`; head `202605221215`.
- Import de `app.main`, `configure_mappers()` e geração OpenAPI: passaram com o mesmo override; 28 tabelas e 47 caminhos.
- A primeira execução backend falhou porque o ambiente herdado continha `DEBUG=release`, inválido para o booleano de Settings. O override foi apenas para os comandos da auditoria; nenhum arquivo de configuração foi modificado.
- `npm run lint`: falhou com 2 erros de variáveis `r` não utilizadas em `frontend/src/app/(dashboard)/flows/page.tsx:30` e `:33`, além de 1 warning de cleanup de ref em `frontend/src/app/(dashboard)/inbox/page.tsx:113`. O comando exige zero warnings. Nenhum desses arquivos foi editado nesta auditoria.
- Não foram encontrados arquivos de testes automatizados versionados na busca do repositório. Não foram executados testes integrados, build de produção, chamadas de negócio no banco, aplicação de migrations, envio WhatsApp ou deploy.

## Encaminhamento recomendado

Primeiro, validar os fluxos reais de marketing e e-commerce: etapas, entrega concluída, quem revisa/aprova, uso interno versus portal do cliente, serviços iniciais, recorrência das demandas, anexos e papel do WhatsApp. O prazo de 20 dias úteis no handoff é uma estimativa condicional, não uma garantia nem medida de trabalho restante.

Em seguida, alinhar `SCOPE.md`, proposta e ClickUp ao novo foco; preservar o roadmap de CRM como histórico/futuro, sem apagar implementação existente. Corrigir o folder ID local e reconciliar as tarefas encerradas divergentes. A chave não precisa ser renovada com base nesta checagem.

A base existente pode ser aproveitada para autenticação, tenancy, contatos, equipe, armazenamento e eventos, após corrigir autorização/onboarding. O próximo incremento de produto recomendado é um fluxo completo validável de cliente + serviço + demanda + responsável/prazo + etapas + comentário/anexo + revisão/conclusão; depois, projetos/checklists de e-commerce e indicadores. Esta é uma recomendação de sequência, não aprovação de requisitos ou plano de implementação fechado.

## Limites desta revisão

O checkout já continha muitas alterações locais anteriores; foram preservadas. Não houve análise integral dos áudios/vídeos nem inspeção visual do PDF, pois a leitura foi de conteúdo para comparar escopo. A auditoria demonstra desalinhamento documental e ausência do domínio novo no código, mas não mede esforço com precisão nem certifica produção. O snapshot do ClickUp é um retrato de 11/11/2026 e pode mudar depois da consulta.
