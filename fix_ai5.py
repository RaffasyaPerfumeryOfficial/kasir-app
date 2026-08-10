import io
m = io.open("app/main.py", encoding="utf-8").read()
old = "                        peng_list = [p for p in db.query(models.Pengeluaran)"
new = "            peng_list = [p for p in db.query(models.Pengeluaran)"
assert old in m, "baris tidak ketemu"
m = m.replace(old, new, 1)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("indent rapi ok")
