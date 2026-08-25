from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

old = '<tr><td>Poin tambah</td><td style="text-align:right">+{{ "%0.0f"|format(pl.poin or 0) }}</td></tr>'

new = '''{% if pl and pl.poin > 0 %}
<tr>
<td>Poin tambah</td>
<td style="text-align:right">+{{ "%0.0f"|format(pl.poin) }}</td>
</tr>
{% endif %}'''

if old not in s:
    raise Exception("Baris Poin tambah tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK poin tambah diperbaiki")
