import json
import re
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
from app.notes_data import N
from app.gender_data import G
from app.db import Base, SessionLocal, engine, get_db

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
    diskon: float = 0.0


class TransaksiCreate(BaseModel):
    items: list[ItemKeranjang]
    bayar: float = 0.0
    metode: str = "TUNAI"
    channel: str = ""
    tunai: float = 0.0
    diskon_total: float = 0.0


def buat_kode_trx():
    acak = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return "RP-MKRS/" + datetime.now().strftime("%d%m%y") + "/" + acak


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


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
        if not sid or not sesi_valid(sid):
            return RedirectResponse("/login", status_code=303)
    return await call_next(request)


@app.get("/login")
def halaman_login(request: Request):
    return templates.TemplateResponse(request, "login.html", {"pesan": ""})


@app.post("/login/masuk")
def login_masuk(request: Request, username: str = Form(...), password: str = Form(...)):
    if USERS.get(username) == password:
        sid = secrets.token_hex(16)
        dbx = SessionLocal()
        dbx.add(models.Sesi(token=sid))
        dbx.commit()
        dbx.close()
        resp = RedirectResponse("/dashboard", status_code=303)
        resp.set_cookie("session_id", sid, max_age=604800)
        return resp
    return templates.TemplateResponse(
        request, "login.html", {"pesan": "Username atau password salah"}
    )


@app.get("/logout")
def logout(request: Request):
    sid = request.cookies.get("session_id")
    dbx = SessionLocal()
    dbx.query(models.Sesi).filter_by(token=sid).delete()
    dbx.commit()
    dbx.close()
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("session_id")
    return resp


@app.get("/")
def home():
    return RedirectResponse("/kasir", status_code=303)


