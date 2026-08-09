import io
p = "templates/kasir.html"
s = io.open(p, encoding="utf-8").read()
n = s.count("background:#f8fafc;")
s = s.replace("background:#f8fafc;", "background:#f8fafc;color:#0f172a;")
io.open(p, "w", encoding="utf-8").write(s)
print("warna teks diperbaiki:", n, "tombol")
