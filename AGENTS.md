# CRM2

Comece por [Como retomar o CRM2](docs/context/CONTINUIDADE_CRM2.md). Esse documento aponta para o desenho vigente, a revisão da base e a fila de trabalho. As referências datadas de marketing e e-commerce servem como histórico.

## Revisores Goldfish do EGM

Ao executar uma revisão Goldfish, defina explicitamente o modelo e o esforço de cada revisor.

| Persona do EGM | Modelo | Esforço | Foco |
| --- | --- | --- | --- |
| `egm-structural`, `egm-style` | `gpt-6-luna` | `low` | Estrutura, manutenção documental e clareza |
| `egm-comprehension` | `gpt-6-luna` | `medium` | Entendimento independente, premissas e ambiguidades |
| `egm-zoom-out`, `egm-design` | `gpt-6.1-sol` | `medium` | Escopo, simplicidade, arquitetura e riscos |
| `egm-codebase-details` | `gpt-6.1-sol` | `medium` | Conferência com código, contratos e evidência verificável |
| `egm-implementation-readiness` | `gpt-6.1-sol` | `medium` | Migração, execução, testes e critérios de aceite |
| `egm-inventive-catalyst` | `gpt-6.1-sol` | `medium` | Contradições e alternativas de desenho |

- Abra cada Goldfish com `fork_turns: "none"`. Passe a persona instalada, o alvo, os padrões requeridos e apenas a lista de leitura necessária. Na revisão de compreensão, siga a entrada mais restrita do EGM para testar se o texto se sustenta sozinho.
- Despache diretamente e consolide no agente principal quando o fluxo permitir. Respeite as vagas da sessão. Se precisar de lotes, congele a entrada e mantenha os achados das outras personas fora de cada contexto.
- Peça achados acionáveis com evidência e severidade, preservando o formato obrigatório da persona. Use os revisores exigidos pelo fluxo escolhido. Uma revisão dirigida pode selecionar apenas as personas relevantes. Uma falha de execução deve ser registrada conforme a regra do fluxo.
- Suba para `gpt-6.1-sol` `high` apenas para um bloqueador ou uma decisão de alto impacto que permaneça aberta com evidência. Se ainda houver impasse técnico, uma segunda opinião pontual pode usar `gpt-6-astra` `medium`. Reserve rodadas adicionais aos critérios e aprovações do EGM.
