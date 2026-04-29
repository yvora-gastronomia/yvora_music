from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# ADD SESSION LANDING STRUCTURE
if "view_session_landing" not in s:
    insert_point = "def view_cliente(session_id: str) -> None:"

    landing_code = '''

def view_session_landing() -> None:
    sessions = get_sessions()
    logo_path = find_logo_path()

    col1, col2 = st.columns([1, 8])
    with col1:
        if logo_path:
            st.image(logo_path, width=80)
    with col2:
        st.markdown('<h1 class="yv-title">YVORA Music</h1>', unsafe_allow_html=True)
        st.markdown('<div class="yv-subtitle">Escolha sua experiência</div>', unsafe_allow_html=True)

    if sessions.empty or "session_id" not in sessions.columns:
        st.warning("Nenhuma sessão disponível")
        return

    for _, row in sessions.iterrows():
        sid = str(row.get("session_id", ""))
        nome = str(row.get("nome", sid))
        descricao = str(row.get("descricao", "Experiência YVORA"))

        st.markdown(f"""
        <div class="yv-card">
            <div class="yv-h2">{nome}</div>
            <div class="yv-muted">{descricao}</div>
            <br>
            <a href="?view=cliente&sid={sid}">
                <button style="background:#0E2A47;color:white;padding:10px 20px;border-radius:20px;border:none;">Iniciar experiência</button>
            </a>
        </div>
        """, unsafe_allow_html=True)

'''

    s = s.replace(insert_point, landing_code + insert_point)

# CHANGE DEFAULT BEHAVIOR (NO AUTO CLIENT)
s = s.replace('requested_view = str(params.get("view", "cliente")).lower().strip()',
              'requested_view = str(params.get("view", "")).lower().strip()')

# ROUTING
old_block = 'render_header(view, sid)'
new_block = '''
if not view:
    view_session_landing()
else:
    render_header(view, sid)
'''
s = s.replace(old_block, new_block)

p.write_text(s, encoding='utf-8')
