import sys
from sqlalchemy.orm import sessionmaker
from app import models
from app.db import engine
from app.pembulatan import bulat_harga

db = sessionmaker(bind=engine)()
terapkan = len(sys.argv) > 1 and sys.argv[1].upper() == "TERAPKAN"

n = 0
for p in db.query(models.Produk).all():
    if (p.kategori or "").upper() != "BIBIT":
        continue
    baru = bulat_harga((p.harga_modal or 0) * 2)
    if n < 12:
        print(p.nama, "| modal", p.harga_modal, "| jual lama", p.harga, "| jual baru", baru)
    if terapkan:
        p.harga = float(baru)
    n += 1

if terapkan:
    db.commit()
    print("DITERAPKAN ke", n, "produk BIBIT")
else:
    print("--- PREVIEW:", n, "produk BIBIT ---")
    print("Jika sudah cocok, jalankan: python ubah_harga_bibit.py TERAPKAN")
