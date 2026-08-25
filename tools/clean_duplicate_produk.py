from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

target = '''

@app.get("/produk/{produk_id}")
def produk_detail(produk_id: int, request: Request, db: Session = Depends(get_db)):
    produk = db.get(models.Produk, produk_id)
'''

pos1 = s.find(target)

if pos1 == -1:
    raise Exception("produk_detail pertama tidak ditemukan")

pos2 = s.find(target, pos1 + 1)

if pos2 == -1:
    raise Exception("produk_detail kedua tidak ditemukan")

# cari akhir stok_masuk kedua sebelum masuk_massal
akhir = s.find('@app.post("/stok/masuk_massal")', pos2)

if akhir == -1:
    raise Exception("batas masuk_massal tidak ditemukan")

hapus = s[pos2:akhir]

s = s.replace(hapus, "", 1)

p.write_text(s, encoding="utf-8")

print("OK hapus duplicate produk_detail + stok_masuk")