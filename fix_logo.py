import io

# 1) struk layar
t = io.open("templates/struk.html", encoding="utf-8").read()
old = '''  <div style="text-align:center">
    <h3 style="margin:0">MEKAR SARI</h3>
    <div style="color:var(--muted)">Refill Perfumery</div>
  </div>'''
new = '''  <div style="text-align:center">
    <img src="/static/logo.png" style="width:72px;height:72px;object-fit:contain;margin:0 auto 6px;display:block">
    <h3 style="margin:0">MEKAR SARI</h3>
    <div style="color:var(--muted)">Refill Perfumery</div>
    <div style="color:var(--muted);font-size:12px;margin-top:4px">Jl. Mekar Sari No.5, Bekasi Jaya, Kec. Bekasi Tim.,<br>Kota Bks, Jawa Barat 17112</div>
    <div style="color:var(--muted);font-size:12px">HP: 0821-1897-1096</div>
  </div>'''
assert old in t
t = t.replace(old, new, 1)
io.open("templates/struk.html", "w", encoding="utf-8").write(t)
print("struk layar ok")

# 2) struk cetak 80mm
p = io.open("templates/struk_print.html", encoding="utf-8").read()
oldp = '<div class="c"><strong>MEKAR SARI</strong><br>Refill Perfumery</div>'
newp = '''<div class="c">
<img src="/static/logo.png" style="width:60px;height:60px;object-fit:contain;margin:0 auto 4px;display:block">
<strong>MEKAR SARI</strong><br>Refill Perfumery<br>
<span style="font-size:9px">Jl. Mekar Sari No.5, Bekasi Jaya, Kec. Bekasi Tim., Kota Bks, Jawa Barat 17112</span><br>
<span style="font-size:9px">HP: 0821-1897-1096</span>
</div>'''
assert oldp in p
p = p.replace(oldp, newp, 1)
io.open("templates/struk_print.html", "w", encoding="utf-8").write(p)
print("struk 80mm ok")

# 3) teks WA struk
m = io.open("app/main.py", encoding="utf-8").read()
oldm = '''    L.append("Refill Perfumery")
    L.append("-----------------------------------------")
    L.append("No   : "'''
newm = '''    L.append("Refill Perfumery")
    L.append("Jl. Mekar Sari No.5, Bekasi Jaya,")
    L.append("Kec. Bekasi Tim., Kota Bks, Jawa Barat 17112")
    L.append("HP: 0821-1897-1096")
    L.append("-----------------------------------------")
    L.append("No   : "'''
assert oldm in m
m = m.replace(oldm, newm, 1)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("teks wa ok")
