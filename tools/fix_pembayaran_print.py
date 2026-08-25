from pathlib import Path

p = Path("templates/struk_print.html")
s = p.read_text(encoding="utf-8")

start = s.index('<div class="line"></div>\n<table>\n<tr>\n<td class="r" style="font-weight:bold">TOTAL BAYAR')
end = s.index('{% if ag %}', start)

new = """<div class="line"></div>

<table>
<tr>
<td class="r" style="font-weight:bold">PEMBAYARAN</td>
<td class="r"></td>
</tr>

{% if t.poin_dipakai %}
<tr>
<td class="r">Poin :</td>
<td class="r">-{{ (t.poin_dipakai or 0)|rpx }}</td>
</tr>
{% endif %}

{% if t.p_tunai %}
<tr>
<td class="r">Tunai :</td>
<td class="r">{{ (t.p_tunai or 0)|rpx }}</td>
</tr>
{% endif %}

{% if t.p_nontunai %}
<tr>
<td class="r">QRIS :</td>
<td class="r">{{ (t.p_nontunai or 0)|rpx }}</td>
</tr>
{% endif %}

<tr>
<td class="r" style="font-weight:bold">TOTAL BAYAR</td>
<td class="r" style="font-weight:bold">
{{ ((t.total or 0) - (t.poin_dipakai or 0))|rpx }}
</td>
</tr>

{% if not nontunai and not t.poin_dipakai %}
<tr>
<td class="r">Bayar :</td>
<td class="r">{{ (t.bayar or 0)|rpx }}</td>
</tr>
<tr>
<td class="r">Kembali :</td>
<td class="r">{{ (t.kembalian or 0)|rpx }}</td>
</tr>
{% endif %}
</table>

<div class="line"></div>

"""
s = s[:start] + new + s[end:]

p.write_text(s, encoding="utf-8")
print("OK pembayaran struk dirapikan")
