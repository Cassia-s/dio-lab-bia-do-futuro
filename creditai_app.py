import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="CreditAI Chat", page_icon="💬", layout="wide")

# =========================================================
# Configurações
# =========================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "agente_credito_base"
BASE_PATH = DATA_DIR / "base_modelagem_agente.csv"
RULES_PATH = DATA_DIR / "regras_credito.json"
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3"

DEFAULT_RULES = {
    "thresholds": {
        "baixo_max": 0.20,
        "medio_max": 0.30
    },
    "mensagens": {
        "baixo": "O comprometimento da renda está em um patamar saudável.",
        "medio": "O comprometimento da renda exige atenção antes da contratação.",
        "alto": "O comprometimento da renda está elevado e aumenta o risco financeiro."
    }
}

FIELD_LABELS = {
    "idade": "idade",
    "renda": "renda mensal",
    "valor": "valor do empréstimo",
    "prazo": "prazo em meses",
    "historico": "histórico de inadimplência"
}

# =========================================================
# Carregamento de dados
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


# =========================================================
# Funções utilitárias
# =========================================================
def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")



def pmt(monthly_rate: float, n_periods: int, principal: float) -> float:
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

    if possui_default:
        if risco == "Baixo":
            risco = "Médio"
        elif risco == "Médio":
            risco = "Alto"

    mensagem = rules.get("mensagens", {}).get(risco.lower(), "")
    return risco, mensagem



def recommendation_text(risco: str, parcela: float, renda: float) -> str:
    if risco == "Baixo":
        return (
            "A operação está em uma faixa mais confortável. Mesmo assim, vale manter uma reserva "
            "financeira e evitar assumir novas dívidas no curto prazo."
        )
    if risco == "Médio":
        return (
            "A operação exige atenção. Uma alternativa é alongar o prazo ou reduzir o valor solicitado "
            "para deixar a parcela mais leve no orçamento."
        )
    reducao_ideal = max(parcela - (renda * 0.30), 0)
valor_ajuste = format_brl(reducao_ideal)
return (
    "O risco está elevado. Para melhorar a simulação, considere reduzir o valor solicitado, aumentar "
    f"o prazo ou buscar uma parcela cerca de {valor_ajuste} menor para voltar a uma faixa mais segura."
)
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
# Prompt e integração com Ollama
# =========================================================
def build_system_prompt() -> str:
    return """
Você é o CreditAI, um agente financeiro inteligente especializado em simulação e análise de crédito.

Seu objetivo é explicar o resultado de uma simulação de crédito com base em valores já calculados pelo sistema.

REGRAS:
1. Utilize exclusivamente os dados fornecidos no contexto.
2. Nunca invente valores, taxas ou informações financeiras.
3. Você não recalcula nada. Os cálculos já foram feitos pelo sistema.
4. Seu papel é interpretar o resultado e explicar de forma clara, acessível e profissional.
5. Sempre explique o motivo da classificação de risco.
6. Sempre ofereça uma recomendação prática.
7. Nunca peça para o usuário informar o risco. O risco já vem pronto no contexto.
8. Se a pergunta estiver fora do escopo de crédito, informe sua limitação e redirecione.
9. Não forneça dados sigilosos, senhas ou informações de terceiros.

FORMATO DA RESPOSTA:
- Resumo da situação
- Interpretação do risco
- Explicação
- Recomendação
""".strip()



def call_ollama(system_prompt: str, context: str, model: str) -> str:
    prompt = f"""
{system_prompt}

CONTEXTO DA ANÁLISE:
{context}

Gere a resposta final do agente seguindo exatamente o formato pedido.
""".strip()

    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


# =========================================================
# Fluxo de conversa
# =========================================================
def init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Olá! Eu sou o CreditAI. Vou te ajudar a simular um crédito. "
                    "Me informe sua idade para começarmos."
                ),
            }
        ]
    if "step" not in st.session_state:
        st.session_state.step = "idade"
    if "dados_cliente" not in st.session_state:
        st.session_state.dados_cliente = {
            "idade": None,
            "renda": None,
            "valor": None,
            "prazo": None,
            "historico": None,
        }
    if "analise" not in st.session_state:
        st.session_state.analise = None



