from pathlib import Path

p = Path("templates/struk_print.html")
s = p.read_text(encoding="utf-8")

old = '<div class="c" style="margin-top:8px">Terima Kasih</div><div class="c" style="font-size:11px;margin-top:4px">Simpan struk ini sebagai bukti yang sah</div>'

new = '''<div class="c" style="margin-top:8px;font-weight:bold">
TERIMA KASIH
</div>

<div class="c" style="font-size:11px;margin-top:6px">
Simpan struk ini sebagai<br>
bukti pembayaran yang sah.
</div>'''

if old not in s:
    raise Exception("Footer tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK footer struk dirapikan")
