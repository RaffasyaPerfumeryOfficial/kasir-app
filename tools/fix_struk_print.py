from pathlib import Path

p = Path("templates/struk_print.html")
s = p.read_text(encoding="utf-8")

old = '''<div style="text-align:right;font-size:16px;font-weight:bold">Grand Total : {{ (t.total or 0)|rpx }}</div>
<div class="line"></div>
'''

new = '''<table>
<tr>
<td class="r" style="font-weight:bold">TOTAL</td>
<td class="r" style="font-size:16px;font-weight:bold">
{{ (t.total or 0)|rpx }}
</td>
</tr>
<tr>
<td class="r">Bayar :</td>
<td class="r">{{ (t.bayar or 0)|rpx }}</td>
</tr>
<tr>
<td class="r">Kembali :</td>
<td class="r">{{ (t.kembalian or 0)|rpx }}</td>
</tr>
</table>
<div class="line"></div>
'''

if old not in s:
    raise Exception("bagian total tidak ditemukan")

s=s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK struk print diperbaiki")
