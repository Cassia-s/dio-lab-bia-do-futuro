import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="CreditAI - Simulador de Crédito", page_icon="💳", layout="wide")

# =========================================================
# Configurações e caminhos
# =========================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "agente_credito_base"
BASE_PATH = DATA_DIR / "base_modelagem_agente.csv"
RULES_PATH = DATA_DIR / "regras_credito.json"

DEFAULT_RULES = {
    "thresholds": {
        "baixo_max": 0.20,
        "medio_max": 0.30
    },
    "peso_default": True,
    "mensagens": {
        "baixo": "O comprometimento da renda está em um patamar saudável.",
        "medio": "O comprometimento da renda exige atenção antes da contratação.",
        "alto": "O comprometimento da renda está elevado e aumenta o risco financeiro."
    }
}

# =========================================================
# Utilitários de carregamento
# =========================================================
@st.cache_data
def load_rules() -> Dict[str, Any]:
    if RULES_PATH.exists():
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_RULES


@st.cache_data
def load_base() -> pd.DataFrame:
    if BASE_PATH.exists():
        return pd.read_csv(BASE_PATH)
    return pd.DataFrame()


@st.cache_data
def load_optional_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


# =========================================================
# Funções de negócio
# =========================================================
def pmt(monthly_rate: float, n_periods: int, principal: float) -> float:
    """Calcula a parcela mensal de um financiamento."""
    if n_periods <= 0:
        return 0.0
    if monthly_rate == 0:
        return principal / n_periods
    factor = (1 + monthly_rate) ** n_periods
    return principal * (monthly_rate * factor) / (factor - 1)



def classify_risk(comprometimento: float, possui_default: bool, rules: Dict[str, Any]) -> Tuple[str, str]:
    thresholds = rules.get("thresholds", {})
    baixo_max = float(thresholds.get("baixo_max", 0.20))
    medio_max = float(thresholds.get("medio_max", 0.30))

    if comprometimento <= baixo_max:
        risco = "Baixo"
    elif comprometimento <= medio_max:
        risco = "Médio"
    else:
        risco = "Alto"

    # Penalização por histórico de default
    if possui_default:
        if risco == "Baixo":
            risco = "Médio"
        elif risco == "Médio":
            risco = "Alto"

    mensagem_base = rules.get("mensagens", {}).get(risco.lower(), "")
    return risco, mensagem_base



def recommendation_text(risco: str, comprometimento: float, parcela: float, renda: float) -> str:
    if risco == "Baixo":
        return (
            "A operação está em uma faixa mais confortável. Ainda assim, é recomendável manter "
            "uma reserva financeira para imprevistos e evitar concentrar grande parte da renda em dívidas."
        )
    if risco == "Médio":
        return (
            "Vale avaliar se existe espaço real no orçamento para essa parcela. Caso queira reduzir o risco, "
            "uma alternativa é aumentar o prazo ou diminuir o valor solicitado."
        )
    reducao_ideal = max(parcela - (renda * 0.30), 0)
    return (
        "O risco está elevado. Para melhorar a simulação, considere reduzir o valor solicitado, aumentar o prazo "
        f"ou buscar uma parcela cerca de R$ {reducao_ideal:,.2f} menor para voltar a uma faixa mais segura."
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )



def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")



def montar_contexto(
    renda_mensal: float,
    valor_solicitado: float,
    prazo_meses: int,
    taxa_mensal: float,
    parcela: float,
    comprometimento: float,
    risco: str,
    possui_default: bool,
    idade: int,
) -> str:
    return f"""
Dados do Cliente:
- Idade: {idade} anos
- Renda mensal: {format_brl(renda_mensal)}
- Valor solicitado: {format_brl(valor_solicitado)}
- Prazo: {prazo_meses} meses
- Taxa mensal: {taxa_mensal:.2f}%
- Histórico de default: {'Sim' if possui_default else 'Não'}

Resultados Calculados:
- Valor da parcela: {format_brl(parcela)}
- Comprometimento da renda: {comprometimento:.1%}
- Classificação de risco: {risco}
""".strip()



