import io

# 1) hapus function bayar() duplikat (yang lama menimpa yang baru)
k = io.open("templates/kasir.html", encoding="utf-8").read()
first = k.find("function bayar(")
assert first != -1, "bayar baru tidak ketemu"
second = k.find("function bayar(", first + 10)
n = 0
while second != -1:
    nxt = k.find("\nfunction ", second + 10)
    end = nxt + 1 if nxt != -1 else len(k)
    k = k[:second] + k[end:]
    n += 1
    second = k.find("function bayar(", first + 10)
k = k.replace("window.location='/struk/'+d.id;", "window.location.href='/struk/'+d.id;", 1)
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("bayar duplikat dihapus:", n)

# 2) aturan: tukar poin = tidak dapat poin tambahan
m = io.open("app/main.py", encoding="utf-8").read()
old = """        if bibit_total > 0:
            earn = int(bibit_total * 0.05)"""
new = """        if bibit_total > 0 and poin == 0:
            earn = int(bibit_total * 0.05)"""
assert old in m, "blok earn tidak ketemu"
m = m.replace(old, new, 1)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("aturan poin ok")
