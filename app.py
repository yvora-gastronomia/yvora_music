import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

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
LOGO_PATHS = ["assets/logo.png", "assets/yvora_logo.png", "yvora_logo.JPG", "yvora_logo.jpg", "yvora_logo.png"]
VIEW_OPTIONS = ["cliente", "banda", "cozinha", "operacao"]

st.set_page_config(page_title=APP_TITLE, layout="wide")


def find_logo_path() -> Optional[str]:
    for path in LOGO_PATHS:
        if os.path.exists(path):
            return path
    return None


def parse_time_value(value: Any) -> Optional[datetime]:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    today = datetime.now().date()
    for fmt in ["%H:%M", "%H:%M:%S"]:
        try:
            t = datetime.strptime(text, fmt).time()
            return datetime.combine(today, t)
        except Exception:
            pass
    try:
        dt = pd.to_datetime(text, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.to_pydatetime().replace(year=today.year, month=today.month, day=today.day)
    except Exception:
        return None


def progress_for_row(row: Dict[str, Any]) -> Tuple[int, str, str]:
    start = parse_time_value(row.get("hora_inicio"))
    end = parse_time_value(row.get("hora_fim"))
    now = datetime.now()
    if not start or not end or end <= start:
        return 0, "Tempo não definido", ""
    total = max((end - start).total_seconds(), 1)
    elapsed = (now - start).total_seconds()
    pct = int(max(0, min(100, (elapsed / total) * 100)))
    remaining = int(max(0, (end - now).total_seconds()))
    mm = remaining // 60
    ss = remaining % 60
    label = "Ainda não iniciou" if elapsed < 0 else ("Etapa concluída" if pct >= 100 else f"{mm:02d}:{ss:02d} restantes")
    detail = f"{start.strftime('%H:%M')} até {end.strftime('%H:%M')}"
    return pct, label, detail


def inject_css() -> None:
    st.markdown(f"""
        <style>
        html, body, [data-testid="stAppViewContainer"] {{ background: radial-gradient(circle at 12% 8%, rgba(198,169,106,0.20), transparent 30%), radial-gradient(circle at 92% 18%, rgba(14,42,71,0.10), transparent 34%), linear-gradient(135deg, {BRAND_BG_SOFT} 0%, {BRAND_BG} 100%) !important; color: {BRAND_TEXT}; }}
        [data-testid="stHeader"] {{ display:none !important; }}
        .block-container {{ padding-top: 1.2rem; max-width: 1240px; }}
        .yv-logo-mark {{ width:54px; height:54px; border-radius:50%; display:flex; align-items:center; justify-content:center; background:{BRAND_BLUE}; color:{BRAND_BG_SOFT}; font-family:Georgia, serif; font-size:22px; letter-spacing:1px; }}
        .yv-title {{ margin:0; color:{BRAND_BLUE}; font-family:Georgia, 'Times New Roman', serif; font-size:clamp(24px, 4vw, 42px); line-height:1.0; letter-spacing:.3px; }}
        .yv-subtitle {{ margin-top:6px; color:rgba(14,42,71,.68); font-size:14px; }}
        .yv-pill {{ display:inline-flex; align-items:center; justify-content:center; padding:7px 13px; border-radius:999px; background:rgba(14,42,71,.08); color:{BRAND_BLUE}; font-size:12px; font-weight:700; border:1px solid rgba(14,42,71,.08); margin:2px; }}
        .yv-cinema {{ position:relative; min-height: 560px; border-radius:36px; overflow:hidden; background:linear-gradient(135deg, #061626, {BRAND_BLUE}); box-shadow:0 30px 80px rgba(14,42,71,.28); margin-bottom:18px; isolation:isolate; }}
        .yv-cinema:before {{ content:""; position:absolute; inset:0; background:linear-gradient(90deg, rgba(6,22,38,.96) 0%, rgba(6,22,38,.78) 38%, rgba(6,22,38,.18) 100%); z-index:1; }}
        .yv-cinema-bg {{ position:absolute; inset:0; background-size:cover; background-position:center; transform:scale(1.06); filter:saturate(.92) contrast(1.02); opacity:.62; animation: slowZoom 18s ease-in-out infinite alternate; }}
        .yv-cinema-content {{ position:relative; z-index:2; padding:clamp(26px, 6vw, 68px); max-width:800px; }}
        .yv-orb {{ position:absolute; width:360px; height:360px; right:-120px; top:-120px; border-radius:50%; background:radial-gradient(circle, rgba(198,169,106,.30), transparent 66%); z-index:2; animation: floatOrb 8s ease-in-out infinite alternate; }}
        .yv-card {{ background:rgba(255,255,255,.68); border:1px solid rgba(14,42,71,.12); border-radius:28px; padding:clamp(18px, 3vw, 32px); box-shadow:0 18px 50px rgba(14,42,71,.08); margin-bottom:18px; overflow:hidden; }}
        .yv-card-dark {{ background:linear-gradient(135deg, {BRAND_BLUE}, #16385B); color:{BRAND_BG_SOFT}; border-radius:30px; padding:clamp(22px, 4vw, 40px); box-shadow:0 24px 60px rgba(14,42,71,.22); margin-bottom:18px; }}
        .yv-kicker {{ color:{BRAND_GOLD}; font-size:12px; letter-spacing:2.2px; text-transform:uppercase; font-weight:800; }}
        .yv-h1 {{ font-family:Georgia, serif; font-size:clamp(38px, 7vw, 86px); line-height:.94; margin:10px 0 16px; letter-spacing:-1.8px; }}
        .yv-h2 {{ font-family:Georgia, serif; color:{BRAND_BLUE}; font-size:clamp(22px, 3vw, 34px); margin:0 0 10px; }}
        .yv-muted {{ color:rgba(71,55,46,.68); font-size:14px; }}
        .yv-white-muted {{ color:rgba(250,246,239,.74); font-size:15px; line-height:1.55; }}
        .yv-story {{ font-size:clamp(18px, 2vw, 23px); line-height:1.62; color:rgba(250,246,239,.92); max-width:760px; }}
        .yv-reveal {{ animation: revealUp .9s cubic-bezier(.2,.8,.2,1) both; }}
        .yv-delay-1 {{ animation-delay:.12s; }} .yv-delay-2 {{ animation-delay:.24s; }} .yv-delay-3 {{ animation-delay:.36s; }}
        .yv-grid {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; margin-top:16px; }}
        .yv-mini {{ background:rgba(255,255,255,.58); border:1px solid rgba(14,42,71,.1); border-radius:22px; padding:18px; box-shadow:0 12px 28px rgba(14,42,71,.05); }}
        .yv-mini b {{ color:{BRAND_BLUE}; }}
        .yv-now {{ border-left:5px solid {BRAND_GOLD}; }}
        .yv-progress-wrap {{ margin:22px 0 8px; }}
        .yv-progress-meta {{ display:flex; justify-content:space-between; gap:10px; color:rgba(250,246,239,.82); font-size:13px; margin-bottom:8px; }}
        .yv-progress-bg {{ width:100%; height:13px; border-radius:999px; background:rgba(250,246,239,.16); overflow:hidden; border:1px solid rgba(250,246,239,.16); }}
        .yv-progress-fill {{ height:100%; border-radius:999px; background:linear-gradient(90deg, {BRAND_GOLD}, #E6D1A0); box-shadow:0 0 18px rgba(198,169,106,.45); transition:width .7s ease; }}
        .yv-progress-light .yv-progress-meta {{ color:rgba(71,55,46,.7); }} .yv-progress-light .yv-progress-bg {{ background:rgba(14,42,71,.08); border-color:rgba(14,42,71,.08); }}
        .yv-play-card {{ background:rgba(255,255,255,.52); border:1px solid rgba(14,42,71,.1); border-radius:22px; padding:16px; margin-top:12px; }}
        .yv-chapter-strip {{ display:flex; gap:8px; margin:18px 0; overflow:auto; padding-bottom:4px; }} .yv-dot {{ min-width:56px; height:6px; border-radius:999px; background:rgba(14,42,71,.16); }} .yv-dot-on {{ background:linear-gradient(90deg, {BRAND_GOLD}, #E6D1A0); box-shadow:0 0 12px rgba(198,169,106,.45); }}
        .stButton > button {{ border-radius:999px !important; background:{BRAND_BLUE} !important; color:{BRAND_BG_SOFT} !important; border:1px solid rgba(14,42,71,.2) !important; min-height:2.7rem !important; font-weight:700 !important; }}
        @keyframes revealUp {{ from {{ opacity:0; transform:translateY(22px); filter:blur(8px); }} to {{ opacity:1; transform:translateY(0); filter:blur(0); }} }} @keyframes slowZoom {{ from {{ transform:scale(1.04); }} to {{ transform:scale(1.14); }} }} @keyframes floatOrb {{ from {{ transform:translateY(0); opacity:.7; }} to {{ transform:translateY(28px); opacity:1; }} }}
        @media(max-width:760px) {{ .yv-grid {{ grid-template-columns:1fr; }} .yv-cinema {{ min-height:620px; }} .yv-cinema:before {{ background:linear-gradient(180deg, rgba(6,22,38,.94), rgba(6,22,38,.72)); }} }}
        </style>
        """, unsafe_allow_html=True)


def progress_html(row: Dict[str, Any], light: bool = False) -> str:
    pct, label, detail = progress_for_row(row)
    extra = " yv-progress-light" if light else ""
    return f'<div class="yv-progress-wrap{extra}"><div class="yv-progress-meta"><span>{label}</span><span>{pct}% · {detail}</span></div><div class="yv-progress-bg"><div class="yv-progress-fill" style="width:{pct}%;"></div></div></div>'


def render_header(view: str, session_id: str) -> None:
    logo_path = find_logo_path()
    if view == "cliente":
        left = st.columns([1, 10])
    else:
        left = st.columns([1, 10, 3])
    with left[0]:
        if logo_path:
            st.image(logo_path, width=82)
        else:
            st.markdown('<div class="yv-logo-mark">Y</div>', unsafe_allow_html=True)
    with left[1]:
        title_map = {"cliente": "YVORA Music", "banda": "YVORA Music | Banda", "cozinha": "YVORA Music | Cozinha", "operacao": "YVORA Music | Operação"}
        subtitle_map = {"cliente": "Uma coreografia entre cozinha, salão, música e narrativa.", "banda": "Setlist e ritmo do jantar em tempo real.", "cozinha": "Prato atual, próximo prato e ritmo de serviço.", "operacao": "Controle do jantar, tempo e sequência da experiência."}
        st.markdown(f'<h1 class="yv-title">{title_map.get(view, "YVORA Music")}</h1><div class="yv-subtitle">{subtitle_map.get(view, "")}</div>', unsafe_allow_html=True)
    if view != "cliente":
        with left[2]:
            st.markdown(f'<span class="yv-pill">{view.upper()}</span><span class="yv-pill">{session_id}</span>', unsafe_allow_html=True)


@st.cache_resource(ttl=300)
def get_sheet():
    google_block = st.secrets.get("google", {})
    sheet_id = google_block.get("sheet_id")
    if not sheet_id:
        st.stop()
    if google_block.get("service_account_json"):
        sa = json.loads(google_block["service_account_json"])
    elif "gcp_service_account" in st.secrets:
        sa = dict(st.secrets["gcp_service_account"])
    else:
        st.stop()
    if "\\n" in sa.get("private_key", "") and "\n" not in sa.get("private_key", ""):
        sa["private_key"] = sa["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(sa, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open_by_key(sheet_id)


@st.cache_data(ttl=3)
def read_df(tab: str) -> pd.DataFrame:
    try:
        ws = get_sheet().worksheet(tab)
        return pd.DataFrame(ws.get_all_records())
    except Exception:
        return pd.DataFrame()


def get_sessions() -> pd.DataFrame:
    df = read_df("sessions")
    return df if not df.empty else pd.DataFrame()


def get_timeline(session_id: str) -> pd.DataFrame:
    df = read_df("timeline")
    if df.empty or "session_id" not in df.columns:
        return pd.DataFrame()
    df["session_id"] = df["session_id"].astype(str).str.strip()
    df = df[df["session_id"] == str(session_id).strip()].copy()
    if "ativo" in df.columns:
        df = df[df["ativo"].astype(str).str.strip().isin(["1", "", "True", "true"])]
    if df.empty:
        return df
    df["ordem"] = pd.to_numeric(df.get("ordem", 0), errors="coerce").fillna(0).astype(int)
    return df.sort_values("ordem").reset_index(drop=True)


def get_live(session_id: str) -> int:
    df = read_df("live")
    if df.empty or "session_id" not in df.columns:
        return 1
    row = df[df["session_id"].astype(str).str.strip() == str(session_id).strip()]
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
    idx_session = header.index("session_id") if "session_id" in header else 0
    found_row = None
    for i, row in enumerate(values[1:], start=2):
        if len(row) > idx_session and str(row[idx_session]).strip() == str(session_id).strip():
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


def media_url(row: Dict[str, Any]) -> str:
    return safe(row, "background_url") or safe(row, "imagem_prato") or safe(row, "gif_momento")


def chapter_strip(df: pd.DataFrame, ordem: int) -> str:
    dots = []
    for _, r in df.iterrows():
        cls = "yv-dot yv-dot-on" if int(r["ordem"]) <= ordem else "yv-dot"
        dots.append(f'<div class="{cls}"></div>')
    return '<div class="yv-chapter-strip">' + ''.join(dots) + '</div>'


def playback_block(row: Dict[str, Any]) -> str:
    modo = safe(row, "modo_musica", "banda") or "banda"
    spotify = safe(row, "spotify_url")
    label = "Banda ao vivo" if modo.lower() != "spotify" else "Playlist Spotify"
    link = f'<br><a href="{spotify}" target="_blank">Abrir playlist ou faixa</a>' if spotify else ""
    return f'<div class="yv-play-card"><b>Modo musical:</b> {label}{link}</div>'


def public_unavailable() -> None:
    st.markdown('<div class="yv-card"><div class="yv-h2">Experiência em preparação</div><div class="yv-muted">Em instantes, a próxima etapa da experiência aparecerá aqui.</div></div>', unsafe_allow_html=True)


def internal_unavailable(session_id: str) -> None:
    sessions = get_sessions()
    available = [] if sessions.empty or "session_id" not in sessions.columns else sessions["session_id"].astype(str).tolist()
    st.warning(f"Timeline não encontrada para a sessão: {session_id}")
    if available:
        st.write("Sessões encontradas:", ", ".join(available))


def view_cliente(session_id: str) -> None:
    df = get_timeline(session_id)
    ordem = get_live(session_id)
    row = current_row(df, ordem)
    if not row:
        public_unavailable()
        return
    bg = media_url(row)
    bg_style = f"background-image:url('{bg}');" if bg else "background-image:radial-gradient(circle at 70% 30%, rgba(198,169,106,.26), transparent 36%);"
    st.markdown(f"""<section class="yv-cinema"><div class="yv-cinema-bg" style="{bg_style}"></div><div class="yv-orb"></div><div class="yv-cinema-content"><div class="yv-kicker yv-reveal">Capítulo {safe(row, 'ordem')} · {safe(row, 'etapa')}</div><div class="yv-h1 yv-reveal yv-delay-1">{safe(row, 'prato', 'Momento YVORA')}</div><div class="yv-white-muted yv-reveal yv-delay-1">{safe(row, 'hora_inicio')} às {safe(row, 'hora_fim')}</div>{progress_html(row)}{chapter_strip(df, ordem)}<div class="yv-kicker yv-reveal yv-delay-2">Agora tocando</div><div class="yv-story yv-reveal yv-delay-2"><b>{safe(row, 'musica', 'Música ao vivo')}</b> {('· ' + safe(row, 'artista')) if safe(row, 'artista') else ''}</div><br><div class="yv-story yv-reveal yv-delay-3">{safe(row, 'conexao_experiencia', 'A conexão entre prato e música aparece aqui.')}</div></div></section>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="yv-grid"><div class="yv-mini yv-reveal"><b>Prato</b><br><span class="yv-muted">{safe(row, 'historia_prato')}</span></div><div class="yv-mini yv-reveal yv-delay-1"><b>Música</b><br><span class="yv-muted">{safe(row, 'historia_musica')}</span></div><div class="yv-mini yv-reveal yv-delay-2"><b>Experiência</b><br><span class="yv-muted">Carnes, queijos, tempo e atmosfera em uma mesma narrativa.</span></div></div>""", unsafe_allow_html=True)


def view_banda(session_id: str) -> None:
    df = get_timeline(session_id)
    ordem = get_live(session_id)
    if df.empty:
        internal_unavailable(session_id)
        return
    st.markdown('<div class="yv-card"><div class="yv-h2">Setlist e ritmo do jantar</div></div>', unsafe_allow_html=True)
    for _, r in df.iterrows():
        cls = "yv-card yv-now" if int(r["ordem"]) == ordem else "yv-card"
        st.markdown(f"""<div class="{cls}"><span class="yv-pill">{safe(r, 'hora_inicio')} · {safe(r, 'hora_fim')}</span><span class="yv-pill">{safe(r, 'etapa')}</span><span class="yv-pill">{safe(r, 'modo_musica', 'banda')}</span><h3 style="color:{BRAND_BLUE}; margin:14px 0 4px;">{safe(r, 'musica', 'Música ao vivo')}</h3><div class="yv-muted">{safe(r, 'artista')} · {safe(r, 'duracao_musica')}</div>{progress_html(r, light=True) if int(r['ordem']) == ordem else ''}<p>{safe(r, 'observacao_banda')}</p>{playback_block(r)}</div>""", unsafe_allow_html=True)


def view_cozinha(session_id: str) -> None:
    df = get_timeline(session_id)
    ordem = get_live(session_id)
    row = current_row(df, ordem)
    if not row:
        internal_unavailable(session_id)
        return
    nxt = df[df["ordem"] > ordem].head(1)
    st.markdown(f"""<div class="yv-card-dark"><div class="yv-kicker">Cozinha · agora</div><div class="yv-h1">{safe(row, 'prato')}</div><div class="yv-story">{safe(row, 'qtd_convidados')} convidados · status: <b>{safe(row, 'status_cozinha')}</b></div>{progress_html(row)}<br><div class="yv-white-muted">{safe(row, 'observacao_cozinha')}</div></div>""", unsafe_allow_html=True)
    if not nxt.empty:
        p = nxt.iloc[0].to_dict()
        st.markdown(f"""<div class="yv-card"><div class="yv-kicker">Próximo prato</div><div class="yv-h2">{safe(p, 'prato')}</div><div class="yv-muted">{safe(p, 'hora_inicio')} · {safe(p, 'status_cozinha')}</div><p>{safe(p, 'observacao_cozinha')}</p></div>""", unsafe_allow_html=True)


def view_operacao(session_id: str) -> None:
    df = get_timeline(session_id)
    ordem = get_live(session_id)
    row = current_row(df, ordem)
    if df.empty or not row:
        internal_unavailable(session_id)
        return
    min_ordem = int(df["ordem"].min())
    max_ordem = int(df["ordem"].max())
    st.markdown(f"""<div class="yv-card-dark"><div class="yv-kicker">Controle operacional</div><div class="yv-h1">{safe(row, 'etapa')}</div><div class="yv-story">Atual: {safe(row, 'prato')} · {safe(row, 'musica')}</div>{progress_html(row)}{playback_block(row)}</div>""", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Voltar", use_container_width=True):
        update_live(session_id, max(min_ordem, ordem - 1))
    if c2.button("Avançar", use_container_width=True):
        update_live(session_id, min(max_ordem, ordem + 1))
    selected = c3.selectbox("Ir para", df["ordem"].tolist(), index=max(0, df["ordem"].tolist().index(ordem)))
    if c4.button("Ativar etapa", use_container_width=True):
        update_live(session_id, int(selected))
    show_cols = ["ordem", "hora_inicio", "hora_fim", "etapa", "prato", "qtd_convidados", "status_cozinha", "status_salao", "modo_musica", "musica", "artista", "spotify_url", "observacao_operacao"]
    st.dataframe(df[[c for c in show_cols if c in df.columns]], use_container_width=True, hide_index=True)


def get_active_view_and_session() -> Tuple[str, str]:
    params = st.query_params
    requested_view = str(params.get("view", "cliente")).lower().strip()
    requested_sid = str(params.get("sid", "")).strip()
    sessions_df = get_sessions()
    available_sessions = [] if sessions_df.empty or "session_id" not in sessions_df.columns else sessions_df["session_id"].astype(str).str.strip().tolist()
    sid = requested_sid or (available_sessions[0] if available_sessions else "jantar-teste")
    view = requested_view if requested_view in VIEW_OPTIONS else "cliente"

    with st.sidebar:
        st.markdown("### Visões YVORA")
        selected_view = st.radio("Escolha a visão", VIEW_OPTIONS, index=VIEW_OPTIONS.index(view), key="selected_view", horizontal=False)
        if available_sessions:
            selected_sid = st.selectbox("Sessão", available_sessions, index=available_sessions.index(sid) if sid in available_sessions else 0, key="selected_sid")
        else:
            selected_sid = st.text_input("Sessão", value=sid, key="selected_sid_text")
        st.caption("Use Cliente para QR público. Use Banda, Cozinha e Operação para controle interno.")
        if selected_view != view or selected_sid != sid:
            st.query_params["view"] = selected_view
            st.query_params["sid"] = selected_sid
            st.rerun()
        view = selected_view
        sid = selected_sid

    return view, sid


inject_css()
view, sid = get_active_view_and_session()
render_header(view, sid)
views = {"cliente": view_cliente, "banda": view_banda, "cozinha": view_cozinha, "operacao": view_operacao}
views[view](sid)

time.sleep(AUTO_REFRESH_SECONDS)
st.rerun()
