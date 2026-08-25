from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

marker = "def struk_page(trx_id: int, request: Request, db: Session = Depends(get_db)):"

pos1 = s.find(marker)

if pos1 == -1:
    raise Exception("struk_page pertama tidak ditemukan")

pos2 = s.find(marker, pos1 + 1)

if pos2 == -1:
    raise Exception("struk_page kedua tidak ditemukan")

# cari decorator sebelum fungsi kedua
awal = s.rfind("@app", 0, pos2)

# cari fungsi setelah blok kedua
akhir = s.find("def _rpx", pos2)

if akhir == -1:
    raise Exception("batas akhir struk tidak ditemukan")

hapus = s[awal:akhir]

s = s.replace(hapus, "", 1)

p.write_text(s, encoding="utf-8")

print("OK hapus duplicate struk_page")