import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# =========================
# BRANDING YVORA
# =========================
BG = "#EFE7DD"
BLUE = "#0E2A47"
GOLD = "#C6A96A"

st.set_page_config(layout="wide")

st.markdown(f"""
<style>
body {{
    background-color: {BG};
}}
.card {{
    background: white;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 12px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
}}
.title {{
    color: {BLUE};
    font-size: 26px;
    font-weight: bold;
}}
.sub {{
    color: #555;
}}
.badge {{
    background: {BLUE};
    color: white;
    padding: 5px 12px;
    border-radius: 20px;
}}
</style>
""", unsafe_allow_html=True)

# =========================
# GOOGLE SHEETS
# =========================
def get_sheet():
    sa = json.loads(st.secrets["google"]["service_account_json"])
    creds = Credentials.from_service_account_info(sa, scopes=[
        "https://www.googleapis.com/auth/spreadsheets"
    ])
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["google"]["sheet_id"])

def read_df(tab):
    sh = get_sheet().worksheet(tab)
    data = sh.get_all_records()
    return pd.DataFrame(data)

# =========================
# CORE
# =========================
def get_timeline(session_id):
    df = read_df("timeline")
    return df[df["session_id"] == session_id].sort_values("ordem")

def get_live(session_id):
    df = read_df("live")
    row = df[df["session_id"] == session_id]
    if row.empty:
        return 0
    return int(row.iloc[0]["ordem_atual"])

# =========================
# CLIENT VIEW
# =========================
def view_cliente(session_id):
    df = get_timeline(session_id)
    idx = get_live(session_id)

    row = df[df["ordem"] == idx].iloc[0]

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="title">{row["prato"]}</div>', unsafe_allow_html=True)

    if row["imagem_prato"]:
        st.image(row["imagem_prato"])

    if row["gif_momento"]:
        st.image(row["gif_momento"])

    st.write(row["conexao_experiencia"])
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# BANDA
# =========================
def view_banda(session_id):
    df = get_timeline(session_id)

    st.markdown("### 🎵 Setlist")

    for _, r in df.iterrows():
        st.markdown(f"""
        <div class="card">
        <b>{r['musica']}</b> - {r['artista']}<br>
        <span class="sub">{r['etapa']}</span>
        </div>
        """, unsafe_allow_html=True)

# =========================
# COZINHA
# =========================
def view_cozinha(session_id):
    df = get_timeline(session_id)
    idx = get_live(session_id)

    atual = df[df["ordem"] == idx].iloc[0]

    st.markdown("### 👨‍🍳 Cozinha")

    st.markdown(f"""
    <div class="card">
    <b>Agora:</b> {atual["prato"]}<br>
    Status: {atual["status_cozinha"]}
    </div>
    """, unsafe_allow_html=True)

    prox = df[df["ordem"] == idx + 1]
    if not prox.empty:
        p = prox.iloc[0]
        st.markdown(f"""
        <div class="card">
        <b>Próximo:</b> {p["prato"]}
        </div>
        """, unsafe_allow_html=True)

# =========================
# OPERAÇÃO
# =========================
def view_operacao(session_id):
    df = get_timeline(session_id)
    idx = get_live(session_id)

    st.markdown("### 🎛 Controle")

    col1, col2 = st.columns(2)

    if col1.button("◀ Voltar"):
        update_live(session_id, idx - 1)

    if col2.button("Avançar ▶"):
        update_live(session_id, idx + 1)

    st.dataframe(df)

def update_live(session_id, new_idx):
    sh = get_sheet().worksheet("live")
    sh.update("B2", new_idx)
    st.rerun()

# =========================
# MAIN
# =========================
params = st.query_params
view = params.get("view", "cliente")
sid = params.get("sid", "")

st.title("YVORA Music Experience")

if not sid:
    st.warning("Informe session_id na URL")
else:
    if view == "cliente":
        view_cliente(sid)
    elif view == "banda":
        view_banda(sid)
    elif view == "cozinha":
        view_cozinha(sid)
    elif view == "operacao":
        view_operacao(sid)
