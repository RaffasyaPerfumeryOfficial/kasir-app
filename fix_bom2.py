import io
p = "app/main.py"
s = io.open(p, encoding="utf-8-sig").read()
s = s.replace("\ufeff", "")
io.open(p, "w", encoding="utf-8").write(s)
print("BOM dibuang, file bersih")
