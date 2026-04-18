# Base de Conhecimento

## Dados Utilizados

Descreva se usou os arquivos da pasta `data`, por exemplo:

| Arquivo                   | Formato | Utilização no Agente                                                        |
| ------------------------- | ------- | --------------------------------------------------------------------------- |
| `clientes.csv`            | CSV     | Armazena dados simulados de clientes (idade, renda, histórico de crédito)   |
| `simulacoes_credito.csv`  | CSV     | Base com exemplos de simulações de crédito e classificação de risco         |
| `regras_credito.json`     | JSON    | Define regras de decisão (comprometimento de renda, classificação de risco) |
| `parametros_credito.json` | JSON    | Contém taxas, limites e parâmetros usados no cálculo das parcelas           |

---

## Adaptações nos Dados

> Você modificou ou expandiu os dados mockados? Descreva aqui.

Os dados originais foram adaptados para atender ao contexto de simulação de crédito, com foco em análise de risco.

As principais modificações foram:

Criação de uma variável de comprometimento de renda (%)
Inclusão de uma coluna de classificação de risco (baixo, médio, alto)
Padronização dos dados para evitar inconsistências (valores nulos, formatos diferentes)
Anonimização completa dos dados (nomes fictícios e dados simulados)
Redução do escopo para variáveis essenciais, evitando complexidade desnecessária

Além disso, foram criados dados sintéticos para simular diferentes cenários de crédito, permitindo ao agente aprender padrões de decisão.

---

## Estratégia de Integração

### Como os dados são carregados?
> Descreva como seu agente acessa a base de conhecimento.

Os arquivos CSV e JSON são carregados no início da aplicação utilizando Python (pandas e json).
As regras de crédito são mantidas separadas em arquivos estruturados, garantindo flexibilidade e facilidade de manutenção.

Exemplo:

CSV → carregado com pandas
JSON → carregado como dicionário

### Como os dados são usados no prompt?
> Os dados vão no system prompt? São consultados dinamicamente?

A integração foi feita de forma híbrida:

Regras de negócio (não vão para o LLM):
Cálculo da parcela
Cálculo do comprometimento de renda
Classificação de risco
LLM (IA generativa):
Recebe apenas o resultado final já calculado
Gera explicações e recomendações

👉 Ou seja:

O LLM não acessa diretamente os dados brutos
Ele trabalha apenas com um contexto estruturado e validado

Isso reduz significativamente o risco de alucinação.

---

## Exemplo de Contexto Montado

> Mostre um exemplo de como os dados são formatados para o agente.

```
Dados do Cliente:
- Idade: 32 anos
- Renda mensal: R$ 4.500
- Valor solicitado: R$ 10.000
- Prazo: 12 meses

Resultados Calculados:
- Valor da parcela: R$ 950
- Comprometimento da renda: 21,1%
- Classificação de risco: Médio

Regras Aplicadas:
- Até 20%: Baixo risco
- 20% a 30%: Médio risco
- Acima de 30%: Alto risco
...
```
