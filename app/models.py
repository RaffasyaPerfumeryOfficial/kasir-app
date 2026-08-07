from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, inspect, text
from pydantic import BaseModel, ConfigDict

from app.db import Base, engine


class Produk(Base):
    __tablename__ = "produk"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String, index=True)
    kode = Column(String, default="")
    kategori = Column(String, default="")
    harga = Column(Float, default=0.0)
    harga_modal = Column(Float, default=0.0)
    stok = Column(Integer, default=0)


class ProdukCreate(BaseModel):
    nama: str
    kode: str = ""
    kategori: str = ""
    harga: float
    harga_modal: float = 0.0
    stok: int


class ProdukOut(ProdukCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class Transaksi(Base):
    __tablename__ = "transaksi"

    id = Column(Integer, primary_key=True, index=True)
    kode_trx = Column(String, default="")
    items = Column(String)
    total = Column(Float, default=0.0)
    total_modal = Column(Float, default=0.0)
    total_diskon = Column(Float, default=0.0)
    bayar = Column(Float, default=0.0)
    kembalian = Column(Float, default=0.0)
    metode = Column(String, default="TUNAI")
    p_tunai = Column(Float, default=0.0)
    p_nontunai = Column(Float, default=0.0)
    dibuat = Column(DateTime, default=datetime.now)


class Pengeluaran(Base):
    __tablename__ = "pengeluaran"

    id = Column(Integer, primary_key=True, index=True)
    keterangan = Column(String)
    jumlah = Column(Float, default=0.0)
    dibuat = Column(DateTime, default=datetime.now)


class TutupKasir(Base):
    __tablename__ = "tutup_kasir"

    id = Column(Integer, primary_key=True, index=True)
    tanggal = Column(String)
    tunai_sistem = Column(Float, default=0.0)
    tunai_input = Column(Float, default=0.0)
    tunai_selisih = Column(Float, default=0.0)
    nontunai_sistem = Column(Float, default=0.0)
    nontunai_input = Column(Float, default=0.0)
    nontunai_selisih = Column(Float, default=0.0)
    dibuat = Column(DateTime, default=datetime.now)


def migrate_db():
    insp = inspect(engine)
    tables = insp.get_table_names()
    with engine.begin() as conn:
        if "produk" in tables:
            cols = [c["name"] for c in insp.get_columns("produk")]
            if "kode" not in cols:
                conn.execute(text("ALTER TABLE produk ADD COLUMN kode VARCHAR"))
            if "kategori" not in cols:
                conn.execute(text("ALTER TABLE produk ADD COLUMN kategori VARCHAR"))
            if "harga_modal" not in cols:
                conn.execute(text("ALTER TABLE produk ADD COLUMN harga_modal FLOAT"))
        if "transaksi" in tables:
            cols = [c["name"] for c in insp.get_columns("transaksi")]
            if "kode_trx" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN kode_trx VARCHAR"))
            if "total_modal" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN total_modal FLOAT"))
            if "metode" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN metode VARCHAR"))
            if "total_diskon" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN total_diskon FLOAT"))
            if "p_tunai" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN p_tunai FLOAT"))
            if "p_nontunai" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN p_nontunai FLOAT"))
            conn.execute(text(
                "UPDATE transaksi SET p_tunai = total, p_nontunai = 0 "
                "WHERE p_tunai IS NULL AND (metode IS NULL OR metode = 'TUNAI')"
            ))
            conn.execute(text(
                "UPDATE transaksi SET p_tunai = 0, p_nontunai = total "
                "WHERE p_nontunai IS NULL AND metode IS NOT NULL AND metode != 'TUNAI'"
            ))