def gerar_resposta_agente(
    renda_mensal: float,
    valor_solicitado: float,
    prazo_meses: int,
    parcela: float,
    comprometimento: float,
    risco: str,
    possui_default: bool,
    mensagem_base: str,
) -> str:
    historico_txt = "Além disso, existe sinalização de histórico de default, o que aumenta a atenção nessa análise." if possui_default else "Não há sinalização de default na simulação informada."

    return (
        f"Resumo da situação: para um crédito de {format_brl(valor_solicitado)} em {prazo_meses} meses, "
        f"a parcela estimada fica em {format_brl(parcela)}.\n\n"
        f"Interpretação do risco: o comprometimento da renda está em {comprometimento:.1%}, "
        f"classificando a operação como risco {risco.lower()}.\n\n"
        f"Explicação: {mensagem_base} {historico_txt}\n\n"
        f"Recomendação: {recommendation_text(risco, comprometimento, parcela, renda_mensal)}"
    )



def infer_profile_stats(df: pd.DataFrame, renda_mensal: float, idade: int) -> Optional[Dict[str, Any]]:
    if df.empty:
        return None

    candidates = df.copy()

    renda_cols = [c for c in candidates.columns if "income" in c.lower() or "renda" in c.lower()]
    idade_cols = [c for c in candidates.columns if "age" in c.lower() or "idade" in c.lower()]
    default_cols = [c for c in candidates.columns if "default" in c.lower() or "inad" in c.lower()]

    if not renda_cols or not idade_cols:
        return None

    renda_col = renda_cols[0]
    idade_col = idade_cols[0]

    candidates[renda_col] = pd.to_numeric(candidates[renda_col], errors="coerce")
    candidates[idade_col] = pd.to_numeric(candidates[idade_col], errors="coerce")
    candidates = candidates.dropna(subset=[renda_col, idade_col])

    faixa = candidates[
        (candidates[renda_col].between(renda_mensal * 0.7, renda_mensal * 1.3))
        & (candidates[idade_col].between(idade - 5, idade + 5))
    ]

    if faixa.empty:
        faixa = candidates

    result = {
        "qtd_clientes": int(len(faixa)),
        "renda_media": float(faixa[renda_col].mean()),
        "idade_media": float(faixa[idade_col].mean()),
    }

    if default_cols:
        default_col = default_cols[0]
        faixa[default_col] = pd.to_numeric(faixa[default_col], errors="coerce").fillna(0)
        result["taxa_default"] = float(faixa[default_col].mean())

    return result


# =========================================================
# Interface
# =========================================================
rules = load_rules()
base_df = load_base()
clientes_df = load_optional_csv("clientes.csv")
emprestimos_df = load_optional_csv("emprestimos_ativos.csv")
historico_df = load_optional_csv("historico_credito.csv")

st.title("💳 CreditAI - Simulador de Crédito")
st.caption("Simulação de crédito com classificação de risco e explicação em linguagem natural.")

with st.sidebar:
    st.header("Configurações")
    taxa_mensal = st.slider("Taxa de juros mensal (%)", min_value=0.0, max_value=8.0, value=2.5, step=0.1)
    mostrar_contexto = st.checkbox("Mostrar contexto enviado ao agente", value=True)
    mostrar_bases = st.checkbox("Mostrar visão rápida das bases", value=False)

    st.divider()
    st.write("**Arquivos encontrados**")
    st.write(f"Base consolidada: {'✅' if not base_df.empty else '❌'}")
    st.write(f"Clientes: {'✅' if not clientes_df.empty else '❌'}")
    st.write(f"Empréstimos: {'✅' if not emprestimos_df.empty else '❌'}")
    st.write(f"Histórico: {'✅' if not historico_df.empty else '❌'}")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Entrada do cliente")
    renda_mensal = st.number_input("Renda mensal (R$)", min_value=0.0, value=4500.0, step=100.0)
    valor_solicitado = st.number_input("Valor do empréstimo (R$)", min_value=0.0, value=10000.0, step=500.0)
    prazo_meses = st.slider("Prazo (meses)", min_value=3, max_value=72, value=12, step=1)
    idade = st.slider("Idade", min_value=18, max_value=80, value=32)
    possui_default = st.toggle("Cliente possui histórico de default?", value=False)

    simular = st.button("Simular crédito", type="primary", use_container_width=True)

