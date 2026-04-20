# Avaliação e Métricas

## Como Avaliar seu Agente

A avaliação do CreditAI foi realizada por meio de testes estruturados, simulando interações reais com o fluxo principal do agente, além de cenários fora do escopo e entradas inválidas.

O objetivo foi validar:

- capacidade de localizar o cliente na base histórica;
- coerência dos cálculos financeiros;
- comportamento do agente diante de perguntas fora do escopo;
- segurança ao lidar com informações inexistentes;
- qualidade das recomendações geradas.

---

## Métricas de Qualidade

| Métrica           | O que avalia                                     | Resultado observado                                                                                                                                        |
| ----------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Assertividade** | O agente respondeu o que foi perguntado?         | Sim. O agente conseguiu localizar clientes válidos, calcular parcela, valor total pago, juros e classificar risco.                                         |
| **Segurança**     | O agente evitou inventar informações?            | Sim. Quando não encontrou o cliente ou recebeu perguntas fora do fluxo, informou sua limitação e redirecionou a conversa.                                  |
| **Coerência**     | A resposta faz sentido para o perfil do cliente? | Sim. Clientes com renda comprometida tiveram risco alto/médio, enquanto clientes com melhor histórico e baixa relação parcela/renda receberam risco baixo. |

---

## Exemplos de Cenários de Teste

Crie testes simples para validar seu agente:

### Teste 1: Busca do cliente na base
- **Pergunta:** "Cassia Silva Silverio"
- **Resposta esperada:** O agente encontra o cliente e carrega seu histórico.
- **Resultado:** [x] Correto  [ ] Incorreto
Observação: O cliente foi localizado com sucesso, com base histórica carregada para a simulação.

### Teste 2: Simulação de alto risco
- **Pergunta:** "Crédito de R$ 300.000,00, prazo 120 meses, taxa 2,5%"
- **Resposta esperada:** Parcela elevada, alto comprometimento da renda e classificação de risco alto.
- **Resultado:** [x] Correto  [ ] Incorreto

Resposta observada:
- Parcela: R$ 7.908,54
- Valor total pago: R$ 949.024,55
- Juros totais: R$ 649.024,55
- Comprometimento da renda: 359,5%
- Classificação: Risco alto

Conclusão: A resposta foi coerente, pois a parcela ficou muito acima da capacidade financeira da cliente.

### Teste 3: Simulação de risco médio
- **Pergunta:** "Crédito de R$ 10.000,00, prazo 24 meses, taxa 1,5%"
- **Resposta esperada:** Parcela moderada, comprometimento intermediário e risco médio.
- **Resultado:** [x] Correto  [ ] Incorreto

Resposta observada:
- Parcela: R$ 499,24
- Valor total pago: R$ 11.981,78
- Juros totais: R$ 1.981,78
- Comprometimento da renda: 22,7%
- Classificação: Risco médio

Conclusão: A resposta foi coerente com a regra definida no projeto, já que o comprometimento ficou entre 20% e 30%.

### Teste 4: Pergunta fora do escopo
- **Pergunta:** "qual a previsão do tempo hoje em jundiaí?"
- **Resposta esperada:** O agente informa que atua no contexto financeiro.
- **Resultado:** [ ] Correto  [ ] Incorreto
- 
Resposta observada: Não encontrei esse nome na base. Digite exatamente o nome cadastrado no histórico.

Conclusão: Neste cenário, o agente não respondeu de forma ideal, porque interpretou a pergunta como tentativa de busca de cliente. Há oportunidade de melhoria no tratamento de mensagens fora do escopo logo no início da conversa.

Teste 5: Saudação fora do fluxo
- **Pergunta**: "olá"
- **Resposta esperada**: O agente se apresenta e orienta o usuário a iniciar pelo nome completo.
- **Resultado**: [x] Correto [ ] Incorreto

