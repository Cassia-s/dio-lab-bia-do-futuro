# 💬 CreditAI — Educador Financeiro com IA

O **CreditAI** é um agente financeiro desenvolvido para ajudar pessoas a tomarem decisões mais conscientes ao contratar crédito.

Ele simula empréstimos de forma personalizada com base no histórico do cliente, mostrando não apenas a parcela, mas o impacto real da decisão financeira.

---

## 🎯 Objetivo

Ajudar usuários a entenderem:

* quanto vão pagar no total;
* quanto da renda será comprometido;
* e qual o risco da operação.

Tudo isso de forma simples, explicativa e personalizada.

---

## 🚀 Como Funciona

1. O usuário informa o **nome completo**
2. O agente busca o cliente na base de dados
3. Carrega automaticamente:

   * renda
   * score de crédito
   * histórico financeiro
4. Solicita:

   * valor do empréstimo
   * prazo
   * taxa de juros
5. Retorna:

   * valor da parcela
   * valor total pago
   * juros totais
   * comprometimento da renda
   * classificação de risco
   * recomendação personalizada

---

## 🧠 Inteligência do Agente

O CreditAI foi projetado para:

* ✅ Não inventar informações (anti-alucinação)
* ✅ Usar apenas dados reais da base
* ✅ Aplicar regras claras de risco
* ✅ Manter o usuário dentro do contexto financeiro

---

## 📊 Tecnologias Utilizadas

* Python
* Streamlit
* Pandas

---

## 📁 Estrutura do Projeto

```
creditai_app.py
data/
 ├── amostra_perfil_sidebar.csv
 └── regras_credito.json
requirements.txt
README.md
```

---

## ▶️ Como Rodar

```bash
pip install -r requirements.txt
streamlit run creditai_app.py
```

---

## 📌 Exemplo de Uso

Entrada:

* Valor: R$ 10.000
* Prazo: 24 meses
* Taxa: 1,5%

Saída:

* Parcela: R$ 499,24
* Juros: R$ 1.981,78
* Risco: Médio
* Recomendação personalizada
  
<img width="875" height="285" alt="image" src="https://github.com/user-attachments/assets/a14fe91a-fcf2-465e-ba36-1dd2a5e6cb12" />

---

## ⚠️ Limitações

* Base de dados fictícia (mock)
* Busca por nome depende de escrita correta
* Não utiliza API externa (LLM)

---

## 💡 Diferencial

Diferente de simuladores comuns, o CreditAI:

* considera o histórico do cliente
* calcula o impacto real da decisão
* orienta o usuário com base em risco

---

## 👩‍💻 Autora

Cassia Silva
Projeto desenvolvido no desafio DIO — IA Generativa aplicada a Finanças

[https://dio-lab-bia-do-futuro.streamlit.app]