def reset_chat() -> None:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Conversa reiniciada. Me informe sua idade para começarmos uma nova simulação.",
        }
    ]
    st.session_state.step = "idade"
    st.session_state.dados_cliente = {
        "idade": None,
        "renda": None,
        "valor": None,
        "prazo": None,
        "historico": None,
    }
    st.session_state.analise = None



def parse_step_input(step: str, text: str) -> Tuple[bool, Any, str]:
    cleaned = text.strip().lower().replace("r$", "").replace(".", "").replace(",", ".")

    try:
        if step == "idade":
            value = int(cleaned)
            if value < 18 or value > 100:
                return False, None, "Informe uma idade válida entre 18 e 100 anos."
            return True, value, ""

        if step == "renda":
            value = float(cleaned)
            if value <= 0:
                return False, None, "Informe uma renda mensal maior que zero."
            return True, value, ""

        if step == "valor":
            value = float(cleaned)
            if value <= 0:
                return False, None, "Informe um valor de empréstimo maior que zero."
            return True, value, ""

        if step == "prazo":
            value = int(cleaned)
            if value < 3 or value > 120:
                return False, None, "Informe um prazo válido entre 3 e 120 meses."
            return True, value, ""

        if step == "historico":
            if cleaned in {"sim", "s", "teve", "inadimplente"}:
                return True, True, ""
            if cleaned in {"nao", "não", "n", "nunca"}:
                return True, False, ""
            return False, None, "Responda apenas com 'sim' ou 'não'."

    except ValueError:
        return False, None, f"Não consegui entender sua {FIELD_LABELS[step]}. Tente novamente."

    return False, None, "Entrada inválida."



def next_step(current_step: str) -> Optional[str]:
    flow = ["idade", "renda", "valor", "prazo", "historico"]
    idx = flow.index(current_step)
    return flow[idx + 1] if idx + 1 < len(flow) else None



def prompt_for_step(step: str) -> str:
    prompts = {
        "idade": "Me informe sua idade.",
        "renda": "Agora me informe sua renda mensal em reais.",
        "valor": "Qual o valor do empréstimo que você deseja simular?",
        "prazo": "Em quantos meses você quer pagar esse empréstimo?",
        "historico": "Você já teve inadimplência ou default antes? Responda com sim ou não.",
    }
    return prompts.get(step, "Pode me informar o próximo dado?")



def build_context(dados: Dict[str, Any], taxa_mensal: float, rules: Dict[str, Any]) -> Dict[str, Any]:
    renda = float(dados["renda"])
    valor = float(dados["valor"])
    prazo = int(dados["prazo"])
    idade = int(dados["idade"])
    historico = bool(dados["historico"])

    monthly_rate = taxa_mensal / 100
    parcela = pmt(monthly_rate, prazo, valor)
    comprometimento = parcela / renda if renda else 0
    risco, mensagem_base = classify_risk(comprometimento, historico, rules)

    contexto = f"""
Dados do Cliente:
- Idade: {idade} anos
- Renda mensal: {format_brl(renda)}
- Valor solicitado: {format_brl(valor)}
- Prazo: {prazo} meses
- Taxa mensal: {taxa_mensal:.2f}%
- Histórico de inadimplência/default: {'Sim' if historico else 'Não'}

Resultados Calculados:
- Valor da parcela: {format_brl(parcela)}
- Comprometimento da renda: {comprometimento:.1%}
- Classificação de risco: {risco}
- Explicação base: {mensagem_base}
- Recomendação base: {recommendation_text(risco, parcela, renda)}
""".strip()

    return {
        "contexto": contexto,
        "parcela": parcela,
        "comprometimento": comprometimento,
        "risco": risco,
        "idade": idade,
        "renda": renda,
    }


# =========================================================
# Interface principal
# =========================================================
rules = load_rules()
base_df = load_base()
init_session()

