from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from pydantic import BaseModel, ConfigDict

from app.db import Base


class Produk(Base):
    __tablename__ = "produk"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String, index=True)
    harga = Column(Float, default=0.0)
    stok = Column(Integer, default=0)


class ProdukCreate(BaseModel):
    nama: str
    harga: float
    stok: int


class ProdukOut(ProdukCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class Transaksi(Base):
    __tablename__ = "transaksi"

    id = Column(Integer, primary_key=True, index=True)
    items = Column(String)
    total = Column(Float, default=0.0)
    bayar = Column(Float, default=0.0)
    kembalian = Column(Float, default=0.0)
    dibuat = Column(DateTime, default=datetime.now)
