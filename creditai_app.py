import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import streamlit as st

st.set_page_config(page_title="CreditAI", page_icon="💬", layout="wide")

# =========================================================
# Configuração visual
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #07111f 0%, #091427 100%);
        color: #f5f7fb;
    }
    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.2rem;
        max-width: 1400px;
    }
    [data-testid="stSidebar"] {
        background: #06101d;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    .brand-card, .sidebar-card, .result-card {
        background: rgba(17, 26, 43, 0.88);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.20);
    }
    .brand-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.1rem;
    }
    .brand-sub {
        color: #aab6d3;
        font-size: 0.96rem;
        margin-bottom: 0;
    }
    .client-avatar {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #7c4dff 0%, #9f67ff 100%);
        color: white;
        font-weight: 700;
        font-size: 1.1rem;
        margin-right: 12px;
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .muted {
        color: #9aa8c5;
        font-size: 0.93rem;
    }
    .good { color: #31d17c; font-weight: 700; }
    .warn { color: #f5c451; font-weight: 700; }
    .bad { color: #ff6961; font-weight: 700; }
    .metric-box {
        background: rgba(12, 20, 34, 0.85);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 14px;
    }
    .small-label {
        color: #97a5c3;
        font-size: 0.82rem;
        margin-bottom: 4px;
    }
    .small-value {
        font-size: 1.05rem;
        font-weight: 700;
        color: #f4f7fb;
    }
    .chat-hint {
        color: #95a3c0;
        margin-top: -4px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Caminhos e arquivos
# =========================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

DEFAULT_RULES = {
    "thresholds": {"baixo_max": 0.20, "medio_max": 0.30},
    "mensagens": {
        "baixo": "O comprometimento da renda está em um patamar saudável.",
        "medio": "O comprometimento da renda exige atenção antes da contratação.",
        "alto": "O comprometimento da renda está elevado e aumenta o risco financeiro.",
    },
}

FIELD_LABELS = {
    "nome": "nome completo",
    "valor": "valor do empréstimo",
    "prazo": "prazo em meses",
    "taxa": "taxa de juros mensal",
}

# =========================================================
# Leitura de arquivos
# =========================================================
@st.cache_data
def load_rules() -> Dict[str, Any]:
    path = DATA_DIR / "regras_credito.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_RULES


@st.cache_data
def load_clients_base() -> Tuple[pd.DataFrame, str]:
    possible_paths = [
        DATA_DIR / "amostra_perfil_sidebar.csv",
        DATA_DIR / "perfil_sidebar_clientes.csv",
    ]

    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    seps = [None, ";", ","]

    for path in possible_paths:
        if path.exists():
            errors = []

            for enc in encodings:
                for sep in seps:
                    try:
                        if sep is None:
                            df = pd.read_csv(
                                path,
                                encoding=enc,
                                sep=None,
                                engine="python",
                                on_bad_lines="skip",
                            )
                        else:
                            df = pd.read_csv(
                            path,
                            encoding="utf-8-sig",
                            sep=";",
                            engine="python",
                            on_bad_lines="skip",
                        )
                        
                        df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]

                        if df.empty:
                            errors.append(f"{enc} | sep={sep} -> vazio")
                            continue

                        if len(df.columns) == 1:
                            errors.append(f"{enc} | sep={sep} -> 1 coluna")
                            continue

                        return df, f"Base carregada: {path.name}"

                    except Exception as e:
                        errors.append(f"{enc} | sep={sep} -> {e}")

            return pd.DataFrame(), f"Erro ao ler {path.name}"

    return pd.DataFrame(), "Base de clientes não encontrada na pasta /data"

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


def recommendation_text(risco: str, renda: float) -> str:
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
    parcela_segura = renda * 0.30
    return (
        "O risco está elevado. Para melhorar a simulação, considere reduzir o valor solicitado ou aumentar "
        f"o prazo. Para uma faixa mais segura, a parcela ideal seria em torno de {format_brl(parcela_segura)}."
    )


def normalize(text: str) -> str:
    return " ".join(str(text).strip().lower().split())


def pick_col(df: pd.DataFrame, options: list[str]) -> Optional[str]:
    lower_map = {c.lower(): c for c in df.columns}
    for opt in options:
        if opt.lower() in lower_map:
            return lower_map[opt.lower()]
    for col in df.columns:
        c = col.lower()
        if any(opt.lower() in c for opt in options):
            return col
    return None


def infer_client_row(df: pd.DataFrame, full_name: str) -> Tuple[Optional[pd.Series], Optional[str]]:
    if df.empty:
        return None, "A base de clientes não foi encontrada."

    name_col = pick_col(df, ["nome_cliente", "nome", "full_name", "name"])
    if not name_col:
        return None, f"A base foi carregada, mas não encontrei coluna de nome. Colunas disponíveis: {list(df.columns)}"

    working = df.copy()
    working["__name_norm__"] = working[name_col].astype(str).map(normalize)
    target = normalize(full_name)

    exact = working[working["__name_norm__"] == target]
    if len(exact) >= 1:
        return exact.iloc[0], None

    contains = working[working["__name_norm__"].str.contains(target, na=False)]
    if len(contains) == 1:
        return contains.iloc[0], None
    if len(contains) > 1:
        sugestoes = ", ".join(contains[name_col].astype(str).head(5).tolist())
        return None, f"Encontrei mais de um nome parecido. Tente um destes: {sugestoes}"

    return None, "Não encontrei esse nome na base. Digite exatamente o nome cadastrado no histórico."


def get_value(row: pd.Series, options: list[str], default: Any = None) -> Any:
    for opt in options:
        for col in row.index:
            if opt.lower() == str(col).lower() or opt.lower() in str(col).lower():
                value = row[col]
                if pd.notna(value):
                    return value
    return default


def summarize_client(row: pd.Series) -> Dict[str, Any]:
    nome = str(get_value(row, ["nome_cliente", "nome", "name"], "Cliente"))
    primeiro_nome = str(get_value(row, ["primeiro_nome"], nome.split()[0] if nome else "Cliente"))
    iniciais = str(get_value(row, ["iniciais"], "".join([p[0] for p in nome.split()[:2]]).upper()))
    cliente_desde = str(get_value(row, ["cliente_desde"], "Mar/2023"))

    score = get_value(row, ["score_credito", "score", "credit_score"], 720)
    historico_pagamentos = str(get_value(row, ["historico_pagamentos", "payment_history"], "Pontual"))
    consultas = int(float(get_value(row, ["consultas_ultimo_ano", "consultas"], 2)))
    emprestimos_anteriores = int(float(get_value(row, ["emprestimos_anteriores", "previous_loans"], 1)))
    ultimo_emprestimo = str(get_value(row, ["ultimo_emprestimo", "status_ultimo_emprestimo"], "Pago em dia"))
    idade = int(float(get_value(row, ["idade", "age"], 32)))
    renda = float(get_value(row, ["renda_mensal", "renda", "income"], 5400))

    default_raw = str(get_value(row, ["possui_default", "inadimplencia", "default", "historico_default"], "não")).strip().lower()
    possui_default = default_raw in {"1", "true", "sim", "s", "yes"}

    return {
        "nome": nome,
        "primeiro_nome": primeiro_nome,
        "iniciais": iniciais,
        "cliente_desde": cliente_desde,
        "score_credito": int(float(score)),
        "historico_pagamentos": historico_pagamentos,
        "consultas_ultimo_ano": consultas,
        "emprestimos_anteriores": emprestimos_anteriores,
        "ultimo_emprestimo": ultimo_emprestimo,
        "idade": idade,
        "renda_mensal": renda,
        "possui_default": possui_default,
    }


def score_label(score: int) -> str:
    if score >= 700:
        return "Bom"
    if score >= 550:
        return "Moderado"
    return "Baixo"


def score_class(score: int) -> str:
    if score >= 700:
        return "good"
    if score >= 550:
        return "warn"
    return "bad"


def local_agent_response(context: Dict[str, Any]) -> str:
    nome = context["primeiro_nome"]
    risco_txt = context["risco"].lower()

    historico_extra = (
        f"Você possui histórico de pagamentos {context['historico_pagamentos'].lower()} e score de crédito {context['score_credito']}, "
        "o que ajuda na leitura do seu perfil."
        if context["score_credito"] >= 700 and not context["possui_default"]
        else "Seu histórico merece atenção adicional na análise de crédito."
    )

    return (
        f"Olá, {nome}! Analisei sua simulação. Para um crédito de {format_brl(context['valor'])} em {context['prazo']} meses, "
        f"com taxa de {context['taxa']:.2f}% ao mês, a parcela estimada fica em {format_brl(context['parcela'])}.\n\n"
        f"Isso representa {context['comprometimento']:.1%} da sua renda mensal, classificando a operação como risco {risco_txt}.\n\n"
        f"{context['mensagem_base']} {historico_extra}\n\n"
        f"Recomendação: {context['recomendacao']}"
    )


def build_context(cliente: Dict[str, Any], valor: float, prazo: int, taxa: float, rules: Dict[str, Any]) -> Dict[str, Any]:
    renda = float(cliente["renda_mensal"])
    monthly_rate = taxa / 100
    parcela = pmt(monthly_rate, prazo, valor)
    comprometimento = parcela / renda if renda else 0
    risco, mensagem_base = classify_risk(comprometimento, cliente["possui_default"], rules)
    recomendacao = recommendation_text(risco, renda)

    contexto_texto = f"""
Dados do Cliente:
- Nome: {cliente['nome']}
- Idade: {cliente['idade']} anos
- Renda mensal: {format_brl(renda)}
- Valor solicitado: {format_brl(valor)}
- Prazo: {prazo} meses
- Taxa mensal: {taxa:.2f}%
- Histórico de inadimplência/default: {'Sim' if cliente['possui_default'] else 'Não'}
- Score de crédito: {cliente['score_credito']}
- Histórico de pagamentos: {cliente['historico_pagamentos']}
- Empréstimos anteriores: {cliente['emprestimos_anteriores']}

Resultados Calculados:
- Valor da parcela: {format_brl(parcela)}
- Comprometimento da renda: {comprometimento:.1%}
- Classificação de risco: {risco}
- Explicação base: {mensagem_base}
- Recomendação base: {recomendacao}
""".strip()

    return {
        "nome": cliente["nome"],
        "primeiro_nome": cliente["primeiro_nome"],
        "idade": cliente["idade"],
        "renda": renda,
        "valor": valor,
        "prazo": prazo,
        "taxa": taxa,
        "parcela": parcela,
        "comprometimento": comprometimento,
        "risco": risco,
        "mensagem_base": mensagem_base,
        "recomendacao": recomendacao,
        "contexto_texto": contexto_texto,
        "score_credito": cliente["score_credito"],
        "historico_pagamentos": cliente["historico_pagamentos"],
        "consultas_ultimo_ano": cliente["consultas_ultimo_ano"],
        "emprestimos_anteriores": cliente["emprestimos_anteriores"],
        "ultimo_emprestimo": cliente["ultimo_emprestimo"],
        "possui_default": cliente["possui_default"],
    }

# =========================================================
# Sessão
# =========================================================
def init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Olá! Eu sou o CreditAI. Para começar, digite seu nome completo para eu localizar "
                    "seu histórico e personalizar a simulação."
                ),
            }
        ]
    if "step" not in st.session_state:
        st.session_state.step = "nome"
    if "cliente" not in st.session_state:
        st.session_state.cliente = None
    if "dados_simulacao" not in st.session_state:
        st.session_state.dados_simulacao = {"valor": None, "prazo": None, "taxa": None}
    if "analise" not in st.session_state:
        st.session_state.analise = None


def reset_chat() -> None:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Nova conversa iniciada. Digite seu nome completo para eu buscar seu histórico na base.",
        }
    ]
    st.session_state.step = "nome"
    st.session_state.cliente = None
    st.session_state.dados_simulacao = {"valor": None, "prazo": None, "taxa": None}
    st.session_state.analise = None


