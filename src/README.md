# 💬 CreditAI - Agente Financeiro Inteligente

O **CreditAI** é um agente financeiro desenvolvido em Python com Streamlit que simula crédito de forma personalizada com base no histórico do cliente.

O objetivo do projeto é apoiar decisões financeiras com **análise de risco, cálculo de parcelas e recomendações**, evitando respostas incorretas ou "alucinações".

---

## 🚀 Funcionalidades

* 🔍 Identificação do cliente pelo nome completo
* 📊 Leitura automática do histórico financeiro
* 💰 Simulação de crédito (valor, prazo e taxa)
* 📈 Cálculo de:

  * Parcela mensal
  * Valor total pago
  * Juros totais
  * Comprometimento da renda
* ⚠️ Classificação de risco (Baixo, Médio, Alto)
* 💡 Recomendação personalizada
* 🤖 Respostas seguras (sem inventar dados)

---

## 🏗️ Estrutura do Projeto

```
.
├── creditai_app.py
├── data/
│   ├── amostra_perfil_sidebar.csv
│   └── regras_credito.json
├── requirements.txt
└── README.md
```

---

## ⚙️ Tecnologias Utilizadas

* Python
* Streamlit
* Pandas

---

## 📊 Base de Conhecimento

O agente utiliza dados estruturados locais:

### `amostra_perfil_sidebar.csv`

Contém:

* Nome do cliente
* Renda mensal
* Score de crédito
* Histórico de pagamentos
* Empréstimos anteriores

### `regras_credito.json`

Define:

* Limites de risco
* Regras de classificação
* Mensagens padrão do agente

---

## 🧠 Como o Agente Funciona

1. O usuário informa o **nome completo**
2. O agente busca o cliente na base
3. Carrega automaticamente o histórico
4. Solicita:

   * Valor do empréstimo
   * Prazo
   * Taxa de juros
5. Realiza os cálculos financeiros
6. Classifica o risco
7. Gera uma recomendação personalizada

---

## 📦 Instalação e Execução

### 1. Clonar o repositório

```bash
git clone https://github.com/Cassia-s/dio-lab-bia-do-futuro.git
cd dio-lab-bia-do-futuro
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Executar o app

```bash
streamlit run creditai_app.py
```

---

## 📌 Exemplo de Uso

**Entrada:**

* Nome: Cassia Silva Silverio
* Valor: R$ 10.000
* Prazo: 24 meses
* Taxa: 1,5%

**Saída:**

* Parcela: R$ 499,24
* Juros totais: R$ 1.981,78
* Risco: Médio
* Recomendação: Ajustar prazo ou valor

<img width="875" height="285" alt="image" src="https://github.com/user-attachments/assets/416af1de-275f-4b6f-9518-c76ad702851c" />


---

## 🔒 Segurança e Anti-Alucinação

* O agente **só responde com base nos dados disponíveis**
* Não inventa informações financeiras
* Quando não encontra dados, informa claramente
* Mantém o usuário dentro do contexto financeiro

---

## ⚠️ Limitações

* Base de dados fictícia (mock)
* Não utiliza API externa (LLM)
* Busca por nome ainda depende de escrita correta
* Não realiza recomendações de investimento

---

## 🚀 Melhorias Futuras

* Busca inteligente de nome (fuzzy matching)
* Integração com IA (OpenAI ou Ollama)
* Dashboard analítico
* Score dinâmico com machine learning
* Autenticação de usuário

---

## 👩‍💻 Autora

Cassia Silva
Projeto desenvolvido como parte do desafio DIO - IA Generativa aplicada a Finanças

---
