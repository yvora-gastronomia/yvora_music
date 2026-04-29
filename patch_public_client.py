from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '[data-testid="stHeader"] {{ display:none !important; }}',
    '[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="collapsedControl"], [data-testid="stStatusWidget"], #MainMenu, header, footer, .stDeployButton, .viewerBadge_container__1QSob, .viewerBadge_link__1S137, .viewerBadge {{ display:none !important; visibility:hidden !important; height:0 !important; }}'
)

old = """<div class=\"yv-kicker yv-reveal\">Capítulo {safe(row, 'ordem')} · {safe(row, 'etapa')}</div><div class=\"yv-h1 yv-reveal yv-delay-1\">{safe(row, 'prato', 'Momento YVORA')}</div><div class=\"yv-white-muted yv-reveal yv-delay-1\">{safe(row, 'hora_inicio')} às {safe(row, 'hora_fim')}</div>{progress_html(row)}{chapter_strip(df, ordem)}"""
new = """<div class=\"yv-kicker yv-reveal\">Momento YVORA</div><div class=\"yv-h1 yv-reveal yv-delay-1\">{safe(row, 'prato', 'Momento YVORA')}</div>"""
s = s.replace(old, new)

s = s.replace(
    'Carnes, queijos, tempo e atmosfera em uma mesma narrativa.',
    'A etapa atual é revelada no ritmo da noite.'
)

p.write_text(s, encoding='utf-8')
