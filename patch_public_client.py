from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '[data-testid="stHeader"] {{ display:none !important; }}',
    '[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="collapsedControl"], [data-testid="stStatusWidget"], #MainMenu, header, footer, .stDeployButton, .viewerBadge_container__1QSob, .viewerBadge_link__1S137, .viewerBadge {{ display:none !important; visibility:hidden !important; height:0 !important; }}'
)

old_client = """<div class=\"yv-kicker yv-reveal\">Capítulo {safe(row, 'ordem')} · {safe(row, 'etapa')}</div><div class=\"yv-h1 yv-reveal yv-delay-1\">{safe(row, 'prato', 'Momento YVORA')}</div><div class=\"yv-white-muted yv-reveal yv-delay-1\">{safe(row, 'hora_inicio')} às {safe(row, 'hora_fim')}</div>{progress_html(row)}{chapter_strip(df, ordem)}"""
new_client = """<div class=\"yv-kicker yv-reveal\">Momento YVORA</div><div class=\"yv-h1 yv-reveal yv-delay-1\">{safe(row, 'prato', 'Momento YVORA')}</div>"""
s = s.replace(old_client, new_client)

s = s.replace(
    'Carnes, queijos, tempo e atmosfera em uma mesma narrativa.',
    'A etapa atual é revelada no ritmo da noite.'
)

# Remove clock-based progress from manual-control views where the real time is not useful.
s = s.replace("{progress_html(row)}{playback_block(row)}", "{playback_block(row)}")
s = s.replace("{progress_html(row)}<br><div class=\"yv-white-muted\">", "<br><div class=\"yv-white-muted\">")
s = s.replace("{progress_html(r, light=True) if int(r['ordem']) == ordem else ''}", "")

# Replace the operation hero copy with a clear manual-control status.
s = s.replace(
    "Atual: {safe(row, 'prato')} · {safe(row, 'musica')}",
    "Etapa ativa {ordem} de {max_ordem}: {safe(row, 'prato')} · {safe(row, 'musica')}"
)

p.write_text(s, encoding='utf-8')
