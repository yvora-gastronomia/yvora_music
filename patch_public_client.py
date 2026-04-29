from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# Stronger Streamlit chrome hiding
s = s.replace(
    '[data-testid="stHeader"] {{ display:none !important; }}',
    '[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="collapsedControl"], [data-testid="stStatusWidget"], #MainMenu, header, footer, .stDeployButton, .viewerBadge_container__1QSob, .viewerBadge_link__1S137, .viewerBadge {{ display:none !important; visibility:hidden !important; height:0 !important; }}'
)

# Add transition CSS once
needle_css = """        .yv-reveal {{ animation: revealUp .9s cubic-bezier(.2,.8,.2,1) both; }}"""
insert_css = """        .yv-show-mode .yv-cinema {{ min-height: 74vh; animation: sceneBreath 10s ease-in-out infinite alternate; }}
        .yv-show-mode .yv-cinema-content {{ padding-top: clamp(42px, 9vw, 92px); }}
        .yv-show-mode .yv-h1 {{ font-size: clamp(46px, 8vw, 104px); }}
        .yv-show-mode .yv-story {{ font-size: clamp(20px, 2.3vw, 28px); }}
        .yv-service-pill {{ display:inline-flex; align-items:center; justify-content:center; padding:8px 14px; border-radius:999px; background:rgba(198,169,106,.18); color:{BRAND_GOLD}; border:1px solid rgba(198,169,106,.35); font-size:12px; font-weight:800; letter-spacing:1px; text-transform:uppercase; }}
        .yv-status-row {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:16px; }}
        .yv-status-card {{ background:rgba(255,255,255,.58); border:1px solid rgba(14,42,71,.1); border-radius:20px; padding:14px 16px; }}
        .yv-reveal {{ animation: revealUp .9s cubic-bezier(.2,.8,.2,1) both; }}"""
if insert_css not in s:
    s = s.replace(needle_css, insert_css)

s = s.replace(
    "@keyframes revealUp {{ from {{ opacity:0; transform:translateY(22px); filter:blur(8px); }} to {{ opacity:1; transform:translateY(0); filter:blur(0); }} }} @keyframes slowZoom",
    "@keyframes revealUp {{ from {{ opacity:0; transform:translateY(22px); filter:blur(8px); }} to {{ opacity:1; transform:translateY(0); filter:blur(0); }} }} @keyframes sceneBreath {{ from {{ transform:scale(1); }} to {{ transform:scale(1.012); }} }} @keyframes slowZoom"
)

# Keep client clean
old_client = """<div class=\"yv-kicker yv-reveal\">Capítulo {safe(row, 'ordem')} · {safe(row, 'etapa')}</div><div class=\"yv-h1 yv-reveal yv-delay-1\">{safe(row, 'prato', 'Momento YVORA')}</div><div class=\"yv-white-muted yv-reveal yv-delay-1\">{safe(row, 'hora_inicio')} às {safe(row, 'hora_fim')}</div>{progress_html(row)}{chapter_strip(df, ordem)}"""
new_client = """<div class=\"yv-kicker yv-reveal\">Momento YVORA</div><div class=\"yv-h1 yv-reveal yv-delay-1\">{safe(row, 'prato', 'Momento YVORA')}</div>"""
s = s.replace(old_client, new_client)
s = s.replace('Carnes, queijos, tempo e atmosfera em uma mesma narrativa.', 'A etapa atual é revelada no ritmo da noite.')

# Remove clock-based progress in manual views
s = s.replace("{progress_html(row)}{playback_block(row)}", "{playback_block(row)}")
s = s.replace("{progress_html(row)}<br><div class=\"yv-white-muted\">", "<br><div class=\"yv-white-muted\">")
s = s.replace("{progress_html(r, light=True) if int(r['ordem']) == ordem else ''}", "")
s = s.replace("Atual: {safe(row, 'prato')} · {safe(row, 'musica')}", "Etapa ativa {ordem} de {max_ordem}: {safe(row, 'prato')} · {safe(row, 'musica')}")

