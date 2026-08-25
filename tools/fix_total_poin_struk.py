from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

old = """{% if t.poin_dipakai %}<tr><td>POIN dipakai</td><td style="text-align:right">-{{ "%0.0f"|format(t.poin_dipakai) }}</td></tr>{% endif %}
<tr><td>Bayar</td><td style="text-align:right">{{ "%0.0f"|format(t.bayar or 0) }}</td></tr>
"""

new = """{% if t.poin_dipakai %}
<tr>
<td>POIN dipakai</td>
<td style="text-align:right">-{{ "%0.0f"|format(t.poin_dipakai) }}</td>
</tr>
{% endif %}
<tr>
<td><strong>TOTAL BAYAR</strong></td>
<td style="text-align:right">
<strong>{{ "%0.0f"|format((t.total or 0) - (t.poin_dipakai or 0)) }}</strong>
</td>
</tr>
"""

if old not in s:
    raise Exception("Bagian total poin tidak ditemukan")

s=s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK total bayar struk diperbaiki")
