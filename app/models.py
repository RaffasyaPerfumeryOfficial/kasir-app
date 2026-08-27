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
    poin_dipakai = Column(Float, default=0)
    poin_setelah = Column(Float, default=0)

    id = Column(Integer, primary_key=True, index=True)
    kode_trx = Column(String, default="")
    request_id = Column(String, unique=True)
    items = Column(String)
    total = Column(Float, default=0.0)
    total_modal = Column(Float, default=0.0)
    total_diskon = Column(Float, default=0.0)
    bayar = Column(Float, default=0.0)
    kembalian = Column(Float, default=0.0)
    metode = Column(String, default="TUNAI")
    p_tunai = Column(Float, default=0.0)
    p_nontunai = Column(Float, default=0.0)
    void = Column(Integer, default=0)
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
        if "user" not in tables:
            conn.execute(text("""
                CREATE TABLE user (
                    id INTEGER PRIMARY KEY,
                    username VARCHAR UNIQUE,
                    password VARCHAR,
                    role VARCHAR,
                    dibuat DATETIME
                )
            """))

        cek = conn.execute(
            text("SELECT COUNT(*) FROM user")
        ).scalar()

        if cek == 0:
            conn.execute(
                text("""
                    INSERT INTO user
                    (username,password,role)
                    VALUES
                    ('admin','1234','admin'),
                    ('kasir','kasir123','kasir')
                """)
            )

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
            if "request_id" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN request_id VARCHAR"))
            if "total_modal" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN total_modal FLOAT"))
            if "metode" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN metode VARCHAR"))
            if "total_diskon" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN total_diskon FLOAT"))
            if "poin_setelah" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN poin_setelah FLOAT"))
            if "p_tunai" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN p_tunai FLOAT"))
            if "p_nontunai" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN p_nontunai FLOAT"))
            if "void" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN void INTEGER"))
            if "void_reason" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN void_reason VARCHAR"))
            if "void_time" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN void_time DATETIME"))
            if "void_by" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN void_by VARCHAR"))
            conn.execute(text(
                "UPDATE transaksi SET p_tunai = total, p_nontunai = 0 "
                "WHERE p_tunai IS NULL AND (metode IS NULL OR metode = 'TUNAI')"
            ))
            conn.execute(text(
                "UPDATE transaksi SET p_tunai = 0, p_nontunai = total "
                "WHERE p_nontunai IS NULL AND metode IS NOT NULL AND metode != 'TUNAI'"
            ))

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="kasir")
    dibuat = Column(DateTime, default=datetime.now)


class Sesi(Base):
    __tablename__ = "sesi"

    token = Column(String, primary_key=True)
    user_id = Column(Integer)
    username = Column(String)
    role = Column(String)
    dibuat = Column(DateTime, default=datetime.now)

class PesanAI(Base):
    __tablename__ = "pesan_ai"

    id = Column(Integer, primary_key=True, index=True)
    pertanyaan = Column(String)
    jawaban = Column(String)
    dibuat = Column(DateTime, default=datetime.now)


class StokMasuk(Base):
    __tablename__ = "stok_masuk"
    id = Column(Integer, primary_key=True)
    nama = Column(String)
    jumlah = Column(Integer, default=0)
    keterangan = Column(String)
    dibuat = Column(DateTime, default=datetime.now)

class RiwayatTutup(Base):
    __tablename__ = "riwayat_tutup"
    id = Column(Integer, primary_key=True)
    omzet = Column(Float, default=0)
    tunai = Column(Float, default=0)
    nontunai = Column(Float, default=0)
    pengeluaran = Column(Float, default=0)
    ringkasan = Column(String)
    dibuat = Column(DateTime, default=datetime.now)


from sqlalchemy import Date

class RekapManual(Base):
    __tablename__ = "rekap_manual"
    id = Column(Integer, primary_key=True)
    tanggal = Column(Date)
    omzet = Column(Float, default=0)
    modal = Column(Float, default=0)
    keuntungan = Column(Float, default=0)
    margin = Column(String)
    trx = Column(Integer, default=0)


class Anggota(Base):
    __tablename__ = "anggota"
    id = Column(Integer, primary_key=True)
    nama = Column(String)
    no_hp = Column(String)
    nomor_member = Column(String)
    poin = Column(Float, default=0)
    dibuat = Column(DateTime, default=datetime.now)

class PoinLog(Base):
    __tablename__ = "poin_log"
    id = Column(Integer, primary_key=True)
    anggota_id = Column(Integer)
    trx_id = Column(Integer)
    poin = Column(Float, default=0)
    dibuat = Column(DateTime, default=datetime.now)


class Pemasukan(Base):
    __tablename__ = "pemasukan"

    id = Column(Integer, primary_key=True, index=True)
    keterangan = Column(String)
    jumlah = Column(Float, default=0.0)
    dibuat = Column(DateTime, default=datetime.now)
