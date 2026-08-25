from pathlib import Path

p = Path("templates/struk_print.html")
s = p.read_text(encoding="utf-8")

old = '<tr><td>Total poin</td><td class="r">{{ "%0.0f"|format(ag.poin or 0) }}</td></tr>'

new = '''{% if pl and pl.poin > 0 %}
<tr><td>Poin tambah</td><td class="r">+{{ "%0.0f"|format(pl.poin) }}</td></tr>
{% endif %}
<tr><td>Sisa poin</td><td class="r">{{ "%0.0f"|format(ag.poin or 0) }}</td></tr>'''

if old not in s:
    raise Exception("Bagian total poin tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK poin struk dirapikan")