with col2:
    st.subheader("Como o app funciona")
    st.markdown(
        """
        1. O usuário informa renda, valor, prazo e perfil básico.  
        2. O sistema calcula a parcela estimada.  
        3. O sistema mede o comprometimento da renda.  
        4. O risco é classificado com regras fixas.  
        5. O agente explica o resultado em linguagem natural.  
        """
    )

if simular:
    if renda_mensal <= 0 or valor_solicitado <= 0 or prazo_meses <= 0:
        st.error("Preencha renda, valor solicitado e prazo com valores válidos.")
    else:
        monthly_rate = taxa_mensal / 100
        parcela = pmt(monthly_rate, prazo_meses, valor_solicitado)
        comprometimento = parcela / renda_mensal if renda_mensal else 0
        risco, mensagem_base = classify_risk(comprometimento, possui_default, rules)

        resposta = gerar_resposta_agente(
            renda_mensal=renda_mensal,
            valor_solicitado=valor_solicitado,
            prazo_meses=prazo_meses,
            parcela=parcela,
            comprometimento=comprometimento,
            risco=risco,
            possui_default=possui_default,
            mensagem_base=mensagem_base,
        )

        contexto = montar_contexto(
            renda_mensal=renda_mensal,
            valor_solicitado=valor_solicitado,
            prazo_meses=prazo_meses,
            taxa_mensal=taxa_mensal,
            parcela=parcela,
            comprometimento=comprometimento,
            risco=risco,
            possui_default=possui_default,
            idade=idade,
        )

        st.divider()
        k1, k2, k3 = st.columns(3)
        k1.metric("Parcela estimada", format_brl(parcela))
        k2.metric("Comprometimento da renda", f"{comprometimento:.1%}")
        k3.metric("Classificação de risco", risco)

        st.subheader("Resposta do agente")
        st.success(resposta)

        profile_stats = infer_profile_stats(base_df, renda_mensal, idade)
        if profile_stats:
            st.subheader("Comparativo com a base histórica")
            c1, c2, c3 = st.columns(3)
            c1.metric("Clientes comparáveis", profile_stats["qtd_clientes"])
            c2.metric("Renda média do grupo", format_brl(profile_stats["renda_media"]))
            if "taxa_default" in profile_stats:
                c3.metric("Taxa média de default do grupo", f"{profile_stats['taxa_default']:.1%}")
            else:
                c3.metric("Idade média do grupo", f"{profile_stats['idade_media']:.1f} anos")

        if mostrar_contexto:
            st.subheader("Contexto montado para o agente")
            st.code(contexto, language="text")

if mostrar_bases:
    st.divider()
    st.subheader("Prévia das bases carregadas")

    tabs = st.tabs(["Base consolidada", "Clientes", "Empréstimos", "Histórico"])

    with tabs[0]:
        st.dataframe(base_df.head(20), use_container_width=True)
    with tabs[1]:
        st.dataframe(clientes_df.head(20), use_container_width=True)
    with tabs[2]:
        st.dataframe(emprestimos_df.head(20), use_container_width=True)
    with tabs[3]:
        st.dataframe(historico_df.head(20), use_container_width=True)

st.divider()
with st.expander("Notas técnicas do projeto"):
    st.markdown(
        """
        - A decisão de risco é baseada em regras fixas, não no modelo de linguagem.
        - O agente apenas interpreta os resultados e gera uma explicação em linguagem natural.
        - Isso reduz alucinação e aumenta a transparência da solução.
        - Caso queira, você pode conectar uma API de LLM depois, mantendo a mesma estrutura de contexto.
        """
    )
