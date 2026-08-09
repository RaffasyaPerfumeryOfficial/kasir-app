from datetime import datetime
from app import models
from app.db import SessionLocal, Base, engine
Base.metadata.create_all(bind=engine)
db = SessionLocal()

DATA = [
    (1, [(277632, "SLATER"), (384950, "SPINJAM"), (1999, "GSPIKER")]),
    (2, [(1999, "GSPIKER")]),
    (3, [(3476046, "ORDER SAG"), (388000, "LISA WANGI"), (1999, "GSPIKER")]),
    (4, [(1999, "GSPIKER")]),
    (5, [(60000, "KABEL POWER"), (1360880, "ALAS MOUSE"), (1999, "GSPIKER"), (103350, "KREDIVO + SHOPEE")]),
    (6, [(35000, "BIAYA PAKET"), (1999, "GSPIKER"), (599000, "SHOPEE"), (177196, "ADAPUNDI")]),
    (7, [(350000, "GAJI")]),
    (9, [(672000, "AKULAKU")]),
]

def ket_of(p):
    return p.keterangan if hasattr(p, "keterangan") else p.nama

n = 0
for d, items in DATA:
    for j, k in items:
        dt = datetime(2026, 8, d, 12, 0)
        dup = False
        for row in db.query(models.Pengeluaran).all():
            if row.dibuat.date() == dt.date() and (row.jumlah or 0) == j and (ket_of(row) or "") == k:
                dup = True
                break
        if dup:
            continue
        p = models.Pengeluaran()
        if hasattr(p, "keterangan"):
            p.keterangan = k
        elif hasattr(p, "nama"):
            p.nama = k
        p.jumlah = j
        p.dibuat = dt
        db.add(p)
        n += 1
db.commit()
db.close()
print("pengeluaran lama masuk:", n, "baris")
