import io
m = io.open("app/main.py", encoding="utf-8").read()
old = 'qty = int(it["jumlah"])'
new = 'qty = float(it["jumlah"])\n        if qty == int(qty): qty = int(qty)'
n = m.count(old)
assert n == 2, "harusnya ada 2 tempat, ketemu " + str(n)
m = m.replace(old, new)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("qty desimal ok (2 tempat)")
