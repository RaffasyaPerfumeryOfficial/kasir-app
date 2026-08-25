from pathlib import Path

p = Path("templates/struk_print.html")
s = p.read_text(encoding="utf-8")

# tambah metode setelah karyawan
old = '''<tr><td>Karyawan</td><td>: MKSR - Admin</td></tr>'''

new = '''<tr><td>Karyawan</td><td>: MKSR - Admin</td></tr>
<tr><td>Metode</td><td>: {{ (t.metode or "TUNAI").replace("POIN + NON-TUNAI (","").replace(")","") }}</td></tr>'''

if old in s:
    s = s.replace(old,new,1)

# rapikan header
old2 = '''<strong style="font-size:14px">MEKAR SARI</strong> <span style="font-size:10px">perfumery</span><br>'''

new2 = '''<strong style="font-size:16px">MEKAR SARI</strong><br>
<span style="font-size:11px">Refill Perfumery</span><br>'''

if old2 in s:
    s = s.replace(old2,new2,1)

# ubah total bawah
old3 = '''<td class="r" style="font-weight:bold">TOTAL</td>'''

new3 = '''<td class="r" style="font-weight:bold">TOTAL BAYAR</td>'''

if old3 in s:
    s = s.replace(old3,new3,1)

p.write_text(s,encoding="utf-8")

print("OK struk print dirapikan")