def parse_step_input(step: str, text: str) -> Tuple[bool, Any, str]:
    raw = text.strip()
    cleaned = raw.lower().replace("r$", "").replace(".", "").replace(",", ".")

    try:
        if step == "nome":
            if len(raw.split()) < 2:
                return False, None, "Digite seu nome completo para eu localizar seu histórico corretamente."
            return True, raw, ""

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

        if step == "taxa":
            value = float(cleaned)
            if value < 0 or value > 15:
                return False, None, "Informe uma taxa mensal válida entre 0 e 15."
            return True, value, ""

    except ValueError:
        return False, None, f"Não consegui entender {FIELD_LABELS[step]}. Tente novamente."

    return False, None, "Entrada inválida."


def next_step(step: str) -> Optional[str]:
    flow = ["nome", "valor", "prazo", "taxa"]
    idx = flow.index(step)
    return flow[idx + 1] if idx + 1 < len(flow) else None


def prompt_for_step(step: str, cliente: Optional[Dict[str, Any]] = None) -> str:
    primeiro_nome = cliente["primeiro_nome"] if cliente else ""
    prompts = {
        "valor": f"Perfeito, {primeiro_nome}. Encontrei seu histórico. Qual valor você deseja solicitar?",
        "prazo": f"Agora me diga o prazo que deseja para pagamento, {primeiro_nome} (em meses).",
        "taxa": f"Ótimo. Qual taxa de juros mensal você deseja simular, {primeiro_nome}? (Ex.: 2,5)",
    }
    return prompts.get(step, "Pode me informar o próximo dado?")

