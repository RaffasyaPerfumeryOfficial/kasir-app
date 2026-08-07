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

@app.post("/produk/hapus/{produk_id}")
def hapus_produk(produk_id: int, db: Session = Depends(get_db)):
    produk = db.get(models.Produk, produk_id)
    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")
    db.delete(produk)
    db.commit()
    return RedirectResponse(url="/manajemen", status_code=303)


@app.get("/produk/edit/{produk_id}")
def form_edit_produk(request: Request, produk_id: int, db: Session = Depends(get_db)):
    produk = db.get(models.Produk, produk_id)
    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")
    return templates.TemplateResponse(request, "edit_produk.html", {"produk": produk})


@app.post("/produk/update/{produk_id}")
def update_produk(
    produk_id: int,
    nama: str = Form(...),
    harga: float = Form(...),
    stok: int = Form(...),
    db: Session = Depends(get_db),
):
    produk = db.get(models.Produk, produk_id)
    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")
    produk.nama = nama
    produk.harga = harga
    produk.stok = stok
    db.commit()
    return RedirectResponse(url="/manajemen", status_code=303)

@app.get("/laporan")
def laporan_harian(request: Request, db: Session = Depends(get_db)):
    transaksi_list = db.query(models.Transaksi).all()
    rekap = {}
    for t in transaksi_list:
        key = t.dibuat.date()
        if key not in rekap:
            rekap[key] = {
                "tanggal": key.strftime("%d/%m/%Y"),
                "jumlah": 0,
                "omzet": 0.0,
                "key": key,
            }
        rekap[key]["jumlah"] += 1
        rekap[key]["omzet"] += t.total
    laporan = sorted(rekap.values(), key=lambda x: x["key"], reverse=True)
    total_omzet = sum(t.total for t in transaksi_list)
    return templates.TemplateResponse(
        request, "laporan.html", {"laporan": laporan, "total_omzet": total_omzet}
    )

import secrets

USERS = {"admin": "1234", "kasir": "kasir123"}
SESSIONS = set()


@app.get("/login")
def halaman_login(request: Request):
    return templates.TemplateResponse(request, "login.html", {"pesan": ""})


@app.post("/login/masuk")
def login_masuk(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if USERS.get(username) == password:
        sid = secrets.token_hex(16)
        SESSIONS.add(sid)
        resp = RedirectResponse("/dashboard", status_code=303)
        resp.set_cookie("session_id", sid)
        return resp
    return templates.TemplateResponse(
        request, "login.html", {"pesan": "Username atau password salah"}
    )


@app.get("/logout")
def logout(request: Request):
    sid = request.cookies.get("session_id")
    SESSIONS.discard(sid)
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("session_id")
    return resp


@app.middleware("http")
async def proteksi_login(request: Request, call_next):
    path = request.url.path
    publik = (
        path == "/login"
        or path == "/login/masuk"
        or path == "/favicon.ico" or path.startswith("/static")
    )
    if not publik:
        sid = request.cookies.get("session_id")
        if not sid or sid not in SESSIONS:
            return RedirectResponse("/login", status_code=303)
    return await call_next(request)


from fastapi.staticfiles import StaticFiles

NAMA_TOKO = "MEKAR SARI"

app.mount("/static", StaticFiles(directory="static"), name="static")
templates.env.globals["nama_toko"] = NAMA_TOKO

@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    from datetime import date, timedelta
    today = date.today()
    transaksi_list = db.query(models.Transaksi).all()
    omzet_hari_ini = 0.0
    transaksi_hari_ini = 0
    for t in transaksi_list:
        if t.dibuat and t.dibuat.date() == today:
            omzet_hari_ini += t.total
            transaksi_hari_ini += 1
    terlaris = {}
    for t in transaksi_list:
        for it in json.loads(t.items):
            nama = it["nama"]
            terlaris[nama] = terlaris.get(nama, 0) + it["jumlah"]
    top_produk = sorted(terlaris.items(), key=lambda x: x[1], reverse=True)[:5]
    grafik = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        total = sum(t.total for t in transaksi_list if t.dibuat and t.dibuat.date() == d)
        grafik.append({"label": d.strftime("%d/%m"), "total": total})
    max_total = max([g["total"] for g in grafik] + [1])
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "omzet_hari_ini": omzet_hari_ini,
            "transaksi_hari_ini": transaksi_hari_ini,
            "jumlah_produk": db.query(models.Produk).count(),
            "top_produk": top_produk,
            "grafik": grafik,
            "max_total": max_total,
        },
    )


from fastapi.responses import Response

@app.get("/laporan/export")
def export_laporan(dari: str = "", sampai: str = "", db: Session = Depends(get_db)):
    from datetime import datetime
    transaksi_list = db.query(models.Transaksi).order_by(models.Transaksi.id).all()
    dari_d = None
    sampai_d = None
    if dari:
        dari_d = datetime.strptime(dari, "%Y-%m-%d").date()
    if sampai:
        sampai_d = datetime.strptime(sampai, "%Y-%m-%d").date()
    lines = ["ID;Tanggal;Jam;Items;Total;Bayar;Kembalian"]
    for t in transaksi_list:
        d = t.dibuat.date()
        if dari_d and d < dari_d:
            continue
        if sampai_d and d > sampai_d:
            continue
        items = json.loads(t.items)
        items_str = ", ".join(
            str(i["nama"]) + " x" + str(i["jumlah"]) for i in items
        )
        lines.append(
            ";".join(
                [
                    str(t.id),
                    t.dibuat.strftime("%d/%m/%Y"),
                    t.dibuat.strftime("%H:%M"),
                    items_str,
                    str(int(t.total)),
                    str(int(t.bayar)),
                    str(int(t.kembalian)),
                ]
            )
        )
    content = "\ufeff" + "\n".join(lines)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=laporan-kasir.csv"},
    )

from datetime import date as tanggal_hari
from fastapi.responses import FileResponse

@app.get("/backup")
def backup_db():
    return FileResponse(
        "kasir.db",
        filename="backup-kasir-" + tanggal_hari.isoformat() + ".db",
        media_type="application/octet-stream",
    )