# Add service status helper
helper_anchor = """def media_url(row: Dict[str, Any]) -> str:
    return safe(row, \"background_url\") or safe(row, \"imagem_prato\") or safe(row, \"gif_momento\")
"""
helper_code = helper_anchor + """

def service_status(row: Dict[str, Any]) -> str:
    status = safe(row, \"status_servico\") or safe(row, \"status_salao\") or safe(row, \"status_cozinha\")
    return status.strip() or \"em andamento\"
"""
if "def service_status" not in s:
    s = s.replace(helper_anchor, helper_code)

# Show mode class for client cinema
s = s.replace('<section class="yv-cinema">', '<section class="yv-cinema yv-show-mode">', 1)

# Add service status in client hero if not present
client_marker = """<div class=\"yv-kicker yv-reveal\">Momento YVORA</div><div class=\"yv-h1 yv-reveal yv-delay-1\">{safe(row, 'prato', 'Momento YVORA')}</div>"""
client_marker_new = """<div class=\"yv-kicker yv-reveal\">Momento YVORA</div><div class=\"yv-h1 yv-reveal yv-delay-1\">{safe(row, 'prato', 'Momento YVORA')}</div><div class=\"yv-service-pill yv-reveal yv-delay-1\">{service_status(row)}</div>"""
s = s.replace(client_marker, client_marker_new)

# Add operation service status controls before dataframe
op_old = """    show_cols = [\"ordem\", \"hora_inicio\", \"hora_fim\", \"etapa\", \"prato\", \"qtd_convidados\", \"status_cozinha\", \"status_salao\", \"modo_musica\", \"musica\", \"artista\", \"spotify_url\", \"observacao_operacao\"]
    st.dataframe(df[[c for c in show_cols if c in df.columns]], use_container_width=True, hide_index=True)
"""
op_new = """    st.markdown('<div class=\"yv-card\"><div class=\"yv-h2\">Status de serviço</div><div class=\"yv-muted\">Use estes estados para coordenar cozinha, salão e música sem depender do relógio.</div></div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    if s1.button(\"Preparando\", use_container_width=True):
        update_step_status(session_id, ordem, \"preparando\")
    if s2.button(\"Pronto\", use_container_width=True):
        update_step_status(session_id, ordem, \"pronto\")
    if s3.button(\"Servido\", use_container_width=True):
        update_step_status(session_id, ordem, \"servido\")
    show_cols = [\"ordem\", \"hora_inicio\", \"hora_fim\", \"etapa\", \"prato\", \"qtd_convidados\", \"status_servico\", \"status_cozinha\", \"status_salao\", \"modo_musica\", \"musica\", \"artista\", \"spotify_url\", \"observacao_operacao\"]
    st.dataframe(df[[c for c in show_cols if c in df.columns]], use_container_width=True, hide_index=True)
"""
s = s.replace(op_old, op_new)

# Add update_step_status function before view_operacao
status_func_anchor = """def view_operacao(session_id: str) -> None:
"""
status_func = """def update_step_status(session_id: str, ordem: int, status: str) -> None:
    ws = get_sheet().worksheet(\"timeline\")
    values = ws.get_all_values()
    if not values:
        return
    headers = values[0]
    if \"session_id\" not in headers or \"ordem\" not in headers:
        return
    if \"status_servico\" not in headers:
        ws.update_cell(1, len(headers) + 1, \"status_servico\")
        headers.append(\"status_servico\")
    idx_session = headers.index(\"session_id\")
    idx_ordem = headers.index(\"ordem\")
    idx_status = headers.index(\"status_servico\")
    for i, row in enumerate(values[1:], start=2):
        sid_ok = len(row) > idx_session and str(row[idx_session]).strip() == str(session_id).strip()
        ordem_ok = len(row) > idx_ordem and str(row[idx_ordem]).strip() == str(ordem).strip()
        if sid_ok and ordem_ok:
            ws.update_cell(i, idx_status + 1, status)
            read_df.clear()
            st.rerun()


""" + status_func_anchor
if "def update_step_status" not in s:
    s = s.replace(status_func_anchor, status_func)

p.write_text(s, encoding='utf-8')
