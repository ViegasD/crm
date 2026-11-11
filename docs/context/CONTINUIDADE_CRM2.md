# Como retomar o CRM2

O [escopo vigente](../../SCOPE.md) inclui CRM comercial, entregas de marketing e projetos de e-commerce. M1–M5 são os blocos do desenho comercial. A fila conjunta fica na pasta CRM2 do ClickUp, com MVP 03 para entregas de marketing e MVP 04 para projetos de e-commerce. Os códigos D03.x e D04.x nessas listas se referem a essas duas frentes.

## Leia nesta ordem

1. [Desenho do MVP comercial](../planning/crm2_mvp_comercial.md) para escopo, contratos, migrações e aceite.
2. [Revisão de código e realinhamento](../reports/crm2_code_review_e_realinhamento_2026-11-11.md) para reuso, lacunas, tarefas e evidências. A base auditada foi `f6a9a22ab79cf1b8cff9b4bb1c35ed516d8b13ff`, do [PR #1](https://github.com/ViegasD/crm/pull/1). Para trabalho novo, confirme o estado do PR, a branch comum e o commit atual com a equipe.
3. Pasta **CRM2** no ClickUp para títulos, aceite, andamento, responsáveis e dependências atuais. Confira o título e o aceite junto com o código Dxx.x, pois o relatório histórico registrou alguns códigos com outras finalidades. A [resolução EGM](../reports/egm-mvp-comercial/goldfish_review_report.md) registra as decisões incorporadas ao desenho comercial.
4. [Runbook de desenvolvimento](../../deploy/README.md) e [relatório histórico de validação](../reports/DEPLOYMENT_DEVELOPMENT_2026-11-11.md) para executar e interpretar as verificações. Peça à equipe as permissões e a configuração privada necessárias.

## Primeira rodada

- **D01.1.** Confirmem a revisão compartilhada e registrem uma execução das verificações da base. Usem branches separadas por tarefa. Na estação que tem trabalho local de Stage 5, usem um checkout isolado.
- **D01.2 e D01.5.** Priorizem a regra de acesso por workspace e conversa privada, a partir da matriz da D00.2, e a validação das migrações em banco descartável. São duas frentes para dividir entre os contribuidores.
- **Marketing e e-commerce.** Validem os fluxos reais na D00.1. Consultem as listas MVP 03 e MVP 04 para escolher o próximo trabalho e conferir seus critérios de aceite.
- **Frontend em paralelo.** O filtro por número usa a API de contas e o parâmetro `channel_account_id`. Validem com duas contas sintéticas, filtros combinados e atualizações da lista. Confiram o vínculo com a tarefa de WhatsApp vigente antes de abrir o PR.
- **Limpeza.** A revisão não comprovou candidatos à retirada. Proponha remoções pontuais com evidência sobre consumidores, dados, migrações e regressões.

Quando alternarem tarefas, deixem no ClickUp o link da branch ou PR, as verificações executadas, as pendências e o próximo passo. Separem o aceite manual da evidência automatizada. A definição de acesso e a autorização dos números oficiais dependem da agência. Backup automatizado, restauração e alertas dependem da configuração do ambiente de produção.

## Para agentes

Leia também [AGENTS.md](../../AGENTS.md). Trate o desenho como contrato e o ClickUp como fila de execução. Valide o commit antes de atribuir um resultado à base. Para alterações de código, use a menor implementação completa e a verificação proporcional ao risco. Quando o agente tiver acesso a Ponytail, use o modo full. Para um novo repasse, use handoff ou registre o mesmo conjunto mínimo de fatos no PR e na tarefa. Use a revisão EGM dirigida quando houver uma pergunta concreta de contrato ou reuso.
