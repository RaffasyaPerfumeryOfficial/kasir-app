import io
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("\ufeff", "")
io.open(p, "w", encoding="utf-8").write(s)
print("bom removed")
