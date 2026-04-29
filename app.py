import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

APP_TITLE = "YVORA Music Experience"
BRAND_BG = "#EFE7DD"
BRAND_BG_SOFT = "#FAF6EF"
BRAND_BLUE = "#0E2A47"
BRAND_GOLD = "#C6A96A"
BRAND_TEXT = "#47372E"
AUTO_REFRESH_SECONDS = 5

st.set_page_config(page_title=APP_TITLE, layout="wide")


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        html, body, [data-testid="stAppViewContainer"] {{
            background:
                radial-gradient(circle at top left, rgba(198,169,106,0.18), transparent 32%),
                linear-gradient(135deg, {BRAND_BG_SOFT} 0%, {BRAND_BG} 100%) !important;
            color: {BRAND_TEXT};
        }}
        [data-testid="stHeader"] {{ background: transparent !important; }}
        .block-container {{ padding-top: 1.6rem; max-width: 1180px; }}
        .yv-shell {{ animation: fadeIn .55s ease-in-out; }}
        .yv-header {{
            display: flex; align-items: center; justify-content: space-between; gap: 18px;
            margin-bottom: 18px; padding: 14px 18px;
            border: 1px solid rgba(14,42,71,0.12); border-radius: 26px;
            background: rgba(255,255,255,0.48); backdrop-filter: blur(8px);
            box-shadow: 0 18px 45px rgba(14,42,71,0.07);
        }}
        .yv-brand {{ display:flex; align-items:center; gap:14px; }}
        .yv-logo-mark {{
            width: 54px; height: 54px; border-radius: 50%; display:flex; align-items:center; justify-content:center;
            background: {BRAND_BLUE}; color: {BRAND_BG_SOFT}; font-family: Georgia, serif; font-size: 22px; letter-spacing: 1px;
        }}
        .yv-title {{ margin:0; color:{BRAND_BLUE}; font-family: Georgia, 'Times New Roman', serif; font-size: clamp(24px, 4vw, 42px); line-height:1.0; letter-spacing:.3px; }}
        .yv-subtitle {{ margin-top:6px; color: rgba(14,42,71,.68); font-size: 14px; }}
        .yv-pill {{ display:inline-flex; align-items:center; justify-content:center; padding: 7px 13px; border-radius: 999px; background: rgba(14,42,71,.08); color:{BRAND_BLUE}; font-size:12px; font-weight:700; border: 1px solid rgba(14,42,71,.08); margin:2px; }}
        .yv-card {{ background: rgba(255,255,255,.68); border: 1px solid rgba(14,42,71,.12); border-radius: 28px; padding: clamp(18px, 3vw, 32px); box-shadow: 0 18px 50px rgba(14,42,71,.08); margin-bottom: 18px; overflow:hidden; }}
        .yv-card-dark {{ background: linear-gradient(135deg, {BRAND_BLUE}, #16385B); color: {BRAND_BG_SOFT}; border-radius: 30px; padding: clamp(22px, 4vw, 40px); box-shadow: 0 24px 60px rgba(14,42,71,.22); margin-bottom: 18px; }}
        .yv-kicker {{ color:{BRAND_GOLD}; font-size:12px; letter-spacing:1.9px; text-transform:uppercase; font-weight:800; }}
        .yv-h1 {{ font-family: Georgia, serif; font-size: clamp(30px, 6vw, 64px); line-height: .98; margin: 8px 0 12px; }}
        .yv-h2 {{ font-family: Georgia, serif; color:{BRAND_BLUE}; font-size: clamp(22px, 3vw, 34px); margin: 0 0 10px; }}
        .yv-muted {{ color: rgba(71,55,46,.68); font-size:14px; }}
        .yv-white-muted {{ color: rgba(250,246,239,.74); font-size:15px; line-height:1.55; }}
        .yv-story {{ font-size: 18px; line-height:1.65; color: rgba(250,246,239,.92); max-width: 760px; }}
        .yv-grid {{ display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 12px; margin-top:16px; }}
        .yv-mini {{ background: rgba(255,255,255,.58); border: 1px solid rgba(14,42,71,.1); border-radius: 20px; padding: 14px; }}
        .yv-mini b {{ color:{BRAND_BLUE}; }}
        .yv-now {{ border-left: 5px solid {BRAND_GOLD}; }}
        .yv-img img {{ border-radius: 24px; }}
        .stButton > button {{ border-radius: 999px !important; background: {BRAND_BLUE} !important; color: {BRAND_BG_SOFT} !important; border: 1px solid rgba(14,42,71,.2) !important; min-height: 2.7rem !important; font-weight: 700 !important; }}
        .stButton > button:hover {{ filter: brightness(1.08); }}
        @keyframes fadeIn {{ from {{ opacity:0; transform: translateY(10px); }} to {{ opacity:1; transform: translateY(0); }} }}
        @media(max-width: 760px) {{ .yv-header {{ align-items:flex-start; flex-direction:column; }} .yv-grid {{ grid-template-columns:1fr; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(view: str, session_id: str) -> None:
    logo_html = '<div class="yv-logo-mark">Y</div>'
    st.markdown('<div class="yv-shell">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="yv-header">
            <div class="yv-brand">
                {logo_html}
                <div>
                    <h1 class="yv-title">YVORA Music</h1>
                    <div class="yv-subtitle">Linha do tempo sensorial entre cozinha, salão, música e narrativa.</div>
                </div>
            </div>
            <div>
                <span class="yv-pill">{view.upper()}</span>
                <span class="yv-pill">{session_id}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=110)


@st.cache_resource(ttl=300)
def get_sheet():
    google_block = st.secrets.get("google", {})
    sheet_id = google_block.get("sheet_id")
    if not sheet_id:
        st.error("Falta configurar [google].sheet_id nos Secrets do Streamlit.")
        st.stop()

    if google_block.get("service_account_json"):
        sa = json.loads(google_block["service_account_json"])
    elif "gcp_service_account" in st.secrets:
        sa = dict(st.secrets["gcp_service_account"])
    else:
        st.error("Falta configurar [google].service_account_json ou [gcp_service_account] nos Secrets.")
        st.stop()

    if "\\n" in sa.get("private_key", "") and "\n" not in sa.get("private_key", ""):
        sa["private_key"] = sa["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(
        sa,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
    )
    return gspread.authorize(creds).open_by_key(sheet_id)


@st.cache_data(ttl=3)
def read_df(tab: str) -> pd.DataFrame:
    try:
        ws = get_sheet().worksheet(tab)
        return pd.DataFrame(ws.get_all_records())
    except Exception:
        return pd.DataFrame()


def get_timeline(session_id: str) -> pd.DataFrame:
    df = read_df("timeline")
    if df.empty or "session_id" not in df.columns:
        return pd.DataFrame()
    df = df[df["session_id"].astype(str) == str(session_id)].copy()
    if df.empty:
        return df
    df["ordem"] = pd.to_numeric(df.get("ordem", 0), errors="coerce").fillna(0).astype(int)
    return df.sort_values("ordem").reset_index(drop=True)


def get_live(session_id: str) -> int:
    df = read_df("live")
    if df.empty or "session_id" not in df.columns:
        return 1
    row = df[df["session_id"].astype(str) == str(session_id)]
    if row.empty:
        return 1
    return int(pd.to_numeric(row.iloc[0].get("ordem_atual", 1), errors="coerce") or 1)


def update_live(session_id: str, new_ordem: int) -> None:
    ws = get_sheet().worksheet("live")
    values = ws.get_all_values()
    if not values:
        ws.append_row(["session_id", "ordem_atual", "updated_at"])
        values = [["session_id", "ordem_atual", "updated_at"]]
    header = values[0]
    if "session_id" not in header:
        ws.clear()
        ws.append_row(["session_id", "ordem_atual", "updated_at"])
        ws.append_row([session_id, new_ordem, datetime.now().isoformat(timespec="seconds")])
        read_df.clear()
        st.rerun()
    idx_session = header.index("session_id")
    found_row = None
    for i, row in enumerate(values[1:], start=2):
        if len(row) > idx_session and str(row[idx_session]) == str(session_id):
            found_row = i
            break
    out = [session_id, int(new_ordem), datetime.now().isoformat(timespec="seconds")]
    if found_row:
        ws.update(f"A{found_row}:C{found_row}", [out])
    else:
        ws.append_row(out)
    read_df.clear()
    st.rerun()


def safe(row: Dict[str, Any], col: str, default: str = "") -> str:
    value = row.get(col, default)
    if pd.isna(value):
        return default
    return str(value)


def current_row(df: pd.DataFrame, ordem: int) -> Optional[Dict[str, Any]]:
    if df.empty:
        return None
    match = df[df["ordem"] == ordem]
    if match.empty:
        return df.iloc[0].to_dict()
    return match.iloc[0].to_dict()


def media_block(row: Dict[str, Any]) -> None:
    img = safe(row, "imagem_prato")
    gif = safe(row, "gif_momento")
    if img:
        st.markdown('<div class="yv-img">', unsafe_allow_html=True)
        st.image(img, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    if gif:
        st.markdown('<div class="yv-img">', unsafe_allow_html=True)
        st.image(gif, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


def view_cliente(session_id: str) -> None:
    df = get_timeline(session_id)
    ordem = get_live(session_id)
    row = current_row(df, ordem)
    if not row:
        st.warning("Timeline não encontrada para esta sessão.")
        return

    left, right = st.columns([1.08, 0.92])
    with left:
        st.markdown(
            f"""
            <div class="yv-card-dark">
                <div class="yv-kicker">Agora à mesa</div>
                <div class="yv-h1">{safe(row, 'prato', 'Momento YVORA')}</div>
                <div class="yv-white-muted">{safe(row, 'etapa')} · {safe(row, 'hora_inicio')} às {safe(row, 'hora_fim')}</div>
                <br>
                <div class="yv-kicker">Agora tocando</div>
                <div class="yv-story"><b>{safe(row, 'musica', 'Música ao vivo')}</b> {('· ' + safe(row, 'artista')) if safe(row, 'artista') else ''}</div>
                <br>
                <div class="yv-story">{safe(row, 'conexao_experiencia', 'A conexão entre prato e música aparece aqui.')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        media_block(row)

    st.markdown(
        f"""
        <div class="yv-grid">
            <div class="yv-mini"><b>Prato</b><br><span class="yv-muted">{safe(row, 'historia_prato')}</span></div>
            <div class="yv-mini"><b>Música</b><br><span class="yv-muted">{safe(row, 'historia_musica')}</span></div>
            <div class="yv-mini"><b>Experiência</b><br><span class="yv-muted">Carnes, queijos, tempo e atmosfera em uma mesma narrativa.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def view_banda(session_id: str) -> None:
    df = get_timeline(session_id)
    ordem = get_live(session_id)
    if df.empty:
        st.warning("Timeline não encontrada.")
        return
    st.markdown('<div class="yv-card"><div class="yv-h2">Setlist e ritmo do jantar</div></div>', unsafe_allow_html=True)
    for _, r in df.iterrows():
        cls = "yv-card yv-now" if int(r["ordem"]) == ordem else "yv-card"
        st.markdown(
            f"""
            <div class="{cls}">
                <span class="yv-pill">{safe(r, 'hora_inicio')} · {safe(r, 'hora_fim')}</span>
                <span class="yv-pill">{safe(r, 'etapa')}</span>
                <h3 style="color:{BRAND_BLUE}; margin:14px 0 4px;">{safe(r, 'musica', 'Música ao vivo')}</h3>
                <div class="yv-muted">{safe(r, 'artista')} · {safe(r, 'duracao_musica')}</div>
                <p>{safe(r, 'observacao_banda')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def view_cozinha(session_id: str) -> None:
    df = get_timeline(session_id)
    ordem = get_live(session_id)
    row = current_row(df, ordem)
    if not row:
        st.warning("Timeline não encontrada.")
        return
    nxt = df[df["ordem"] > ordem].head(1)
    st.markdown(
        f"""
        <div class="yv-card-dark">
            <div class="yv-kicker">Cozinha · agora</div>
            <div class="yv-h1">{safe(row, 'prato')}</div>
            <div class="yv-story">{safe(row, 'qtd_convidados')} convidados · status: <b>{safe(row, 'status_cozinha')}</b></div>
            <br><div class="yv-white-muted">{safe(row, 'observacao_cozinha')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not nxt.empty:
        p = nxt.iloc[0].to_dict()
        st.markdown(
            f"""
            <div class="yv-card">
                <div class="yv-kicker">Próximo prato</div>
                <div class="yv-h2">{safe(p, 'prato')}</div>
                <div class="yv-muted">{safe(p, 'hora_inicio')} · {safe(p, 'status_cozinha')}</div>
                <p>{safe(p, 'observacao_cozinha')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def view_operacao(session_id: str) -> None:
    df = get_timeline(session_id)
    ordem = get_live(session_id)
    row = current_row(df, ordem)
    if df.empty or not row:
        st.warning("Timeline não encontrada.")
        return
    min_ordem = int(df["ordem"].min())
    max_ordem = int(df["ordem"].max())
    st.markdown(
        f"""
        <div class="yv-card-dark">
            <div class="yv-kicker">Controle operacional</div>
            <div class="yv-h1">{safe(row, 'etapa')}</div>
            <div class="yv-story">Atual: {safe(row, 'prato')} · {safe(row, 'musica')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Voltar", use_container_width=True):
        update_live(session_id, max(min_ordem, ordem - 1))
    if c2.button("Avançar", use_container_width=True):
        update_live(session_id, min(max_ordem, ordem + 1))
    selected = c3.selectbox("Ir para", df["ordem"].tolist(), index=max(0, df["ordem"].tolist().index(ordem)))
    if c4.button("Ativar etapa", use_container_width=True):
        update_live(session_id, int(selected))

    show_cols = ["ordem", "hora_inicio", "hora_fim", "etapa", "prato", "qtd_convidados", "status_cozinha", "status_salao", "musica", "artista", "observacao_operacao"]
    st.dataframe(df[[c for c in show_cols if c in df.columns]], use_container_width=True, hide_index=True)


inject_css()
params = st.query_params
view = str(params.get("view", "cliente")).lower()
sid = str(params.get("sid", "jantar-teste"))
render_header(view, sid)

views = {"cliente": view_cliente, "banda": view_banda, "cozinha": view_cozinha, "operacao": view_operacao}

if view not in views:
    st.warning("Visão inválida. Use view=cliente, view=banda, view=cozinha ou view=operacao.")
else:
    views[view](sid)

st.caption("Atualização automática a cada poucos segundos. Para imagens e GIFs, use links públicos nas colunas imagem_prato e gif_momento.")
time.sleep(AUTO_REFRESH_SECONDS)
st.rerun()
