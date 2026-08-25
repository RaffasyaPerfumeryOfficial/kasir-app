from pathlib import Path

p = Path("templates/struk_print.html")
s = p.read_text(encoding="utf-8")

old = '''<tr><td style="width:60%">Poin +</td><td class="r">{{ "%0.0f"|format(pl.poin or 0) }}</td></tr>'''

new = '''{% if pl and pl.poin > 0 %}
<tr><td style="width:60%">Poin +</td><td class="r">{{ "%0.0f"|format(pl.poin) }}</td></tr>
{% endif %}'''

if old not in s:
    raise Exception("Bagian Poin + tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK fix poin struk")
