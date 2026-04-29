from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# REMOVE service status from client completely
s = s.replace("<div class=\"yv-service-pill yv-reveal yv-delay-1\">{service_status(row)}</div>", "")

# RESTORE CLIENT STORYTELLING WITHOUT OPERATIONAL SPOILERS
start = s.find("def view_cliente(session_id: str) -> None:")
end = s.find("\ndef view_banda(session_id: str) -> None:")

if start != -1 and end != -1:
    new_block = '''def view_cliente(session_id: str) -> None:\n    df = get_timeline(session_id)\n    ordem = get_live(session_id)\n    row = current_row(df, ordem)\n    if not row:\n        public_unavailable()\n        return\n\n    bg = media_url(row)\n    bg_style = f"background-image:url('{bg}');" if bg else "background-image:radial-gradient(circle at 70% 30%, rgba(198,169,106,.26), transparent 36%);"\n\n    st.markdown(f"""\n    <section class="yv-cinema yv-show-mode">\n        <div class="yv-cinema-bg" style="{bg_style}"></div>\n        <div class="yv-orb"></div>\n        <div class="yv-cinema-content">\n            <div class="yv-kicker yv-reveal">YVORA Music Experience</div>\n            <div class="yv-h1 yv-reveal yv-delay-1">{safe(row, 'prato', 'Experiência YVORA')}</div>\n            <div class="yv-kicker yv-reveal yv-delay-2">Agora tocando</div>\n            <div class="yv-story yv-reveal yv-delay-2">\n                <b>{safe(row, 'musica', 'Música ao vivo')}</b>\n                {('· ' + safe(row, 'artista')) if safe(row, 'artista') else ''}\n            </div>\n            <br>\n            <div class="yv-story yv-reveal yv-delay-3">\n                {safe(row, 'conexao_experiencia', 'A música e o prato se encontram em uma experiência construída para este momento.')}\n            </div>\n        </div>\n    </section>\n    """, unsafe_allow_html=True)\n\n    st.markdown(f"""\n    <div class="yv-grid">\n        <div class="yv-mini yv-reveal">\n            <b>Prato</b><br>\n            <span class="yv-muted">{safe(row, 'historia_prato')}</span>\n        </div>\n        <div class="yv-mini yv-reveal yv-delay-1">\n            <b>Música</b><br>\n            <span class="yv-muted">{safe(row, 'historia_musica')}</span>\n        </div>\n        <div class="yv-mini yv-reveal yv-delay-2">\n            <b>Harmonização</b><br>\n            <span class="yv-muted">{safe(row, 'conexao_experiencia')}</span>\n        </div>\n    </div>\n    """, unsafe_allow_html=True)\n\n'''
    s = s[:start] + new_block + s[end:]

# Ensure grid CSS remains active after previous safety replacement
s = s.replace("yv-grid-disabled", "yv-grid")

p.write_text(s, encoding='utf-8')
