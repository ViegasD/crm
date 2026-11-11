# EGM 7 · Crítica da especificação

Alvo: crm2_mvp_comercial.md, linhas 1–248. Revisores design, structural e style concluíram as leituras. Sol low substituiu Luna nas duas últimas personas.

| ID | Persona | Severidade | Linhas | Achado |
| --- | --- | --- | --- | --- |
| 7-D1 | Design | Blocker | 68–72, 134, 197, 223–227 | Confirmar na fundação que o canal distingue anúncio, reentrega, continuidade e nova entrada distinta. A elegibilidade do número não comprova o sinal que habilita a criação automática. A ausência de evidência deve ficar como dependência de aceite. |
| 7-D2 | Design | Major | 114–116, 128, 134 | Especificar autenticação da origem, resolução da conta validada e tratamento de conta desconhecida ou desativada. Proteger consistência entre registrar evento e criar captação sob reentrega simultânea ou falha parcial. |
| 7-D3 | Design | Major | 64–66, 140–147, 164–166, 182 | Definir o que o operador pode conferir após transferir a conversa, distinguindo permissão sobre evento próprio e conteúdo atual da conversa. |
| 7-D4 | Design | Major | 23, 128, 140–149 | Determinar revogação para sessões já abertas e destino de oportunidades, atendimentos e tarefas do operador desativado sem apagar créditos históricos. |
| 7-D5 | Design | Major | 62–64, 164–166, 180, 197 | Tratar interrupção após envio com resultado inconclusivo, risco de reenvio e impacto na primeira resposta e fila. |
| 7-E1 | Structural | Major | 124–201 | Dar subtítulos ao plano técnico por área e ao diagrama e tabela de integração, para facilitar navegação e revisão. |
| 7-E2 | Structural | Major | 241–245 | Comparar reabertura com histórico de eventos de fechamento à nova oportunidade vinculada, pois o primeiro modelo também pode preservar o histórico com outro custo. |
| 7-E3 | Structural | Nit | 42, 126, 193 | Identificar a revisão f6a9a22 na tabela hoje rotulada como checkout local. |
| 7-E4 | Structural | Nit | 201, 209, 233, 239, 245 | Referenciar decisão registrada quando disponível e manter racional técnico explícito. |
| 7-S1 | Style | Major | 42, 126, 193, 215 | Unificar a identificação da revisão inspecionada e separar leitura estática de verificação em execução. |
| 7-S2 | Style | Major | 15, 220 | A inspeção constatou contagem igual e rótulos/valores diferentes. Ela não demonstrou que os relatórios calcularam a mesma métrica sobre os mesmos negócios. |
| 7-S3 | Style | Nit | 44, 247 | Remover repetição sobre carga inicial e confirmação com a agência. |
| 7-S4 | Style | Nit | 130, 184 | Dizer quais ajustes de captação ficam expostos no MVP e quais ficam localizados para evolução posterior. |
| 7-S5 | Style | Nit | 164, 166, 180 | Padronizar o nome do indicador e distinguir o evento que encerra a medição. |
