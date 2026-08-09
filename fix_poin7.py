import io, re

k = io.open("templates/kasir.html", encoding="utf-8").read()

# 1) helper aman
if "function setTxt(" not in k:
    old = "function fmtInput(el){el.value=el.value.replace(/[^\\d]/g,'');if(el.value==='')return;el.value=fmtRp(parseInt(el.value));}"
    assert old in k
    k = k.replace(old, old + "\nfunction setTxt(id,v){var e=document.getElementById(id);if(e)e.textContent=v;}", 1)
k = k.replace("document.getElementById('total').textContent=fmtRp(T);", "setTxt('total',fmtRp(T));", 1)
k = k.replace("document.getElementById('total2').textContent=fmtRp(T);", "setTxt('total2',fmtRp(T));", 1)
k = k.replace("document.getElementById('total3').textContent=fmtRp(T);", "setTxt('total3',fmtRp(T));", 1)

# 2) hapus function bayar duplikat
first = k.find("function bayar(")
assert first != -1
second = k.find("function bayar(", first + 10)
n = 0
while second != -1:
    nxt = k.find("\nfunction ", second + 10)
    end = nxt + 1 if nxt != -1 else len(k)
    k = k[:second] + k[end:]
    n += 1
    second = k.find("function bayar(", first + 10)
print("bayar duplikat dihapus:", n)

# 3) sukses = langsung struk (cocok versi apa pun)
pat = re.compile(r"if\(d\.ok\)\{cart=\[\];.*?window\.location(?:\.href)?='/struk/'\+d\.id;\}")
new = "if(d.ok){document.getElementById('modalBayar').style.display='none';window.location.href='/struk/'+d.id;}"
k, c = pat.subn(new, k, count=1)
assert c == 1, "baris sukses tidak ketemu"
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("redirect struk ok")

# 4) aturan: tukar poin = tidak dapat poin tambahan
m = io.open("app/main.py", encoding="utf-8").read()
old = """        if bibit_total > 0:
            earn = int(bibit_total * 0.05)"""
new = """        if bibit_total > 0 and poin == 0:
            earn = int(bibit_total * 0.05)"""
if old in m:
    m = m.replace(old, new, 1)
    io.open("app/main.py", "w", encoding="utf-8").write(m)
    print("aturan poin ok")
else:
    print("aturan poin sudah ada")
