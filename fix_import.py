import io
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace("\nfrom fastapi import Body\n", "\n")
if not s.startswith("from fastapi import Body"):
    s = "from fastapi import Body\n" + s
io.open(p, "w", encoding="utf-8").write(s)
print("import Body di baris atas ok")
