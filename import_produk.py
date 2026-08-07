import csv

from sqlalchemy.orm import sessionmaker

from app import models
from app.db import Base, engine

Base.metadata.create_all(bind=engine)
models.migrate_db()

db = sessionmaker(bind=engine)()


def num(s):
    s = (s or "").strip()
    if not s:
        return 0.0
    return float(s.replace(",", "."))


PATH = r"F:\Users\rival\Downloads\KASIR MEKAR SARI - Produk.csv"

with open(PATH, encoding="utf-8-sig", errors="ignore") as f:
    reader = csv.DictReader(f)
    for row in reader:
        nama = (row.get("Nama Barang") or "").strip()
        if not nama:
            continue
        kode = (row.get("Nama Kode") or "").strip()
        modal = num(row.get("Harga Modal"))
        jual = num(row.get("Harga Jual"))
        stok = int(num(row.get("Stok")))
        kategori = (row.get("Kategori") or "").strip()
        if not db.query(models.Produk).filter_by(nama=nama).first():
            db.add(
                models.Produk(
                    nama=nama,
                    kode=kode,
                    kategori=kategori,
                    harga=jual,
                    harga_modal=modal,
                    stok=stok,
                )
            )
db.commit()
print("Import selesai. Total produk:", db.query(models.Produk).count())
