from datetime import date
from app import models
from app.db import SessionLocal
db = SessionLocal()
MAP = {
    1360880: "KREDIVO",
    60000: "KABEL POWER + ALAS MOUSE",
    103350: "SHOPEE",
    1999: "GSPIKER",
}
n = 0
for row in db.query(models.Pengeluaran).all():
    if row.dibuat.date() == date(2026, 8, 5) and (row.jumlah or 0) in MAP:
        if hasattr(row, "keterangan"):
            row.keterangan = MAP[row.jumlah]
        elif hasattr(row, "nama"):
            row.nama = MAP[row.jumlah]
        n += 1
db.commit()
db.close()
print("keterangan tanggal 5 diperbaiki:", n, "baris")
