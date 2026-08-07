import json
import random
import secrets
import string
from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.db import Base, engine, get_db

Base.metadata.create_all(bind=engine)
models.migrate_db()

app = FastAPI(title="Aplikasi Kasir")
templates = Jinja2Templates(directory="templates")

NAMA_TOKO = "MEKAR SARI"

app.mount("/static", StaticFiles(directory="static"), name="static")
templates.env.globals["nama_toko"] = NAMA_TOKO

USERS = {"admin": "1234", "kasir": "kasir123"}
SESSIONS = set()


class ItemKeranjang(BaseModel):
    produk_id: int
    jumlah: int


class TransaksiCreate(BaseModel):
    items: list[ItemKeranjang]
    bayar: float
    metode: str = "TUNAI"


def buat_kode_trx():
    acak = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return "RP-MKRS/" + datetime.now().strftime("%d%m%y") + "/" + acak


@app.middleware("http")
async def proteksi_login(request: Request, call_next):
    path = request.url.path
    publik = (
        path == "/login"
        or path == "/login/masuk"
        or path == "/favicon.ico"
        or path.startswith("/static")
    )
    if not publik:
        sid = request.cookies.get("session_id")
        if not sid or sid not in SESSIONS:
            return RedirectResponse("/login", status_code=303)
    return await call_next(request)


@app.get("/login")
def halaman_login(request: Request):
    return templates.TemplateResponse(request, "login.html", {"pesan": ""})


@app.post("/login/masuk")
def login_masuk(request: Request, username: str = Form(...), password: str = Form(...)):
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


@app.get("/")
def home():
    return RedirectResponse("/kasir", status_code=303)


@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    transaksi_list = db.query(models.Transaksi).all()
    omzet_hari_ini = 0.0
    transaksi_hari_ini = 0
    tunai_total = 0.0
    nontunai_total = 0.0
    for t in transaksi_list:
        if (t.metode or "TUNAI") == "TUNAI":
            tunai_total += t.total
        else:
            nontunai_total += t.total
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
            "tunai_total": tunai_total,
            "nontunai_total": nontunai_total,
            "top_produk": top_produk,
            "grafik": grafik,
            "max_total": max_total,
        },
    )


@app.get("/kasir")
def halaman_kasir(request: Request, db: Session = Depends(get_db)):
    produk_list = db.query(models.Produk).all()
    return templates.TemplateResponse(request, "kasir.html", {"produk_list": produk_list})


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
                "kode": t.kode_trx or ("TRX-" + str(t.id)),
                "metode": t.metode or "TUNAI",
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


@app.get("/struk/{trx_id}")
def struk_transaksi(request: Request, trx_id: int, db: Session = Depends(get_db)):
    trx = db.get(models.Transaksi, trx_id)
    if not trx:
        raise HTTPException(404, "Transaksi tidak ditemukan")
    return templates.TemplateResponse(
        request,
        "struk.html",
        {"trx": trx, "items": json.loads(trx.items)},
    )


@app.get("/manajemen")
def manajemen_produk(request: Request, db: Session = Depends(get_db)):
    produk_list = db.query(models.Produk).all()
    return templates.TemplateResponse(request, "manajemen.html", {"produk_list": produk_list})


@app.post("/produk/simpan")
def simpan_produk(
    nama: str = Form(...),
    harga: float = Form(...),
    stok: int = Form(...),
    kode: str = Form(""),
    kategori: str = Form(""),
    harga_modal: float = Form(0),
    db: Session = Depends(get_db),
):
    db.add(
        models.Produk(
            nama=nama, kode=kode, kategori=kategori,
            harga=harga, harga_modal=harga_modal, stok=stok,
        )
    )
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
    kode: str = Form(""),
    kategori: str = Form(""),
    harga_modal: float = Form(0),
    db: Session = Depends(get_db),
):
    produk = db.get(models.Produk, produk_id)
    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")
    produk.nama = nama
    produk.kode = kode
    produk.kategori = kategori
    produk.harga = harga
    produk.harga_modal = harga_modal
    produk.stok = stok
    db.commit()
    return RedirectResponse(url="/manajemen", status_code=303)


@app.post("/produk/hapus/{produk_id}")
def hapus_produk(produk_id: int, db: Session = Depends(get_db)):
    produk = db.get(models.Produk, produk_id)
    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")
    db.delete(produk)
    db.commit()
    return RedirectResponse(url="/manajemen", status_code=303)


@app.get("/produk", response_model=list[models.ProdukOut])
def daftar_produk(db: Session = Depends(get_db)):
    return db.query(models.Produk).all()


@app.post("/transaksi")
def buat_transaksi(t: TransaksiCreate, db: Session = Depends(get_db)):
    total = 0.0
    total_modal = 0.0
    detail = []
    for it in t.items:
        produk = db.get(models.Produk, it.produk_id)
        if not produk:
            raise HTTPException(404, "Produk tidak ditemukan")
        if produk.stok < it.jumlah:
            raise HTTPException(400, "Stok tidak cukup: " + produk.nama)
        subtotal = produk.harga * it.jumlah
        total_modal += (produk.harga_modal or 0.0) * it.jumlah
        total += subtotal
        detail.append({"nama": produk.nama, "jumlah": it.jumlah, "subtotal": subtotal})
    for it in t.items:
        produk = db.get(models.Produk, it.produk_id)
        produk.stok -= it.jumlah
    if t.metode == "TUNAI" and t.bayar < total:
        raise HTTPException(400, "Uang bayar kurang")
    trx = models.Transaksi(
        kode_trx=buat_kode_trx(),
        items=json.dumps(detail, ensure_ascii=False),
        total=total,
        total_modal=total_modal,
        bayar=t.bayar if t.metode == "TUNAI" else total,
        kembalian=(t.bayar - total) if t.metode == "TUNAI" else 0.0,
        metode=t.metode,
    )
    db.add(trx)
    db.commit()
    db.refresh(trx)
    return {"id": trx.id, "kode": trx.kode_trx, "total": total, "kembalian": trx.kembalian}


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