with st.sidebar:
    st.header("Configurações")
    taxa_mensal = st.slider("Taxa de juros mensal (%)", 0.0, 8.0, 2.5, 0.1)
    model_name = st.text_input("Modelo no Ollama", value=DEFAULT_MODEL)
    mostrar_contexto = st.checkbox("Mostrar contexto da análise", value=True)
    mostrar_base = st.checkbox("Mostrar visão rápida da base", value=False)

    st.divider()
    st.caption("Use este app com o Ollama rodando localmente em http://localhost:11434")
    if st.button("Reiniciar conversa", use_container_width=True):
        reset_chat()
        st.rerun()

st.title("💬 CreditAI - Chat de Simulação de Crédito")
st.caption("Conversa guiada com cálculo automático de parcela, classificação de risco e resposta via Ollama.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Digite sua resposta aqui...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    current_step = st.session_state.step
    valid, parsed_value, error_msg = parse_step_input(current_step, user_input)

    if not valid:
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        st.rerun()

    st.session_state.dados_cliente[current_step] = parsed_value
    upcoming_step = next_step(current_step)

    if upcoming_step is not None:
        st.session_state.step = upcoming_step
        st.session_state.messages.append({"role": "assistant", "content": prompt_for_step(upcoming_step)})
        st.rerun()

    try:
        analise = build_context(st.session_state.dados_cliente, taxa_mensal, rules)
        st.session_state.analise = analise
        resposta = call_ollama(build_system_prompt(), analise["contexto"], model_name)
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        st.session_state.step = "finalizado"
        st.rerun()
    except requests.exceptions.ConnectionError:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Não consegui conectar ao Ollama. Verifique se ele está aberto e rodando localmente. "
                    "Exemplo: `ollama run llama3`."
                ),
            }
        )
        st.rerun()
    except requests.exceptions.HTTPError as exc:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"O Ollama respondeu com erro HTTP: {exc}. Confira o nome do modelo informado na barra lateral.",
            }
        )
        st.rerun()
    except Exception as exc:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"Ocorreu um erro inesperado durante a análise: {exc}",
            }
        )
        st.rerun()

if st.session_state.analise:
    st.divider()
    st.subheader("Resumo técnico da simulação")
    k1, k2, k3 = st.columns(3)
    k1.metric("Parcela estimada", format_brl(st.session_state.analise["parcela"]))
    k2.metric("Comprometimento da renda", f"{st.session_state.analise['comprometimento']:.1%}")
    k3.metric("Classificação de risco", st.session_state.analise["risco"])

    stats = infer_profile_stats(base_df, st.session_state.analise["renda"], st.session_state.analise["idade"])
    if stats:
        st.subheader("Comparativo com a base histórica")
        c1, c2, c3 = st.columns(3)
        c1.metric("Clientes comparáveis", stats["qtd_clientes"])
        c2.metric("Renda média do grupo", format_brl(stats["renda_media"]))
        if "taxa_default" in stats:
            c3.metric("Taxa média de default do grupo", f"{stats['taxa_default']:.1%}")
        else:
            c3.metric("Idade média do grupo", f"{stats['idade_media']:.1f} anos")

    if mostrar_contexto:
        st.subheader("Contexto enviado ao modelo")
        st.code(st.session_state.analise["contexto"], language="text")

if mostrar_base:
    st.divider()
    st.subheader("Prévia da base consolidada")
    if not base_df.empty:
        st.dataframe(base_df.head(30), use_container_width=True)
    else:
        st.info("A base consolidada não foi encontrada na pasta agente_credito_base.")

with st.expander("Notas técnicas"):
    st.markdown(
        """
        - O usuário informa apenas dados simples no chat.
        - O sistema calcula parcela, comprometimento e risco antes de enviar o contexto ao modelo.
        - O Ollama recebe apenas o contexto calculado e responde como explicador da análise.
        - Isso mantém a lógica financeira controlada e reduz alucinação.
        """
    )
