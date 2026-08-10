import io
k = io.open("templates/kasir.html", encoding="utf-8").read()
a = k.count("background:#f8fafc;text-align:left;font-weight:600")
k = k.replace("background:#f8fafc;text-align:left;font-weight:600", "background:#f8fafc;color:#0f172a;text-align:left;font-weight:600")
b = k.count("background:#e2e8f0;text-align:left;font-weight:600")
k = k.replace("background:#e2e8f0;text-align:left;font-weight:600", "background:#e2e8f0;color:#0f172a;text-align:left;font-weight:600")
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("warna teks ok", a, b)