# =========================================================
# Sidebar
# =========================================================
def render_sidebar(cliente: Optional[Dict[str, Any]]) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class='brand-card'>
                <div class='brand-title'>CreditAI</div>
                <p class='brand-sub'>Seu Educador Financeiro</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")

        if cliente:
            st.markdown(
                f"""
                <div class='sidebar-card'>
                    <div style='display:flex; align-items:center;'>
                        <div class='client-avatar'>{cliente['iniciais']}</div>
                        <div>
                            <div style='font-size:1.15rem; font-weight:700; color:#f6f8fb;'>{cliente['nome']}</div>
                            <div class='muted'>Cliente desde {cliente['cliente_desde']}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")

            st.markdown(
                f"""
                <div class='sidebar-card'>
                    <div class='section-title'>Score de crédito</div>
                    <div class='{score_class(cliente['score_credito'])}' style='font-size:1.6rem; font-weight:700;'>
                        {score_label(cliente['score_credito'])}
                    </div>
                    <div class='muted' style='margin-top:4px;'>Pontuação: {cliente['score_credito']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")

            historico_class = "good" if cliente["historico_pagamentos"].strip().lower() == "pontual" else "warn"

            st.markdown(
                f"""
                <div class='sidebar-card'>
                    <div class='section-title'>Resumo do seu histórico</div>
                    <div class='muted'>Histórico de pagamentos</div>
                    <div class='{historico_class}' style='margin-bottom:14px;'>
                        {cliente['historico_pagamentos']}
                    </div>
                    <div class='muted'>Consultas no último ano</div>
                    <div style='margin-bottom:14px; color:#f4f7fb; font-weight:700;'>{cliente['consultas_ultimo_ano']}</div>
                    <div class='muted'>Empréstimos anteriores</div>
                    <div style='margin-bottom:14px; color:#f4f7fb; font-weight:700;'>{cliente['emprestimos_anteriores']}</div>
                    <div class='muted'>Último empréstimo</div>
                    <div class='good'>{cliente['ultimo_emprestimo']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class='sidebar-card'>
                    <div class='section-title'>Base histórica</div>
                    <div class='muted'>Digite seu nome completo no chat para eu localizar seu cadastro e carregar automaticamente seu histórico.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        if st.button("Nova conversa", use_container_width=True):
            reset_chat()
            st.rerun()

# =========================================================
# App principal
# =========================================================
rules = load_rules()
clients_df, base_status = load_clients_base()
init_session()
render_sidebar(st.session_state.cliente)

col_header, col_button = st.columns([6, 1])

with col_header:
    st.title("Converse com o CreditAI")
    st.markdown(
        "<div class='chat-hint'>Estou aqui para te ajudar a tomar decisões financeiras melhores.</div>",
        unsafe_allow_html=True,
    )
    st.caption(base_status)

with col_button:
    st.write("")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Digite sua mensagem...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    current_step = st.session_state.step
    valid, parsed_value, error_msg = parse_step_input(current_step, user_input)

    if not valid:
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        st.rerun()

    if current_step == "nome":
        row, err = infer_client_row(clients_df, parsed_value)
        if err:
            st.session_state.messages.append({"role": "assistant", "content": err})
            st.rerun()

        cliente = summarize_client(row)
        st.session_state.cliente = cliente
        st.session_state.step = "valor"
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    f"Olá, {cliente['primeiro_nome']}! 👋 Encontrei seu histórico. "
                    f"Vejo que sua renda mensal cadastrada é {format_brl(cliente['renda_mensal'])} e seu score atual é {cliente['score_credito']}.\n\n"
                    f"{prompt_for_step('valor', cliente)}"
                ),
            }
        )
        st.rerun()

    st.session_state.dados_simulacao[current_step] = parsed_value
    upcoming_step = next_step(current_step)

    if upcoming_step is not None:
        st.session_state.step = upcoming_step
        st.session_state.messages.append(
            {"role": "assistant", "content": prompt_for_step(upcoming_step, st.session_state.cliente)}
        )
        st.rerun()

    cliente = st.session_state.cliente
    dados = st.session_state.dados_simulacao

    analise = build_context(
        cliente=cliente,
        valor=float(dados["valor"]),
        prazo=int(dados["prazo"]),
        taxa=float(dados["taxa"]),
        rules=rules,
    )

    st.session_state.analise = analise
    st.session_state.step = "finalizado"

    resposta = local_agent_response({**analise, **cliente})
    st.session_state.messages.append({"role": "assistant", "content": resposta})
    st.rerun()

if st.session_state.analise and st.session_state.cliente:
    cliente = st.session_state.cliente
    analise = st.session_state.analise

    st.write("")
    st.markdown("### 📊 Resultado da Simulação")

    left, right = st.columns(2)

    with left:
        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        st.markdown("#### Dados do Cliente")

        items = [
            ("Nome", cliente["nome"]),
            ("Idade", f"{cliente['idade']} anos"),
            ("Renda mensal", format_brl(cliente["renda_mensal"])),
            ("Valor solicitado", format_brl(analise["valor"])),
            ("Prazo", f"{analise['prazo']} meses"),
            ("Taxa mensal", f"{analise['taxa']:.2f}%"),
            ("Histórico de inadimplência/default", "Sim" if cliente["possui_default"] else "Não"),
        ]

        for label, value in items:
            st.markdown(
                f"<div class='metric-box' style='margin-bottom:10px;'><div class='small-label'>{label}</div><div class='small-value'>{value}</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        st.markdown("#### Resultados Calculados")

        risco_class = "good" if analise["risco"] == "Baixo" else "warn" if analise["risco"] == "Médio" else "bad"

        results = [
            ("Valor da parcela", format_brl(analise["parcela"])),
            ("Comprometimento da renda", f"{analise['comprometimento']:.1%}"),
            ("Classificação de risco", analise["risco"], risco_class),
            ("Explicação base", analise["mensagem_base"]),
            ("Recomendação base", analise["recomendacao"]),
        ]

        for row in results:
            if len(row) == 3:
                label, value, klass = row
                value_html = f"<span class='{klass}'>{value}</span>"
            else:
                label, value = row
                value_html = value

            st.markdown(
                f"<div class='metric-box' style='margin-bottom:10px;'><div class='small-label'>{label}</div><div class='small-value'>{value_html}</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("### 📌 Considerando seu histórico")

    historico_texto = (
        f"Você possui histórico de pagamentos {cliente['historico_pagamentos'].lower()} e um score de crédito de {cliente['score_credito']}, "
        "o que fortalece a leitura do seu perfil. "
        if cliente["score_credito"] >= 700 and not cliente["possui_default"]
        else f"Seu histórico mostra score de crédito {cliente['score_credito']} e requer uma análise mais cuidadosa do comprometimento da renda. "
    )

    st.markdown(
        f"""
        <div class='result-card'>
            <div style='font-size:1.15rem; font-weight:700; margin-bottom:8px;'>Análise complementar</div>
            <div class='muted' style='font-size:1rem; line-height:1.7;'>
                {historico_texto}
                Hoje você tem {cliente['consultas_ultimo_ano']} consulta(s) no último ano e {cliente['emprestimos_anteriores']} empréstimo(s) anterior(es).<br><br>
                Com base na simulação atual, a principal atenção está no valor da parcela em relação à sua renda mensal.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Ver contexto técnico da análise"):
        st.code(analise["contexto_texto"], language="text")

st.caption("CreditAI pode cometer erros. Sempre confirme as informações antes de tomar decisões financeiras.")
