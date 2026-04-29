from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

css_anchor = "        .yv-card {{ background:rgba(255,255,255,.68);"
css_insert = "        .yv-session-list {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(280px,1fr)); gap:20px; margin-top:26px; }}\n        .yv-session-link {{ display:block; text-decoration:none !important; color:inherit !important; }}\n        .yv-session-card {{ min-height:260px; position:relative; overflow:hidden; background:rgba(255,255,255,.72); border:1px solid rgba(14,42,71,.12); border-radius:30px; padding:28px; box-shadow:0 18px 50px rgba(14,42,71,.08); transition:transform .35s ease, box-shadow .35s ease; }}\n        .yv-session-card:hover {{ transform:translateY(-4px); box-shadow:0 24px 70px rgba(14,42,71,.16); }}\n        .yv-session-cover {{ position:absolute; inset:0; background-size:cover; background-position:center; opacity:.22; transform:scale(1.05); }}\n        .yv-session-content {{ position:relative; z-index:2; }}\n        .yv-session-title {{ font-family:Georgia, serif; color:{BRAND_BLUE}; font-size:34px; line-height:1.02; margin:10px 0 10px; }}\n        .yv-session-meta {{ color:rgba(71,55,46,.68); font-size:15px; line-height:1.5; }}\n        .yv-session-featured {{ border:1px solid rgba(198,169,106,.55); box-shadow:0 24px 76px rgba(198,169,106,.18); }}\n        .yv-card {{ background:rgba(255,255,255,.68);"
if ".yv-session-list" not in s:
    s = s.replace(css_anchor, css_insert)

landing_code = '''def session_cell(row: Dict[str, Any], col: str, default: str = "") -> str:
    value = row.get(col, default)
    if pd.isna(value):
        return default
    return str(value).strip()


def view_session_landing() -> None:
    sessions = get_sessions()
    logo_path = find_logo_path()

    col1, col2 = st.columns([1, 8])
    with col1:
        if logo_path:
            st.image(logo_path, width=82)
        else:
            st.markdown('<div class="yv-logo-mark">Y</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<h1 class="yv-title">YVORA Music</h1>', unsafe_allow_html=True)
        st.markdown('<div class="yv-subtitle">Escolha a experiência disponível para iniciar sua jornada.</div>', unsafe_allow_html=True)

    if sessions.empty or "session_id" not in sessions.columns:
        st.markdown('<div class="yv-card"><div class="yv-h2">Experiências em preparação</div><div class="yv-muted">As próximas sessões aparecerão aqui.</div></div>', unsafe_allow_html=True)
        return

    df = sessions.copy()
    if "status" in df.columns:
        df = df[df["status"].astype(str).str.lower().str.strip().isin(["ativo", "live", "publicado", "1", "true", "sim"])]
    if "ordem_exibicao" in df.columns:
        df["_ordem"] = pd.to_numeric(df["ordem_exibicao"], errors="coerce").fillna(9999)
        df = df.sort_values("_ordem")

    if df.empty:
        st.markdown('<div class="yv-card"><div class="yv-h2">Experiências em preparação</div><div class="yv-muted">As próximas sessões aparecerão aqui.</div></div>', unsafe_allow_html=True)
        return

    cards = []
    for _, r in df.iterrows():
        row = r.to_dict()
        sid = session_cell(row, "session_id")
        nome = session_cell(row, "nome", sid)
        descricao = session_cell(row, "descricao", "Uma experiência YVORA entre música, cozinha e narrativa.")
        imagem = session_cell(row, "imagem_capa")
        tema = session_cell(row, "tema_musical")
        destaque = session_cell(row, "destaque") in ["1", "true", "True", "sim", "yes"]
        cover = f'<div class="yv-session-cover" style="background-image:url({imagem});"></div>' if imagem else ''
        featured = ' yv-session-featured' if destaque else ''
        tema_html = f'<span class="yv-pill">{tema}</span>' if tema else '<span class="yv-pill">Experiência</span>'
        card = f'<a class="yv-session-link" href="?view=cliente&sid={sid}"><div class="yv-session-card{featured}">{cover}<div class="yv-session-content"><div class="yv-kicker">Experiência disponível</div><div class="yv-session-title">{nome}</div><div class="yv-session-meta">{descricao}</div><br>{tema_html}<span class="yv-pill">Iniciar</span></div></div></a>'
        cards.append(card)

    st.markdown('<div class="yv-session-list">' + ''.join(cards) + '</div>', unsafe_allow_html=True)


'''

start = s.find("def session_cell(row: Dict[str, Any]")
if start != -1:
    end = s.find("def view_cliente(session_id: str) -> None:", start)
    if end != -1:
        s = s[:start] + landing_code + s[end:]
elif "def view_session_landing" in s:
    start = s.find("def view_session_landing() -> None:")
    end = s.find("def view_cliente(session_id: str) -> None:", start)
    if start != -1 and end != -1:
        s = s[:start] + landing_code + s[end:]
else:
    s = s.replace("def view_cliente(session_id: str) -> None:", landing_code + "def view_cliente(session_id: str) -> None:")

s = s.replace('requested_view = str(params.get("view", "cliente")).lower().strip()', 'requested_view = str(params.get("view", "")).lower().strip()')
s = s.replace('view = requested_view if requested_view in VIEW_OPTIONS else "cliente"', 'view = requested_view if requested_view in VIEW_OPTIONS else ""')
s = s.replace('show_sidebar = requested_admin or view in INTERNAL_VIEWS', 'show_sidebar = bool(view) and (requested_admin or view in INTERNAL_VIEWS)')
s = s.replace('hide_sidebar_for_css = initial_view_for_css == "cliente" and not admin_for_css', 'hide_sidebar_for_css = (initial_view_for_css in ["", "cliente"]) and not admin_for_css')

old = '''render_header(view, sid)
views = {"cliente": view_cliente, "banda": view_banda, "cozinha": view_cozinha, "operacao": view_operacao}
views[view](sid)'''
new = '''if not view:
    view_session_landing()
else:
    render_header(view, sid)
    views = {"cliente": view_cliente, "banda": view_banda, "cozinha": view_cozinha, "operacao": view_operacao}
    views[view](sid)'''
s = s.replace(old, new)

broken = '''
if not view:
    view_session_landing()
else:
    render_header(view, sid)

views = {"cliente": view_cliente, "banda": view_banda, "cozinha": view_cozinha, "operacao": view_operacao}
views[view](sid)'''
s = s.replace(broken, "\n" + new)

p.write_text(s, encoding='utf-8')