Resposta observada: Sou o CreditAI, seu educador financeiro, e meu foco é ajudar com simulações de crédito. Para começar, preciso que você digite seu nome completo para localizar seu histórico.

Conclusão: O agente respondeu corretamente, mantendo o contexto do produto e direcionando o usuário para o fluxo esperado.

Teste 6: Cliente inexistente
- **Pergunta**: "Maria da Silva Teste"
- **Resposta esperada**: O agente informa que não encontrou o cliente na base.
- **Resultado**: [x] Correto [ ] Incorreto

Resposta observada: Não encontrei esse nome na base. Digite exatamente o nome cadastrado no histórico.

Conclusão: O comportamento está correto, evitando inventar dados e mantendo segurança na resposta.

- Teste 7: Entrada inválida no início do fluxo
- **Pergunta**: "quero saber de investimentos"
- **Resposta esperada**: O agente orienta o usuário a informar o nome completo.
- **Resultado**: [x] Correto [ ] Incorreto

Resposta observada: Não encontrei esse nome na base. Digite exatamente o nome cadastrado no histórico.

Conclusão: Embora funcional, a resposta pode ser melhorada para diferenciar uma entrada inválida de uma tentativa real de busca de cliente.

Teste 8: Entrada inválida no prazo
- Pergunta: "não sei"
- Resposta esperada: O agente solicita novamente o prazo em meses.
- Resultado: [x] Correto [ ] Incorreto

Resposta observada: Entendi. Eu sou o CreditAI e posso te ajudar com essa simulação. Agora preciso que você informe o prazo de pagamento em meses.

Conclusão: O agente conseguiu manter o fluxo corretamente e orientar o usuário sem quebrar a experiência.

Teste 9: Entrada inválida na taxa
- **Pergunta**: "qual você recomenda?"
- **Resposta esperada**: O agente solicita a taxa para continuar a simulação.
- **Resultado**: [x] Correto [ ] Incorreto

Resposta observada: Posso te orientar na simulação de crédito. Para continuar, me informe a taxa de juros mensal que deseja considerar, por exemplo: 2,5.

Conclusão: O comportamento está adequado, mantendo o foco no fluxo e evitando assumir valores automaticamente.

Teste 10: Coerência com histórico do cliente
- **Pergunta**: Simulação com cliente de bom perfil (Bruno) — R$ 10.000,00 em 24 meses a 1,0%
- **Resposta esperada**: Classificação de risco baixa e recomendação coerente com histórico positivo.
- **Resultado**: [x] Correto [ ] Incorreto

Resposta observada:
- Parcela: R$ 470,73
- Valor total pago: R$ 11.297,63
- Juros totais: R$ 1.297,63
- Comprometimento da renda: 6,3%
- Classificação: risco baixo

Trecho relevante:
- "Você possui histórico de pagamentos pontual e score de crédito 820, o que ajuda na leitura do seu perfil."

Conclusão: A resposta foi coerente com o perfil do cliente, demonstrando uso adequado do histórico para personalização e tomada de decisão.
---

## Resultados

Após os testes, registre suas conclusões:

**O que funcionou bem:**
- Busca de clientes válidos na base histórica
- Personalização da resposta com nome, renda, score e histórico
- Cálculo de parcela, juros totais e valor total pago
- Classificação de risco coerente com o comprometimento da renda
- Redirecionamento em entradas inválidas durante o fluxo
- Boa coerência entre histórico positivo e recomendação final

**O que pode melhorar:**
- Melhor tratamento de perguntas fora do escopo no início da conversa
- Diferenciar melhor “nome inválido” de “mensagem fora do contexto”
- Tornar a resposta inicial mais flexível para saudações e perguntas livres
- Melhorar a naturalidade de algumas mensagens de erro

---

## Notas sugeridas (1 a 5)
Com base nos testes realizados:

- Assertividade: 4/5
- Segurança: 4/5
- Coerência: 5/5

Média geral: 4,3/5