@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    mode = request.query_params.get("mode", "7")
    dari_s = request.query_params.get("dari", "")
    sampai_s = request.query_params.get("sampai", "")
    transaksi_list = db.query(models.Transaksi).all()
    omzet_hari_ini = 0.0
    transaksi_hari_ini = 0
    tunai_total = 0.0
    nontunai_total = 0.0
    for t in transaksi_list:
        tunai_total += t.p_tunai or 0.0
        nontunai_total += t.p_nontunai or 0.0
        if t.dibuat and t.dibuat.date() == today:
            omzet_hari_ini += t.total
            transaksi_hari_ini += 1
    days = []
    if mode == "harian":
        days = [today]
    elif mode == "custom":
        d1 = parse_date(dari_s) or today
        d2 = parse_date(sampai_s) or today
        if d1 > d2:
            d1, d2 = d2, d1
        d = d1
        while d <= d2 and len(days) < 120:
            days.append(d)
            d += timedelta(days=1)
    else:
        n = 7
        if mode in ("30", "90"):
            n = int(mode)
        days = [today - timedelta(days=i) for i in range(n - 1, -1, -1)]
    grafik = []
    for d in days:
        total = sum(t.total for t in transaksi_list if t.dibuat and t.dibuat.date() == d)
        grafik.append({"label": d.strftime("%d/%m"), "total": total})
    max_total = max([g["total"] for g in grafik] + [1])
    month_start = today.replace(day=1)
    kat_map = {}
    for p in db.query(models.Produk).all():
        kat_map[p.nama] = p.kategori or ""
    terlaris = {}
    for t in transaksi_list:
        if t.dibuat and t.dibuat.date() >= month_start:
            for it in json.loads(t.items):
                if kat_map.get(it["nama"]) == "BIBIT":
                    terlaris[it["nama"]] = terlaris.get(it["nama"], 0) + it["jumlah"]
    top_produk = sorted(terlaris.items(), key=lambda x: x[1], reverse=True)[:10]
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
            "saran_list": buat_saran(db),
            "mode": mode,
            "dari": dari_s,
            "sampai": sampai_s,
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
    total_before = 0.0
    total_modal = 0.0
    total_diskon = t.diskon_total or 0.0
    detail = []
    for it in t.items:
        produk = db.get(models.Produk, it.produk_id)
        if not produk:
            raise HTTPException(404, "Produk tidak ditemukan")
        if produk.stok < it.jumlah:
            raise HTTPException(400, "Stok tidak cukup: " + produk.nama)
        subtotal = produk.harga * it.jumlah
        total_before += subtotal
        total_modal += (produk.harga_modal or 0.0) * it.jumlah
        total_diskon += it.diskon or 0.0
        detail.append(
            {"nama": produk.nama, "jumlah": it.jumlah, "subtotal": subtotal, "diskon": it.diskon or 0.0}
        )
    total = max(0.0, total_before - total_diskon)
    for it in t.items:
        produk = db.get(models.Produk, it.produk_id)
        produk.stok -= it.jumlah
    if t.metode == "TUNAI":
        tunai = t.tunai if t.tunai else t.bayar
        if tunai < total:
            raise HTTPException(400, "Uang bayar kurang")
        p_tunai, p_nontunai = total, 0.0
        kembalian = tunai - total
        label = "TUNAI"
    elif t.metode == "SPLIT":
        tunai = t.tunai
        if tunai <= 0 or tunai >= total:
            raise HTTPException(400, "Isi tunai harus di antara 0 dan total")
        p_tunai, p_nontunai = tunai, total - tunai
        kembalian = 0.0
        label = "SPLIT (" + t.channel + ")"
    else:
        tunai = total
        p_tunai, p_nontunai = 0.0, total
        kembalian = 0.0
        label = "NON-TUNAI (" + t.channel + ")"
    trx = models.Transaksi(
        kode_trx=buat_kode_trx(),
        items=json.dumps(detail, ensure_ascii=False),
        total=total,
        total_modal=total_modal,
        total_diskon=total_diskon,
        bayar=tunai,
        kembalian=kembalian,
        metode=label,
        p_tunai=p_tunai,
        p_nontunai=p_nontunai,
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
    dari_d = parse_date(dari)
    sampai_d = parse_date(sampai)
    lines = ["ID;Kode;Tanggal;Jam;Metode;Items;Total;Diskon;Bayar;Kembalian"]
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
                    str(int(t.total_diskon or 0)),
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
    dari_d = parse_date(dari)
    sampai_d = parse_date(sampai)
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
    tot_omzet = 0.0
    tot_modal = 0.0
    tot_pengeluaran = 0.0
    for r in rows:
        r["laba"] = r["omzet"] - r["modal"] - r["pengeluaran"]
        tot_omzet += r["omzet"]
        tot_modal += r["modal"]
        tot_pengeluaran += r["pengeluaran"]
    tot_laba = tot_omzet - tot_modal - tot_pengeluaran
    bulan = {}
    for t in db.query(models.Transaksi).all():
        key = t.dibuat.strftime("%Y-%m")
        b = bulan.setdefault(key, {"bulan": key, "omzet": 0.0, "modal": 0.0, "pengeluaran": 0.0})
        b["omzet"] += t.total
        b["modal"] += t.total_modal or 0.0
    for p in db.query(models.Pengeluaran).all():
        key = p.dibuat.strftime("%Y-%m")
        b = bulan.setdefault(key, {"bulan": key, "omzet": 0.0, "modal": 0.0, "pengeluaran": 0.0})
        b["pengeluaran"] += p.jumlah
    bulan_list = sorted(bulan.values(), key=lambda x: x["bulan"], reverse=True)
    for b in bulan_list:
        b["laba"] = b["omzet"] - b["modal"] - b["pengeluaran"]
        b["margin"] = (b["laba"] / b["omzet"] * 100) if b["omzet"] else 0.0
    return templates.TemplateResponse(
        request,
        "labarugi.html",
        {
            "rows": rows,
            "dari": dari,
            "sampai": sampai,
            "tot_omzet": tot_omzet,
            "tot_modal": tot_modal,
            "tot_pengeluaran": tot_pengeluaran,
            "tot_laba": tot_laba,
            "bulan_list": bulan_list,
        },
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
            tunai_sistem += t.p_tunai or 0.0
            nontunai_sistem += t.p_nontunai or 0.0
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
            tunai_sistem += t.p_tunai or 0.0
            nontunai_sistem += t.p_nontunai or 0.0
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


def sesi_valid(token):
    dbx = SessionLocal()
    try:
        return dbx.query(models.Sesi).filter_by(token=token).first() is not None
    finally:
        dbx.close()


def buat_saran(db):
    saran = []
    today = date.today()
    produk_list = db.query(models.Produk).all()
    transaksi_list = db.query(models.Transaksi).all()
    month_start = today.replace(day=1)
    habis = [p for p in produk_list if (p.stok or 0) == 0]
    if habis:
        names = ", ".join(p.nama for p in habis[:4])
        saran.append(("warning", str(len(habis)) + " produk STOK HABIS (misal: " + names + "). Segera restock agar tidak kehilangan penjualan."))
    rendah = [p for p in produk_list if 0 < (p.stok or 0) < 10]
    if rendah:
        names = ", ".join(p.nama for p in rendah[:4])
        saran.append(("info", str(len(rendah)) + " produk stok menipis (<10): " + names + ". Pertimbangkan restock."))
    terjual = {}
    for t in transaksi_list:
        if t.dibuat and t.dibuat.date() >= month_start:
            for it in json.loads(t.items):
                terjual[it["nama"]] = terjual.get(it["nama"], 0) + it["jumlah"]
    if terjual:
        top_nama, top_qty = sorted(terjual.items(), key=lambda x: x[1], reverse=True)[0]
        p = next((x for x in produk_list if x.nama == top_nama), None)
        if p:
            if (p.stok or 0) < top_qty:
                saran.append(("warning", "Produk terlaris bulan ini " + top_nama + " (" + str(top_qty) + " terjual) stoknya tinggal " + str(p.stok) + ". Restock segera!"))
            else:
                saran.append(("success", "Produk terlaris bulan ini: " + top_nama + " (" + str(top_qty) + " terjual). Stok " + str(p.stok) + " masih aman."))
    omzet_7 = sum(t.total for t in transaksi_list if t.dibuat and today - timedelta(days=6) <= t.dibuat.date() <= today)
    omzet_7p = sum(t.total for t in transaksi_list if t.dibuat and today - timedelta(days=13) <= t.dibuat.date() <= today - timedelta(days=7))
    if omzet_7p > 0:
        diff = (omzet_7 - omzet_7p) / omzet_7p * 100
        if diff >= 10:
            saran.append(("success", "Omzet 7 hari terakhir naik " + str(int(diff)) + "% dibanding minggu sebelumnya. Pertahankan!"))
        elif diff <= -10:
            saran.append(("warning", "Omzet 7 hari terakhir turun " + str(int(abs(diff))) + "%. Coba promo bundling parfum BIBIT atau diskon qty."))
        else:
            saran.append(("info", "Omzet 7 hari terakhir stabil dibanding minggu sebelumnya."))
    tunai = sum(t.p_tunai or 0 for t in transaksi_list)
    nontunai = sum(t.p_nontunai or 0 for t in transaksi_list)
    tot = tunai + nontunai
    if tot > 0:
        pct_non = nontunai / tot * 100
        if pct_non >= 60:
            saran.append(("info", str(int(pct_non)) + "% pembayaran NON-TUNAI. Pastikan cek mutasi QRIS setiap tutup kasir."))
        else:
            saran.append(("info", str(int(100 - pct_non)) + "% pembayaran TUNAI. Siapkan pecahan kecil untuk kembalian."))
    omzet_b = 0.0
    modal_b = 0.0
    for t in transaksi_list:
        if t.dibuat and t.dibuat.date() >= month_start:
            omzet_b += t.total
            modal_b += t.total_modal or 0.0
    if omzet_b > 0:
        margin = (omzet_b - modal_b) / omzet_b * 100
        if margin < 40:
            saran.append(("warning", "Margin bulan ini " + str(int(margin)) + "% (rendah). Tinjau harga jual parfum dengan modal tinggi."))
        else:
            saran.append(("success", "Margin keuntungan bulan ini sehat: " + str(int(margin)) + "%."))
    sold_names = set()
    for t in transaksi_list:
        for it in json.loads(t.items):
            sold_names.add(it["nama"])
    never = [p for p in produk_list if p.nama not in sold_names and (p.stok or 0) > 0]
    if never:
        saran.append(("info", str(len(never)) + " produk belum pernah terjual (misal: " + ", ".join(p.nama for p in never[:3]) + "). Coba pajang di etalase depan atau beri diskon."))
    selisih_neg = db.query(models.TutupKasir).filter(models.TutupKasir.nontunai_selisih < 0).count()
    if selisih_neg:
        saran.append(("warning", "Ada " + str(selisih_neg) + " tutup kasir dengan selisih NON-TUNAI minus. Periksa kembali mutasi QRIS."))
    if not saran:
        saran.append(("success", "Semua indikator bagus. Pertahankan!"))
    return saran

def hitung_range(d1, d2, transaksi_list, pengeluaran_list):
    omzet = 0.0
    modal = 0.0
    keluar = 0.0
    for t in transaksi_list:
        if t.dibuat and d1 <= t.dibuat.date() <= d2:
            omzet += t.total
            modal += t.total_modal or 0.0
    for p in pengeluaran_list:
        if d1 <= p.dibuat.date() <= d2:
            keluar += p.jumlah
    laba = omzet - modal - keluar
    margin = (laba / omzet * 100) if omzet else 0.0
    return omzet, modal, keluar, laba, margin


def rp(x):
    return "Rp " + format(int(round(x)), ",").replace(",", ".")


def jawab_ai(q, db):
    q = (q or "").lower()
    today = date.today()
    transaksi_list = db.query(models.Transaksi).all()
    pengeluaran_list = db.query(models.Pengeluaran).all()
    produk_list = db.query(models.Produk).all()
    bibit = [p for p in produk_list if (p.kategori or "") == "BIBIT"]
    nama_bibit = set(p.nama for p in bibit)
    if "notes" in q or "aroma" in q or "wangi" in q:
        t2 = cari_produk(q, produk_list)
        if t2:
            return t2.nama + ":\n" + (N.get(t2.nama) or "Data notes belum ada untuk produk ini.")
        return "Produk tidak ditemukan. Contoh pertanyaan: notes AFNAN - 9PM"
    if "laris" in q:
        hit = {}
        for t in transaksi_list:
            if t.dibuat and t.dibuat.date() == today:
                for it in json.loads(t.items):
                    if it["nama"] in nama_bibit and boleh(it["nama"], q):
                        hit[it["nama"]] = hit.get(it["nama"], 0) + it["jumlah"]
        if hit:
            top = sorted(hit.items(), key=lambda x: x[1], reverse=True)[:5]
            return "Laris hari ini (BIBIT):\n" + "\n".join(str(i + 1) + ". " + n + " (" + str(v) + " terjual)" for i, (n, v) in enumerate(top))
        return "Belum ada penjualan BIBIT hari ini.\nCoba tawarkan:\n" + "\n".join(str(i + 1) + ". " + p.nama for i, p in enumerate(bibit[:3]))
    if "harus terjual" in q or "rekomendasi" in q or "jual hari ini" in q or "apa yang harus" in q:
        month_start = today.replace(day=1)
        hit = {}
        for t in transaksi_list:
            if t.dibuat and t.dibuat.date() >= month_start:
                for it in json.loads(t.items):
                    if it["nama"] in nama_bibit and boleh(it["nama"], q):
                        hit[it["nama"]] = hit.get(it["nama"], 0) + it["jumlah"]
        terlaris = sorted(hit.items(), key=lambda x: x[1], reverse=True)[:3]
        margin_top = sorted(bibit, key=lambda p: p.harga - (p.harga_modal or 0), reverse=True)[:3]
        j = "Fokus jual hari ini (BIBIT):"
        if terlaris:
            j += "\nLaris bulan ini:\n" + "\n".join(str(i + 1) + ". " + n + " (" + str(v) + " terjual)" for i, (n, v) in enumerate(terlaris))
        j += "\nUntung terbesar per pcs:\n" + "\n".join(str(i + 1) + ". " + p.nama + " (" + rp(p.harga - (p.harga_modal or 0)) + ")" for i, p in enumerate(margin_top))
        return j
    period = None
    if "harian" in q or "hari ini" in q:
        period = "harian"
    elif "mingguan" in q or "minggu" in q:
        period = "mingguan"
    elif "bulanan" in q or "bulan" in q:
        period = "bulanan"
    elif "tahunan" in q or "tahun" in q:
        period = "tahunan"
    topics = []
    if "omzet" in q or "omset" in q or "penjualan" in q:
        topics.append("omzet")
    if "untung" in q or "laba" in q or "keuntungan" in q:
        topics.append("laba")
    if "modal" in q:
        topics.append("modal")
    if "margin" in q:
        topics.append("margin")
    if not topics:
        topics = ["omzet", "modal", "laba", "margin"]
    periods = [period] if period else ["harian", "mingguan", "bulanan", "tahunan"]
    lines = []
    for per in periods:
        if per == "harian":
            d1 = today
            label = "hari ini"
        elif per == "mingguan":
            d1 = today - timedelta(days=6)
            label = "7 hari terakhir"
        elif per == "bulanan":
            d1 = today.replace(day=1)
            label = "bulan ini"
        else:
            d1 = today.replace(month=1, day=1)
            label = "tahun ini"
        omzet, modal, keluar, laba, margin = hitung_range(d1, today, transaksi_list, pengeluaran_list)
        parts = []
        if "omzet" in topics:
            parts.append("omzet " + rp(omzet))
        if "modal" in topics:
            parts.append("modal " + rp(modal))
        if "laba" in topics:
            parts.append("keuntungan " + rp(laba))
        if "margin" in topics:
            parts.append("margin " + str(int(margin)) + "%")
        lines.append(label + ": " + ", ".join(parts))
    return "\n".join(lines)


@app.get("/ai")
def halaman_ai(request: Request):
    return templates.TemplateResponse(request, "ai.html", {})


@app.get("/ai/jawab")
def ai_jawab(q: str, db: Session = Depends(get_db)):
    return {"jawab": jawab_ai2(q, db)}






def jawab_ai2(q, db):
    ql = (q or "").lower()
    transaksi_list = db.query(models.Transaksi).all()
    produk_list = db.query(models.Produk).all()
    pengeluaran_list = db.query(models.Pengeluaran).all()
    terjual = {}
    for t in transaksi_list:
        for it in json.loads(t.items):
            terjual[it["nama"]] = terjual.get(it["nama"], 0) + it["jumlah"]
    if "mirip" in ql or "serupa" in ql or "menyerupai" in ql:
        target = cari_produk(ql, produk_list)
        if not target:
            return "Sebutkan nama parfumnya. Contoh: yang mirip sauvage"
        my_notes = (N.get(target.nama) or "").lower()
        tokens = set(w for w in re.split("[^a-z]+", my_notes) if len(w) > 3)
        scores = []
        for p in produk_list:
            if p.nama == target.nama:
                continue
            other = (N.get(p.nama) or "").lower()
            if not other:
                continue
            ot = set(w for w in re.split("[^a-z]+", other) if len(w) > 3)
            common = len(tokens & ot)
            if common > 0:
                scores.append((common, p))
        scores.sort(key=lambda x: x[0], reverse=True)
        top = scores[:5]
        if not top:
            return "Tidak ditemukan parfum mirip " + target.nama + "."
        out = "Mirip " + target.nama + ":\n"
        for i, (s, p) in enumerate(top):
            out += str(i + 1) + ". " + p.nama + " (" + G.get(p.nama, "unisex") + ")\n"
        return out
    target = cari_produk(ql, produk_list)
    if target and not ("notes" in ql or "aroma" in ql or "wangi" in ql):
        if "stok" in ql or "sisa" in ql or "tersisa" in ql:
            return "Stok " + target.nama + ": " + str(target.stok or 0)
        if "modal" in ql or "grosir" in ql:
            return "Harga modal " + target.nama + ": " + rp(target.harga_modal or 0)
        if "jual" in ql or "pasaran" in ql:
            return "Harga jual " + target.nama + ": " + rp(target.harga)
        if "untung" in ql or "laba" in ql:
            return "Untung per pcs " + target.nama + ": " + rp(target.harga - (target.harga_modal or 0))
        if "kode" in ql or "pabrik" in ql or "brand" in ql:
            return "Kode / pabrik " + target.nama + ": " + (target.kode or "-")
        if "gender" in ql or "untuk siapa" in ql:
            return target.nama + " untuk: " + G.get(target.nama, "unisex")
        if "kategori" in ql:
            return "Kategori " + target.nama + ": " + (target.kategori or "-")
        g = G.get(target.nama, "-")
        nts = N.get(target.nama, "")
        out = target.nama + "\n"
        out += "Kode / pabrik: " + (target.kode or "-") + "\n"
        out += "Kategori: " + (target.kategori or "-") + "\n"
        out += "Gender: " + g + "\n"
        out += "Harga modal: " + rp(target.harga_modal or 0) + "\n"
        out += "Harga jual: " + rp(target.harga) + "\n"
        out += "Untung per pcs: " + rp(target.harga - (target.harga_modal or 0)) + "\n"
        out += "Stok sekarang: " + str(target.stok or 0) + "\n"
        out += "Terjual: " + str(terjual.get(target.nama, 0))
        if nts:
            out += "\nNotes: " + nts
        return out
    if "kode" in ql or "pabrik" in ql or "brand" in ql or "dari apa" in ql:
        codes = set((p.kode or "").lower() for p in produk_list if p.kode)
        found = None
        for kod in codes:
            if re.search(r"\b" + re.escape(kod) + r"\b", ql):
                found = kod
                break
        if found:
            pool = [p for p in produk_list if (p.kode or "").lower() == found]
            pool = acak(pilih_pool(pool, ql), 15)
            if pool:
                return "Produk kode " + found.upper() + ":\n" + "\n".join(str(i + 1) + ". " + p.nama + " (stok " + str(p.stok or 0) + ")" for i, p in enumerate(pool))
    if "stok" in ql:
        if "kosong" in ql or "habis" in ql:
            pool = acak([p for p in produk_list if (p.stok or 0) == 0 and boleh(p.nama, ql)], 10)
            if pool:
                return "Stok kosong:\n" + "\n".join(str(i + 1) + ". " + p.nama for i, p in enumerate(pool))
            return "Tidak ada stok kosong."
        if "menipis" in ql or "hampir" in ql or "20" in ql:
            pool = acak([p for p in produk_list if 0 < (p.stok or 0) < 20 and boleh(p.nama, ql)], 10)
            if pool:
                return "Stok hampir habis (<20):\n" + "\n".join(str(i + 1) + ". " + p.nama + " (stok " + str(p.stok or 0) + ")" for i, p in enumerate(pool))
            return "Tidak ada stok di bawah 20."
    if ("omzet" in ql or "omset" in ql) and ("hari ini" in ql or "sekarang" in ql):
        tot = 0.0
        tun = 0.0
        non = 0.0
        for t in transaksi_list:
            if t.dibuat and t.dibuat.date() == date.today():
                tot += t.total
                tun += t.p_tunai or 0.0
                non += t.p_nontunai or 0.0
        return "Omzet hari ini:\n" + rp(tot) + "\nQRIS " + rp(non) + "\nTunai " + rp(tun)
    if "harus" in ql and ("jual" in ql or "terjual" in ql):
        out = "Produk yang harus dijual hari ini:\nPEREMPUAN:\n"
        pool_w = pilih_pool([p for p in produk_list if G.get(p.nama, "").startswith("wanita") or G.get(p.nama, "").startswith("unisex")], ql)
        sold_w = sorted([p for p in pool_w if terjual.get(p.nama, 0) > 0], key=lambda p: terjual[p.nama], reverse=True)[:5]
        never_w = daftar_belum_terjual(pool_w, terjual, 5)
        i = 0
        for p in sold_w + never_w:
            i += 1
            out += str(i) + ". " + p.nama + "\n"
        out += "LAKI-LAKI:\n"
        pool_m = pilih_pool([p for p in produk_list if G.get(p.nama, "").startswith("pria") or G.get(p.nama, "").startswith("unisex")], ql)
        sold_m = sorted([p for p in pool_m if terjual.get(p.nama, 0) > 0], key=lambda p: terjual[p.nama], reverse=True)[:5]
        never_m = daftar_belum_terjual(pool_m, terjual, 5)
        i = 0
        for p in sold_m + never_m:
            i += 1
            out += str(i) + ". " + p.nama + "\n"
        return out
    if "laris" in ql and ("habis" in ql or "menipis" in ql or "hampir" in ql):
        low = [p for p in produk_list if terjual.get(p.nama, 0) > 0 and (p.stok or 0) < 10 and boleh(p.nama, ql)]
        low.sort(key=lambda p: terjual[p.nama], reverse=True)
        if not low:
            return "Tidak ada produk laris yang hampir habis. Stok aman."
        out = "Laris tetapi hampir habis / habis:\n"
        out += "\n".join(str(i + 1) + ". " + p.nama + " (terjual " + str(terjual[p.nama]) + ", stok " + str(p.stok) + ")" for i, p in enumerate(low[:10]))
        return out
    if ("laba" in ql or "untung" in ql or "keuntungan" in ql) and ("hari ini" in ql or "sekarang" in ql):
        omzet = 0.0
        modal = 0.0
        keluar = 0.0
        for t in transaksi_list:
            if t.dibuat and t.dibuat.date() == date.today():
                omzet += t.total
                modal += t.total_modal or 0.0
        for p in pengeluaran_list:
            if p.dibuat.date() == date.today():
                keluar += p.jumlah
        laba = omzet - modal - keluar
        return "Laba hari ini:\nOmzet " + rp(omzet) + "\nModal " + rp(modal) + "\nPengeluaran " + rp(keluar) + "\nKeuntungan " + rp(laba)
    if ("laba" in ql or "untung" in ql or "keuntungan" in ql or "margin" in ql) and "bulan" in ql:
        month_start = date.today().replace(day=1)
        omzet = 0.0
        modal = 0.0
        keluar = 0.0
        for t in transaksi_list:
            if t.dibuat and t.dibuat.date() >= month_start:
                omzet += t.total
                modal += t.total_modal or 0.0
        for p in pengeluaran_list:
            if p.dibuat.date() >= month_start:
                keluar += p.jumlah
        laba = omzet - modal - keluar
        margin = (laba / omzet * 100) if omzet else 0.0
        return "Laba bulan ini:\nOmzet " + rp(omzet) + "\nModal " + rp(modal) + "\nPengeluaran " + rp(keluar) + "\nKeuntungan " + rp(laba) + "\nMargin " + str(int(margin)) + "%"
    if "tidak laku" in ql or "stok banyak" in ql or "dead" in ql:
        dead = [p for p in produk_list if terjual.get(p.nama, 0) == 0 and (p.stok or 0) >= 50 and G.get(p.nama, "") not in ("", "-") and boleh(p.nama, ql)]
        dead.sort(key=lambda p: p.stok or 0, reverse=True)
        if not dead:
            return "Tidak ada dead stock. Semua stok bergerak."
        out = "Stok banyak tapi belum laku (beri promo!):\n"
        out += "\n".join(str(i + 1) + ". " + p.nama + " (stok " + str(p.stok) + ")" for i, p in enumerate(acak(dead, 10)))
        return out
    if "terlaris" in ql or "best seller" in ql or "bestseller" in ql:
        month_start = date.today().replace(day=1)
        hit = {}
        for t in transaksi_list:
            if t.dibuat and t.dibuat.date() >= month_start:
                for it in json.loads(t.items):
                    if boleh(it["nama"], ql):
                        hit[it["nama"]] = hit.get(it["nama"], 0) + it["jumlah"]
        top = sorted(hit.items(), key=lambda x: x[1], reverse=True)[:5]
        if not top:
            return "Belum ada penjualan bulan ini."
        return "Top 5 terlaris bulan ini:\n" + "\n".join(str(i + 1) + ". " + n + " (" + str(v) + " terjual)" for i, (n, v) in enumerate(top))
    if "naik" in ql or "turun" in ql or ("minggu" in ql and ("omzet" in ql or "omset" in ql)):
        today = date.today()
        omzet_7 = sum(t.total for t in transaksi_list if t.dibuat and today - timedelta(days=6) <= t.dibuat.date() <= today)
        omzet_7p = sum(t.total for t in transaksi_list if t.dibuat and today - timedelta(days=13) <= t.dibuat.date() <= today - timedelta(days=7))
        if omzet_7p > 0:
            diff = (omzet_7 - omzet_7p) / omzet_7p * 100
            arah = "NAIK" if diff >= 0 else "TURUN"
            return "Omzet 7 hari: " + rp(omzet_7) + "\n7 hari sebelumnya: " + rp(omzet_7p) + "\nHasil: " + arah + " " + str(int(abs(diff))) + "%"
        return "Omzet 7 hari: " + rp(omzet_7) + "\n(Belum ada data minggu sebelumnya.)"
    if "qris" in ql or "non tunai" in ql:
        month_start = date.today().replace(day=1)
        non = 0.0
        tun = 0.0
        for t in transaksi_list:
            if t.dibuat and t.dibuat.date() >= month_start:
                non += t.p_nontunai or 0.0
                tun += t.p_tunai or 0.0
        return "Bulan ini:\nQRIS / NON-TUNAI " + rp(non) + "\nTUNAI " + rp(tun) + "\n(Samakan angka QRIS dengan mutasi rekening Anda.)"
    if "restock" in ql or "stok menipis" in ql:
        low = [p for p in produk_list if (p.stok or 0) < 10 and boleh(p.nama, ql)]
        low.sort(key=lambda p: p.stok or 0)
        if not low:
            return "Semua stok aman. Tidak perlu restock."
        return "Perlu restock (stok < 10):\n" + "\n".join(str(i + 1) + ". " + p.nama + " (stok " + str(p.stok) + ")" for i, p in enumerate(low[:10]))
    male_kw = ["pria", "cowok", "cowo", "cwok", "laki", "bujang"]
    female_kw = ["wanita", "perempuan", "cewek", "cewe", "cwek", "cwe", "gadis"]
    is_male = any(k in ql for k in male_kw)
    is_female = any(k in ql for k in female_kw)
    if (is_male or is_female) and ("parfum" in ql or "apa" in ql):
        gender = "pria" if is_male else "wanita"
        pool = pilih_pool([p for p in produk_list if G.get(p.nama, "").startswith(gender) or G.get(p.nama, "").startswith("unisex")], ql)
        if "anak" in ql or "bayi" in ql or "remaja" in ql:
            pool2 = [p for p in pool if any(a in G.get(p.nama, "") for a in ["anak", "bayi", "remaja"])]
            if pool2:
                pool = pool2
        sold = sorted([p for p in pool if terjual.get(p.nama, 0) > 0], key=lambda p: terjual[p.nama], reverse=True)[:5]
        never = daftar_belum_terjual(pool, terjual, 5)
        out = "Parfum " + gender.upper() + ":\nBest seller:\n"
        if sold:
            out += "\n".join(str(i + 1) + ". " + p.nama + " (" + str(terjual[p.nama]) + " terjual)" for i, p in enumerate(sold))
        else:
            out += "(belum ada yang terjual)"
        out += "\nBelum pernah terjual:\n"
        if never:
            out += "\n".join(str(i + 1) + ". " + p.nama for i, p in enumerate(never))
        else:
            out += "(semua sudah terjual)"
        return out
    if "notes" in ql or "note" in ql or "aroma" in ql or "wangi" in ql or "parfum" in ql or "parfume" in ql:
        has_name = ("apa saja" not in ql) and cari_produk(ql, produk_list) is not None
        if not has_name:
            clean = ql
            for w in ["parfume", "parfum", "notes", "note", "aroma", "wangi", "apa", "saja", "yang", "ini", "dengan", "laris", "terlaris", "hari", "bulan", "minggu", "?"]:
                clean = clean.replace(w, "")
            clean = clean.strip()
            if clean:
                terms = NOTE_SYNONYMS.get(clean, [clean])
                cands = [p for p in produk_list if any(tm in (N.get(p.nama) or "").lower() for tm in terms) and G.get(p.nama, "") not in ("", "-")]
                if cands:
                    cands = pilih_pool(cands, ql)
                    best = sorted([p for p in cands if terjual.get(p.nama, 0) > 0], key=lambda p: terjual[p.nama], reverse=True)[:3]
                    never = acak([p for p in cands if terjual.get(p.nama, 0) == 0], 3)
                    women = acak([p for p in cands if G.get(p.nama, "").startswith("wanita")], 2)
                    men = acak([p for p in cands if G.get(p.nama, "").startswith("pria")], 2)
                    seen = set()
                    final = []
                    for p in best + never + women + men:
                        if p.nama not in seen:
                            seen.add(p.nama)
                            final.append(p)
                    final = final[:10]
                    out = "Parfum dengan notes '" + clean + "':\n"
                    out += "\n".join(str(i + 1) + ". " + p.nama + " (" + G.get(p.nama, "unisex") + ", " + str(terjual.get(p.nama, 0)) + " terjual)" for i, p in enumerate(final))
                    return out
                return "Tidak ditemukan parfum dengan notes: " + clean + ".\nCoba kata lain: vanilla, musk, oud, mawar, kayu manis, citrus, kelapa, kopi, cokelat."
    return jawab_ai(q, db)


def daftar_belum_terjual(pool, terjual, n):
    never = [p for p in pool if terjual.get(p.nama, 0) == 0]
    if not never:
        return []
    return random.sample(never, min(n, len(never)))


NOTE_SYNONYMS = {
    "cinnamon": ["kayu manis", "cinnamon"],
    "vanilla": ["vanilla", "vanili"],
    "rose": ["mawar", "rose"],
    "jasmine": ["melati", "jasmine"],
    "sandalwood": ["sandalwood", "sandal", "cendana"],
    "oud": ["oud"],
    "musk": ["musk", "misik", "kasturi"],
    "citrus": ["citrus", "jeruk"],
    "orange": ["jeruk", "orange"],
    "coconut": ["kelapa", "coconut"],
    "coffee": ["kopi", "coffee"],
    "cherry": ["ceri", "cherry"],
    "apple": ["apel", "apple"],
    "pear": ["pir", "pear"],
    "lavender": ["lavender"],
    "amber": ["amber"],
    "caramel": ["karamel", "caramel"],
    "chocolate": ["cokelat", "chocolate"],
    "tobacco": ["tembakau", "tobacco"],
    "leather": ["kulit", "leather"],
    "tea": ["teh", "tea"],
    "lychee": ["lychee", "leci"],
    "peach": ["persik", "peach"],
    "strawberry": ["stroberi", "strawberry"],
    "mango": ["mangga", "mango"],
    "pineapple": ["nanas", "pineapple"],
    "floral": ["floral", "bunga"],
    "flower": ["bunga", "floral", "flower"],
    "woody": ["woody", "kayu"],
    "fresh": ["segar", "fresh"],
    "sweet": ["manis", "sweet"],
    "powder": ["powder", "bedak"],
    "marine": ["laut", "marine", "aquatic"],
    "aquatic": ["aquatic", "laut", "marine"],
    "spicy": ["rempah", "spicy"],
    "fruity": ["fruity", "buah"],
}

NOTE_SYNONYMS = {
    "cinnamon": ["kayu manis", "cinnamon"],
    "vanilla": ["vanilla", "vanili"],
    "rose": ["mawar", "rose"],
    "jasmine": ["melati", "jasmine"],
    "sandalwood": ["sandalwood", "sandal", "cendana"],
    "oud": ["oud"],
    "musk": ["musk", "misik", "kasturi"],
    "citrus": ["citrus", "jeruk"],
    "orange": ["jeruk", "orange"],
    "coconut": ["kelapa", "coconut"],
    "coffee": ["kopi", "coffee"],
    "cherry": ["ceri", "cherry"],
    "apple": ["apel", "apple"],
    "pear": ["pir", "pear"],
    "lavender": ["lavender"],
    "amber": ["amber"],
    "caramel": ["karamel", "caramel"],
    "chocolate": ["cokelat", "chocolate"],
    "tobacco": ["tembakau", "tobacco"],
    "leather": ["kulit", "leather"],
    "tea": ["teh", "tea"],
    "lychee": ["lychee", "leci"],
    "peach": ["persik", "peach"],
    "strawberry": ["stroberi", "strawberry"],
    "mango": ["mangga", "mango"],
    "pineapple": ["nanas", "pineapple"],
    "floral": ["floral", "bunga"],
    "flower": ["bunga", "floral", "flower"],
    "woody": ["woody", "kayu"],
    "fresh": ["segar", "fresh"],
    "sweet": ["manis", "sweet"],
    "powder": ["powder", "bedak"],
    "marine": ["laut", "marine", "aquatic"],
    "aquatic": ["aquatic", "laut", "marine"],
    "spicy": ["rempah", "spicy"],
    "fruity": ["fruity", "buah"],
}



ARAB_KW = ["arabic", "arabian", "arab", "timur tengah", "ibadah", "sholat", "solat", "sesajen", "syarat", "keris"]
CANDY_KW = ["permen", "candy"]

def is_arab_q(ql):
    return any(k in ql for k in ARAB_KW)

def is_candy_q(ql):
    return any(k in ql for k in CANDY_KW)

def boleh(nama, ql):
    if nama.startswith("ARABIC PERFUME"):
        return is_arab_q(ql)
    if nama.startswith("CANDY / FRUIT"):
        return is_candy_q(ql)
    return True

def acak(lst, n):
    if not lst:
        return []
    return random.sample(lst, min(n, len(lst)))

def pilih_pool(pool, ql):
    if is_arab_q(ql):
        return [p for p in pool if p.nama.startswith("ARABIC PERFUME")]
    if is_candy_q(ql):
        candy = [p for p in pool if p.nama.startswith("CANDY / FRUIT")]
        others = [p for p in pool if not p.nama.startswith("CANDY / FRUIT") and not p.nama.startswith("ARABIC PERFUME")]
        return acak(candy, 2) + acak(others, 8)
    return [p for p in pool if not p.nama.startswith("ARABIC PERFUME") and not p.nama.startswith("CANDY / FRUIT")]


STOP_WORDS = ["stok", "berapa", "harga", "jual", "modal", "grosir", "pasaran", "kode", "pabrik", "brand", "dari", "apa", "saja", "yang", "parfum", "parfume", "notes", "note", "aroma", "wangi", "hari", "ini", "terjual", "laris", "kosong", "habis", "menipis", "restock", "untuk", "siapa", "gender", "kategori", "untung", "laba", "sekarang", "ada", "gak", "tidak", "kalau", "mirip", "serupa", "dan", "di", "ke", "dengan", "omzet", "omset", "qris", "tunai", "non", "naik", "turun", "minggu", "bulan", "tahun", "margin", "pengeluaran", "dead", "stock", "top", "best", "seller", "perlu", "harus", "produk", "pria", "wanita", "cowok", "cewek", "cwe", "cwek", "cowo", "cwok", "laki", "bujang", "gadis", "perempuan"]

def cari_produk(ql, produk_list):
    import difflib
    for p in produk_list:
        if p.nama.lower() in ql:
            return p
    toks = [w for w in re.split("[^a-z0-9]+", ql) if len(w) >= 3 and w not in STOP_WORDS]
    if not toks:
        return None
    best = None
    best_score = 0.0
    for p in produk_list:
        ntoks = [w for w in re.split("[^a-z0-9]+", p.nama.lower()) if len(w) >= 3]
        score = 0.0
        for w in toks:
            if w in ntoks:
                score += 1.0
            else:
                if difflib.get_close_matches(w, ntoks, n=1, cutoff=0.8):
                    score += 0.8
        if score > 0:
            norm = score / len(toks)
            if norm > best_score:
                best_score = norm
                best = p
    if best_score >= 0.8:
        return best
    return None
