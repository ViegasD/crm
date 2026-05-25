# Modo de trabalho - CRM2

Regra operacional do projeto:

- O desenvolvimento sera feito por stage.
- Sempre que um stage for trabalhado, o que foi feito deve ser comparado com as tarefas correspondentes no ClickUp.
- Ao concluir ou avançar uma parte do stage, o progresso deve ser registrado no ClickUp.
- Tarefas so devem ser marcadas como concluidas quando o codigo estiver realmente implementado, integrado e validado.
- Se o codigo mostrar que uma tarefa marcada como concluida ainda nao esta funcional, isso deve ser apontado antes de seguir.
- O status do ClickUp deve refletir o estado real do repositorio, nao apenas a intencao arquitetural.
- Ao terminar qualquer entrega, separar claramente o que foi validado pelo Codex e o que ainda precisa de validacao manual pelo Thiago.
- "Feito" nao significa apenas compilar ou passar lint. Feito significa: implementado, validado tecnicamente, testado manualmente quando necessario, e registrado no ClickUp com evidencias.

Checklist antes de fechar qualquer stage:

- Implementacao feita no repositorio.
- Contratos frontend/backend conferidos, quando aplicavel.
- Validacao tecnica executada pelo Codex.
- Lista de testes manuais obrigatorios entregue para o Thiago.
- Resultado dos testes manuais considerado antes de fechar o item como concluido.
- Evidencias/resumo registrados no ClickUp.
- Tarefas do stage atualizadas no ClickUp.

Formato obrigatorio ao finalizar uma entrega:

1. Status
   - O que foi implementado.
   - O que mudou em backend, frontend, banco, workers, integracoes ou Docker.

2. Validado pelo Codex
   - Comandos executados: lint, type-check, build, migrations, smoke API, smoke Docker, navegador local, logs.
   - Resultado objetivo de cada validacao.
   - Qualquer ponto que nao foi possivel validar tecnicamente.

3. Testes manuais obrigatorios do Thiago
   - Passo a passo do que deve ser testado na UI ou com integracoes reais.
   - Casos de tentativa e erro: cancelar, duplicar, trocar tela, recarregar, testar erro, testar dado real.
   - Integracoes que dependem de provedor real, numero WhatsApp, QR code, Meta/Evolution, permissao externa ou credencial real.

4. Criterio de aprovacao
   - O comportamento esperado para considerar a entrega pronta.
   - O que deve aparecer na UI, no banco, nos logs, no webhook ou no ClickUp.

5. Riscos e pendencias
   - O que ainda pode quebrar.
   - O que ficou sem teste automatizado.
   - O que deve virar nova task, reabrir task existente ou ir para outro stage.

6. ClickUp
   - Registrar comentario com resumo e evidencias.
   - So marcar como Closed quando a validacao tecnica e a validacao manual necessaria estiverem coerentes com o criterio de aprovacao.
   - Se a entrega for parcial, usar status/progresso parcial e comentar exatamente o que falta.
