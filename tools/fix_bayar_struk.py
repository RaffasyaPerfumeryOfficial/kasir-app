from pathlib import Path

p = Path("templates/struk_print.html")
s = p.read_text(encoding="utf-8")

old = """
<tr><td class="r">Bayar :</td><td class="r">{{ (t.bayar or 0)|rpx }}</td></tr>
<tr><td class="r">Kembali :</td><td class="r">{{ (t.kembalian or 0)|rpx }}</td></tr>
"""

new = """
{% if not nontunai %}
<tr><td class="r">Bayar :</td><td class="r">{{ (t.bayar or 0)|rpx }}</td></tr>
<tr><td class="r">Kembali :</td><td class="r">{{ (t.kembalian or 0)|rpx }}</td></tr>
{% endif %}
"""

if old not in s:
    raise Exception("Bagian Bayar/Kembali tidak ditemukan")

s = s.replace(old,new)

p.write_text(s,encoding="utf-8")

print("OK Bayar Kembali dirapikan")