@app.get("/laporan/export")
def export_laporan(dari: str = "", sampai: str = "", db: Session = Depends(get_db)):
    transaksi_list = db.query(models.Transaksi).order_by(models.Transaksi.id).all()
    dari_d = None
    sampai_d = None
    if dari:
        dari_d = datetime.strptime(dari, "%Y-%m-%d").date()
    if sampai:
        sampai_d = datetime.strptime(sampai, "%Y-%m-%d").date()
    lines = ["ID;Kode;Tanggal;Jam;Metode;Items;Total;Bayar;Kembalian"]
    for t in transaksi_list:
        d = t.dibuat.date()
        if dari_d and d < dari_d:
            continue
        if sampai_d and d > sampai_d:
            continue
        items = json.loads(t.items)
        items_str = ", ".join(str(i["nama"]) + " x" + str(i["jumlah"]) for i in items)
        lines.append(
            ";".join(
                [
                    str(t.id),
                    t.kode_trx or "",
                    t.dibuat.strftime("%d/%m/%Y"),
                    t.dibuat.strftime("%H:%M"),
                    t.metode or "TUNAI",
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


@app.get("/labarugi")
def labarugi(request: Request, dari: str = "", sampai: str = "", db: Session = Depends(get_db)):
    dari_d = None
    sampai_d = None
    if dari:
        dari_d = datetime.strptime(dari, "%Y-%m-%d").date()
    if sampai:
        sampai_d = datetime.strptime(sampai, "%Y-%m-%d").date()
    rekap = {}
    for t in db.query(models.Transaksi).all():
        d = t.dibuat.date()
        if dari_d and d < dari_d:
            continue
        if sampai_d and d > sampai_d:
            continue
        r = rekap.setdefault(
            d,
            {"tanggal": d.strftime("%d/%m/%Y"), "omzet": 0.0, "modal": 0.0, "pengeluaran": 0.0, "key": d},
        )
        r["omzet"] += t.total
        r["modal"] += t.total_modal or 0.0
    for p in db.query(models.Pengeluaran).all():
        d = p.dibuat.date()
        if dari_d and d < dari_d:
            continue
        if sampai_d and d > sampai_d:
            continue
        r = rekap.setdefault(
            d,
            {"tanggal": d.strftime("%d/%m/%Y"), "omzet": 0.0, "modal": 0.0, "pengeluaran": 0.0, "key": d},
        )
        r["pengeluaran"] += p.jumlah
    rows = sorted(rekap.values(), key=lambda x: x["key"], reverse=True)
    for r in rows:
        r["laba"] = r["omzet"] - r["modal"] - r["pengeluaran"]
    return templates.TemplateResponse(
        request, "labarugi.html", {"rows": rows, "dari": dari, "sampai": sampai}
    )


@app.post("/pengeluaran")
def tambah_pengeluaran(
    keterangan: str = Form(...),
    jumlah: float = Form(...),
    db: Session = Depends(get_db),
):
    db.add(models.Pengeluaran(keterangan=keterangan, jumlah=jumlah))
    db.commit()
    return RedirectResponse("/labarugi", status_code=303)


@app.get("/tutup")
def halaman_tutup(request: Request, db: Session = Depends(get_db)):
    tunai_sistem = 0.0
    nontunai_sistem = 0.0
    for t in db.query(models.Transaksi).all():
        if t.dibuat and t.dibuat.date() == date.today():
            if (t.metode or "TUNAI") == "TUNAI":
                tunai_sistem += t.total
            else:
                nontunai_sistem += t.total
    riwayat_tutup = db.query(models.TutupKasir).order_by(models.TutupKasir.id.desc()).all()
    return templates.TemplateResponse(
        request,
        "tutup.html",
        {
            "tunai_sistem": tunai_sistem,
            "nontunai_sistem": nontunai_sistem,
            "riwayat_tutup": riwayat_tutup,
        },
    )


@app.post("/tutup")
def proses_tutup(
    nontunai_input: float = Form(...),
    tunai_input: float = Form(0),
    db: Session = Depends(get_db),
):
    tunai_sistem = 0.0
    nontunai_sistem = 0.0
    for t in db.query(models.Transaksi).all():
        if t.dibuat and t.dibuat.date() == date.today():
            if (t.metode or "TUNAI") == "TUNAI":
                tunai_sistem += t.total
            else:
                nontunai_sistem += t.total
    db.add(
        models.TutupKasir(
            tanggal=date.today().isoformat(),
            tunai_sistem=tunai_sistem,
            tunai_input=tunai_input,
            tunai_selisih=tunai_input - tunai_sistem,
            nontunai_sistem=nontunai_sistem,
            nontunai_input=nontunai_input,
            nontunai_selisih=nontunai_input - nontunai_sistem,
        )
    )
    db.commit()
    return RedirectResponse("/tutup", status_code=303)


@app.get("/backup")
def backup_db():
    return FileResponse(
        "kasir.db",
        filename="backup-kasir-" + date.today().isoformat() + ".db",
        media_type="application/octet-stream",
    )
