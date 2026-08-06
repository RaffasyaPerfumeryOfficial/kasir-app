import json

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.db import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aplikasi Kasir")
templates = Jinja2Templates(directory="templates")


class ItemKeranjang(BaseModel):
    produk_id: int
    jumlah: int


class TransaksiCreate(BaseModel):
    items: list[ItemKeranjang]
    bayar: float


@app.get("/")
def home():
    return {"app": "Aplikasi Kasir", "status": "jalan"}


@app.get("/kasir")
def halaman_kasir(request: Request, db: Session = Depends(get_db)):
    produk_list = db.query(models.Produk).all()
    return templates.TemplateResponse(request, "kasir.html", {"produk_list": produk_list})


@app.get("/manajemen")
def manajemen_produk(request: Request, db: Session = Depends(get_db)):
    produk_list = db.query(models.Produk).all()
    return templates.TemplateResponse(request, "manajemen.html", {"produk_list": produk_list})


@app.post("/produk/simpan")
def simpan_produk(
    nama: str = Form(...),
    harga: float = Form(...),
    stok: int = Form(...),
    db: Session = Depends(get_db),
):
    db_produk = models.Produk(nama=nama, harga=harga, stok=stok)
    db.add(db_produk)
    db.commit()
    return RedirectResponse(url="/manajemen", status_code=303)


@app.get("/riwayat")
def riwayat_transaksi(request: Request, db: Session = Depends(get_db)):
    transaksi_list = (
        db.query(models.Transaksi).order_by(models.Transaksi.id.desc()).all()
    )
    data = []
    for t in transaksi_list:
        data.append(
            {
                "id": t.id,
                "dibuat": t.dibuat.strftime("%d/%m/%Y %H:%M"),
                "items": json.loads(t.items),
                "total": t.total,
                "bayar": t.bayar,
                "kembalian": t.kembalian,
            }
        )
    total_penjualan = sum(t.total for t in transaksi_list)
    return templates.TemplateResponse(
        request,
        "riwayat.html",
        {
            "transaksi_list": data,
            "total_penjualan": total_penjualan,
            "jumlah_transaksi": len(data),
        },
    )


@app.get("/produk", response_model=list[models.ProdukOut])
def daftar_produk(db: Session = Depends(get_db)):
    return db.query(models.Produk).all()


@app.post("/produk", response_model=models.ProdukOut)
def tambah_produk(produk: models.ProdukCreate, db: Session = Depends(get_db)):
    db_produk = models.Produk(**produk.model_dump())
    db.add(db_produk)
    db.commit()
    db.refresh(db_produk)
    return db_produk


@app.post("/transaksi")
def buat_transaksi(t: TransaksiCreate, db: Session = Depends(get_db)):
    total = 0.0
    detail = []
    for it in t.items:
        produk = db.get(models.Produk, it.produk_id)
        if not produk:
            raise HTTPException(404, "Produk tidak ditemukan")
        if produk.stok < it.jumlah:
            raise HTTPException(400, "Stok tidak cukup: " + produk.nama)
        subtotal = produk.harga * it.jumlah
        total += subtotal
        detail.append({"nama": produk.nama, "jumlah": it.jumlah, "subtotal": subtotal})
    for it in t.items:
        produk = db.get(models.Produk, it.produk_id)
        produk.stok -= it.jumlah
    if t.bayar < total:
        raise HTTPException(400, "Uang bayar kurang")
    trx = models.Transaksi(
        items=json.dumps(detail, ensure_ascii=False),
        total=total,
        bayar=t.bayar,
        kembalian=t.bayar - total,
    )
    db.add(trx)
    db.commit()
    db.refresh(trx)
    return {"id": trx.id, "total": total, "kembalian": trx.kembalian}

@app.get("/struk/{trx_id}")
def struk_transaksi(request: Request, trx_id: int, db: Session = Depends(get_db)):
    trx = db.get(models.Transaksi, trx_id)
    if not trx:
        raise HTTPException(404, "Transaksi tidak ditemukan")
    return templates.TemplateResponse(
        request,
        "struk.html",
        {
            "trx": trx,
            "items": json.loads(trx.items),
        },
    )
