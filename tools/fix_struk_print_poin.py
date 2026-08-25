from pathlib import Path

p = Path("templates/struk_print.html")
s = p.read_text(encoding="utf-8")


old = '''{% if t.poin_dipakai %}
<table><tr><td class="r" style="width:60%">POIN :</td><td class="r">{{ (t.poin_dipakai or 0)|rpx }}</td></tr></table>
<div class="line"></div>
{% endif %}'''


new = '''{% if t.poin_dipakai %}
<table>
<tr>
<td class="r" style="width:60%">POIN dipakai :</td>
<td class="r">-{{ (t.poin_dipakai or 0)|rpx }}</td>
</tr>
<tr>
<td class="r"><strong>TOTAL BAYAR :</strong></td>
<td class="r"><strong>{{ ((t.total or 0) - (t.poin_dipakai or 0))|rpx }}</strong></td>
</tr>
</table>
<div class="line"></div>
{% endif %}'''


if old not in s:
    raise Exception("Bagian poin print tidak ditemukan")

s=s.replace(old,new,1)


old2 = '''{% if ag %}
<table>
<tr><td style="width:60%">Poin +</td><td class="r">{{ "%0.0f"|format(pl.poin or 0) }}</td></tr>
<tr><td>Total poin</td><td class="r">{{ "%0.0f"|format(ag.poin or 0) }}</td></tr>
</table>
<div class="line"></div>
{% endif %}'''


new2 = '''{% if ag %}
<table>
{% if pl and pl.poin > 0 and not t.poin_dipakai %}
<tr>
<td style="width:60%">Poin +</td>
<td class="r">{{ "%0.0f"|format(pl.poin or 0) }}</td>
</tr>
{% endif %}
<tr>
<td>Total poin</td>
<td class="r">{{ "%0.0f"|format(ag.poin or 0) }}</td>
</tr>
</table>
<div class="line"></div>
{% endif %}'''


if old2 in s:
    s=s.replace(old2,new2,1)

p.write_text(s,encoding="utf-8")

print("OK struk print poin diperbaiki")
