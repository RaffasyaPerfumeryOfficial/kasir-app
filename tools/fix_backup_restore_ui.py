from pathlib import Path

p = Path("templates/backup_restore.html")
s = p.read_text(encoding="utf-8")

s = s.replace(
'action="/backup/create"',
'action="/backup/manual"'
)

s = s.replace(
'''{% elif "kasir-" in b.nama %}
<span class="badge-manual">Manual</span>''',
'''{% elif "kasir_" in b.nama %}
<span class="badge-auto">Backup Harian</span>'''
)

s = s.replace(
'''<form method="post" action="/restore">

<input type="hidden" name="file" value="{{ b.file }}">''',
'''<form method="post" action="/backup/restore/{{ b.nama }}">'''
)

s = s.replace("📦", "??")
s = s.replace("⬇", "?")
s = s.replace("↻", "?")
s = s.replace("💾", "??")
s = s.replace("✓", "?")

p.write_text(s, encoding="utf-8")

print("OK patch backup restore UI")
