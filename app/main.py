from fastapi import Body
import json
import re
import random
import secrets
import string
from datetime import date, datetime, timedelta
import os
import shutil
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.notes_data import N
from app.gender_data import G
from app.pembulatan import bulat_harga
from app.db import Base, SessionLocal, engine, get_db

Base.metadata.create_all(bind=engine)


# MIGRASI PENGELUARAN
from sqlalchemy import inspect, text

with engine.connect() as conn:

    insp = inspect(engine)

    if "pengeluaran" in insp.get_table_names():

        cols = [c["name"] for c in insp.get_columns("pengeluaran")]

        if "jenis" not in cols:
            conn.execute(
                text("ALTER TABLE pengeluaran ADD COLUMN jenis VARCHAR")
            )

        if "status" not in cols:
            conn.execute(
                text("ALTER TABLE pengeluaran ADD COLUMN status VARCHAR")
            )

        conn.execute(
            text(
                "UPDATE pengeluaran SET status='AKTIF' WHERE status IS NULL"
            )
        )

        conn.commit()

models.migrate_db()

app = FastAPI(title="Aplikasi Kasir")

# ================= BACKUP OTOMATIS DATABASE =================


def catat_backup(aksi, file="", keterangan=""):

    folder = "backup/log_backup"
    os.makedirs(folder, exist_ok=True)

    nama = datetime.now().strftime(
        "backup_log_%Y%m%d.txt"
    )

    path = os.path.join(folder, nama)

    with open(path, "a", encoding="utf-8") as f:
        f.write(
            "\n"
            "[" + datetime.now().strftime("%d/%m/%Y %H:%M") + "]\n"
            "AKSI : " + aksi + "\n"
            "FILE : " + str(file) + "\n"
            "INFO : " + keterangan + "\n"
            "-------------------------\n"
        )




@app.get("/backup-history")
def backup_history(request: Request):

    data = []

    folders = [
        "backup/log_backup",
        "backup/log_restore"
    ]

    for folder in folders:

        if os.path.exists(folder):

            for nama in sorted(os.listdir(folder), reverse=True):

                if nama.endswith(".txt"):

                    path = os.path.join(folder, nama)

                    with open(path, "r", encoding="utf-8") as f:
                        isi = f.read()

                blok = isi.replace("\\n", "\n").split("-------------------------")

                if "RESTORE DATABASE" in isi:
                    blok += isi.split("RESTORE DATABASE")

                for b in blok:

                    if "AKSI :" in b or "RESTORE DATABASE" in b:

                        baris = b.strip().split("\n")

                        if "RESTORE DATABASE" in b:

                            waktu = ""
                            file = ""

                            for x in baris:

                                if x.startswith("Waktu"):
                                    waktu = x.replace("Waktu : ", "")

                                elif x.startswith("Sumber"):
                                    file = x.replace("Sumber : ", "")

                            data.append({
                                "waktu": waktu,
                                "aksi": "RESTORE",
                                "file": file,
                                "info": "Database berhasil dipulihkan"
                            })

                            continue

                        waktu = ""
                        aksi = ""
                        file = ""
                        info = ""

                        for x in baris:

                            if x.startswith("["):
                                waktu = x.replace("[","").replace("]","")

                            elif x.startswith("AKSI"):
                                aksi = x.replace("AKSI : ","")

                            elif x.startswith("FILE"):
                                file = x.replace("FILE : ","")

                            elif x.startswith("INFO"):
                                info = x.replace("INFO : ","")

                        data.append({
                            "waktu": waktu,
                            "aksi": aksi,
                            "file": file,
                            "info": info
                        })



    from datetime import datetime

    for item in data:
        try:
            if len(item["waktu"]) > 10:
                dt = datetime.strptime(
                    item["waktu"].split(".")[0],
                    "%Y-%m-%d %H:%M:%S"
                )
                item["waktu"] = dt.strftime("%d/%m/%Y %H:%M")
        except:
            pass

    data.sort(
        key=lambda x: x["waktu"],
        reverse=True
    )


    from datetime import datetime

    for item in data:
        try:
            if len(item["waktu"]) > 10:
                dt = datetime.strptime(
                    item["waktu"].split(".")[0],
                    "%Y-%m-%d %H:%M:%S"
                )
                item["waktu"] = dt.strftime("%d/%m/%Y %H:%M")
        except:
            pass

    data.sort(
        key=lambda x: x["waktu"],
        reverse=True
    )

    return templates.TemplateResponse(
        request=request,
        name="backup_history.html",
        context={
            "data": data
        }
    )


def backup_database(jenis="auto"):
    db_file = "kasir.db"

    folder = Path("backup") / jenis
    folder.mkdir(parents=True, exist_ok=True)

    if not Path(db_file).exists():
        return


    if jenis == "auto":

        nama = "auto_" + datetime.now().strftime("%Y%m%d") + ".db"

        tujuan = folder / nama

        # hanya 1 backup otomatis per hari
        if tujuan.exists():
            return

    else:

        nama = jenis + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"

        tujuan = folder / nama


    shutil.copy2(db_file, tujuan)

    catat_backup(
        "BACKUP",
        str(tujuan),
        "Backup database berhasil dibuat " + jenis
    )


    # maksimal 30 file tiap kategori
    files = sorted(
        folder.glob("*.db"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )


    for f in files[30:]:
        f.unlink()


@app.on_event("startup")
def auto_backup_database():
    backup_database("auto")

# ================= END BACKUP =================


templates = Jinja2Templates(directory="templates")


NAMA_TOKO = "MEKAR SARI"

app.mount("/static", StaticFiles(directory="static"), name="static")
templates.env.globals["nama_toko"] = NAMA_TOKO


def user_context(request: Request):
    role = "guest"

    sid = request.cookies.get("session_id")

    if sid:
        dbx = SessionLocal()
        sesi = dbx.query(models.Sesi).filter_by(token=sid).first()
        dbx.close()

        if sesi:
            role = sesi.role

    return {
        "user_role": role
    }


templates.context_processors = [user_context]

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


LOGIN_FAIL = {}

@app.post("/login/masuk")
def login_masuk(request: Request, username: str = Form(...), password: str = Form(...)):
    import time as _time
    info = LOGIN_FAIL.setdefault(username, {"n": 0, "lock": 0})
    if info["lock"] and _time.time() < info["lock"]:
        sisa = int((info["lock"] - _time.time()) // 60) + 1
        return templates.TemplateResponse(
            request, "login.html",
            {"pesan": "Terlalu banyak percobaan. Coba lagi " + str(sisa) + " menit lagi."})
    dbx = SessionLocal()

    akun = dbx.query(models.User).filter_by(
        username=username,
        password=password
    ).first()

    if akun:
        info["n"] = 0
        info["lock"] = 0
        sid = secrets.token_hex(16)
        dbx = SessionLocal()
        dbx.add(models.Sesi(
            token=sid,
            user_id=akun.id,
            username=akun.username,
            role=akun.role
        ))
        dbx.commit()
        dbx.close()
        resp = RedirectResponse("/dashboard", status_code=303)
        resp.set_cookie("session_id", sid, max_age=604800)
        return resp
    info["n"] += 1
    if info["n"] >= 5:
        info["lock"] = _time.time() + 300
        info["n"] = 0
        return templates.TemplateResponse(
            request, "login.html",
            {"pesan": "5x salah! Login dikunci 5 menit."})
    return templates.TemplateResponse(
        request, "login.html",
        {"pesan": "Username atau password salah (percobaan " + str(info["n"]) + "/5)"})




def get_user_session(request: Request):
    sid = request.cookies.get("session_id")

    if not sid:
        return None

    dbx = SessionLocal()

    sesi = dbx.query(models.Sesi).filter_by(
        token=sid
    ).first()

    dbx.close()

    return sesi


def hanya_admin(request: Request):
    sesi = get_user_session(request)

    if not sesi:
        return False

    return sesi.role == "admin"


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
    transaksi_list = transaksi_valid(db)
    omzet_hari_ini = 0.0
    transaksi_hari_ini = 0
    tunai_total = 0.0
    nontunai_total = 0.0
    for t in transaksi_list:
        if t.dibuat and t.dibuat.date() == today:
            omzet_hari_ini += t.total
            transaksi_hari_ini += 1
            _t, _n = split_tunai_non(t)
            tunai_total += _t
            nontunai_total += _n
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

    omzet_bulan_ini = sum(
        t.total for t in transaksi_list
        if t.dibuat and t.dibuat.date() >= month_start
    )

    transaksi_bulan_ini = sum(
        1 for t in transaksi_list
        if t.dibuat and t.dibuat.date() >= month_start
    )

    stok_menipis = db.query(models.Produk).filter(
        models.Produk.stok < 10
    ).count()

    produk_stok_menipis = db.query(models.Produk).filter(
        models.Produk.stok < 10
    ).order_by(models.Produk.stok.asc()).all()

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
            "omzet_bulan_ini": omzet_bulan_ini,
            "transaksi_bulan_ini": transaksi_bulan_ini,
            "stok_menipis": stok_menipis,
            "produk_stok_menipis": produk_stok_menipis,
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

    urutan_cepat = [
        "Z - PRIME MOLI",
        "TAS PLASTIK PERFUMERY KECIL",
        "TAS PLASTIK PERFUMERY BESAR",
        "PROMO FREE EQUATION"
    ]

    produk_cepat = []

    for nama in urutan_cepat:
        for p in produk_list:
            if (p.nama or "").upper() == nama:
                produk_cepat.append(p)
                break

    return templates.TemplateResponse(
        request,
        "kasir.html",
        {
            "produk_list": produk_list,
            "produk_cepat": produk_cepat
        }
    )


def filter_transaksi(semua, flt, dari, sampai, q):
    today = date.today()
    out = []
    for t in semua:
        d = t.dibuat.date()
        if flt == "HARI" and d != today:
            continue
        if flt == "KEMARIN" and d != today - timedelta(days=1):
            continue
        if flt == "KOSTUM":
            d1 = parse_date(dari)
            d2 = parse_date(sampai)
            if d1 and d < d1:
                continue
            if d2 and d > d2:
                continue
        if flt == "BULAN" and dari:
            if t.dibuat.strftime("%Y-%m") != dari[:7]:
                continue
        if q:
            kode = (t.kode_trx or ("TRX-" + str(t.id))).upper()
            if q.upper() not in kode:
                continue
        out.append(t)
    return out


@app.get("/riwayat")
def riwayat_transaksi(request: Request, filter: str = "", dari: str = "", sampai: str = "", q: str = "", db: Session = Depends(get_db)):
    semua = db.query(models.Transaksi).order_by(models.Transaksi.id.desc()).all()
    transaksi_list = filter_transaksi(semua, filter, dari, sampai, q)
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
                "void": t.void or 0,
            }
        )
    total_penjualan = sum(x["total"] for x in data if not x["void"])
    return templates.TemplateResponse(
        request,
        "riwayat.html",
        {
            "transaksi_list": data,
            "total_penjualan": total_penjualan,
            "jumlah_transaksi": len(data),
            "filter": filter,
            "dari": dari,
            "sampai": sampai,
            "q": q,
        },
    )


@app.get("/riwayat/export")
def riwayat_export(filter: str = "", dari: str = "", sampai: str = "", q: str = "", db: Session = Depends(get_db)):
    semua = sorted(transaksi_valid(db), key=lambda t: t.id)
    transaksi_list = filter_transaksi(semua, filter, dari, sampai, q)
    lines = ["ID;Kode;Waktu;Metode;Items;Total;Diskon;Bayar;Kembalian"]
    for t in transaksi_list:
        items = json.loads(t.items)
        items_str = ", ".join(str(i["nama"]) + " x" + str(i["jumlah"]) for i in items)
        lines.append(
            ";".join(
                [
                    str(t.id),
                    t.kode_trx or "",
                    t.dibuat.strftime("%d/%m/%Y %H:%M"),
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
        headers={"Content-Disposition": "attachment; filename=transaksi.csv"},
    )


@app.post("/transaksi/void/{trx_id}")
def void_transaksi(
    trx_id: int,
    void_reason: str = Form("Tanpa alasan"),
    db: Session = Depends(get_db)
):
    t = db.get(models.Transaksi, trx_id)
    if not t:
        raise HTTPException(404, "Transaksi tidak ditemukan")
    if t.void:
        return RedirectResponse("/riwayat", status_code=303)
    t.void = 1
    t.void_reason = void_reason
    t.void_time = datetime.now()
    t.void_by = "Admin"

    for it in json.loads(t.items):
        p = db.query(models.Produk).filter_by(nama=it["nama"]).first()
        if p:
            jumlah = it["jumlah"]

            db.add(models.StokMasuk(
                nama=p.nama,
                jumlah=jumlah,
                jenis="VOID",
                keterangan="VOID TRX " + (t.kode_trx or ("TRX-" + str(t.id)))
            ))

            p.stok = (p.stok or 0) + jumlah

            db.add(models.StokMasuk(
                nama=p.nama,
                jumlah=jumlah,
                jenis="MASUK",
                keterangan="PENGEMBALIAN VOID " + (t.kode_trx or ("TRX-" + str(t.id)))
            ))
    db.commit()
    return RedirectResponse("/riwayat", status_code=303)





@app.get("/backup/list")
def backup_list():
    folder = Path("backup")
    folder.mkdir(exist_ok=True)

    data = []

    for f in sorted(folder.glob("kasir_*.db"), reverse=True):
        data.append({
            "nama": f.name,
            "ukuran": round(f.stat().st_size / 1024, 1)
        })

    return data


@app.post("/backup/manual")
def backup_manual():
    backup_database("manual")
    return RedirectResponse("/backup-restore", status_code=303)


@app.post("/backup/restore/{nama:path}")
def backup_restore(nama: str):

    folder = Path("backup")

    file_backup = Path(nama)

    if not file_backup.exists():
        file_backup = Path("backup") / nama.replace("backup/","")

    if not file_backup.exists():
        raise HTTPException(404, "Backup tidak ditemukan")

    # backup kondisi sekarang sebelum restore
    sekarang = folder / (
        "sebelum_restore_" +
        datetime.now().strftime("%Y%m%d_%H%M%S") +
        ".db"
    )

    shutil.copy2("kasir.db", sekarang)

    shutil.copy2(file_backup, "kasir.db")

    # reset koneksi sqlite setelah restore
    engine.dispose()

    return RedirectResponse(
        "/backup-restore",
        status_code=303
    )

@app.get("/manajemen")
def manajemen_produk(request: Request, db: Session = Depends(get_db)):
    produk_list = db.query(models.Produk).all()
    return templates.TemplateResponse(request, "manajemen.html", {"produk_list": produk_list})


@app.get("/pembelian")
def halaman_pembelian(
    request: Request,
    status: str = "",
    db: Session = Depends(get_db)
):

    query = db.query(models.Pembelian)

    if status:
        query = query.filter(
            models.Pembelian.status == status
        )

    pembelian = query.order_by(
        models.Pembelian.id.desc()
    ).all()

    return templates.TemplateResponse(
        request,
        "pembelian.html",
        {
            "pembelian": pembelian,
            "filter_status": status
        }
    )




@app.get("/laporan/pembelian")
def laporan_pembelian(
    request: Request,
    dari: str = "",
    sampai: str = "",
    db: Session = Depends(get_db)
):

    if dari:
        dari = datetime.strptime(dari, "%Y-%m-%d").date()
    else:
        dari = date.today().replace(day=1)

    if sampai:
        sampai = datetime.strptime(sampai, "%Y-%m-%d").date()
    else:
        sampai = date.today()

    total, jumlah, data = hitung_pembelian(
        dari,
        sampai,
        db
    )

    return templates.TemplateResponse(
        request,
        "laporan_pembelian.html",
        {
            "total": total,
            "jumlah": jumlah,
            "data": data,
            "dari": dari,
            "sampai": sampai
        }
    )



@app.get("/laporan/pembelian/excel")
def export_laporan_pembelian_excel(
    dari: str = "",
    sampai: str = "",
    db: Session = Depends(get_db)
):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from io import BytesIO
    from datetime import datetime
    from fastapi.responses import StreamingResponse

    if dari:
        start_dt = datetime.strptime(dari, "%Y-%m-%d").date()
    else:
        start_dt = date.today().replace(day=1)

    if sampai:
        end_dt = datetime.strptime(sampai, "%Y-%m-%d").date()
    else:
        end_dt = date.today()

    data = db.query(models.Pembelian).filter(
        models.Pembelian.status == "SELESAI"
    ).all()

    data = [
        p for p in data
        if p.dibuat and start_dt <= p.dibuat.date() <= end_dt
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "Pembelian"

    ws["A1"] = "CABANG"
    ws["B1"] = ": MEKAR SARI"

    ws["A2"] = "LAPORAN"
    ws["B2"] = ": PEMBELIAN"

    ws["A3"] = "PERIODE"
    ws["B3"] = ": " + start_dt.strftime("%d-%m-%Y") + " s/d " + end_dt.strftime("%d-%m-%Y")

    ws["A5"] = "DETAIL PEMBELIAN"

    header_row = 7

    headers = [
        "NO",
        "KODE PEMBELIAN",
        "TANGGAL",
        "SUPPLIER",
        "TOTAL",
        "STATUS"
    ]

    for i, h in enumerate(headers, 1):
        ws.cell(header_row, i, h)
        ws.cell(header_row, i).font = Font(bold=True)

    row = 8
    total = 0

    for no, p in enumerate(data, 1):

        supplier = getattr(p, "supplier", "") or "-"

        ws.cell(row, 1, no)
        ws.cell(row, 2, p.kode_beli)
        ws.cell(row, 3, p.dibuat.strftime("%d-%m-%Y %H:%M"))
        ws.cell(row, 4, supplier)
        ws.cell(row, 5, p.total or 0)
        ws.cell(row, 6, p.status)

        total += p.total or 0
        row += 1

    row += 1

    ws.cell(row, 1, "TOTAL PEMBELIAN SELESAI")
    ws.cell(row, 5, total)

    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 25
    ws.column_dimensions["C"].width = 22
    ws.column_dimensions["D"].width = 25
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 15

    file = BytesIO()
    wb.save(file)
    file.seek(0)

    return StreamingResponse(
        file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            "attachment; filename=laporan-pembelian.xlsx"
        }
    )


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
def buat_transaksi(payload: dict = Body(...), db: Session = Depends(get_db)):
    import random, string
    from datetime import datetime
    items_in = payload.get("items", [])
    if not items_in:
        return JSONResponse({"ok": False, "detail": "Keranjang kosong"}, status_code=400)
    rows = []
    total = 0.0
    bibit_total = 0.0
    for it in items_in:
        p = db.get(models.Produk, int(it["produk_id"]))
        if not p:
            return JSONResponse({"ok": False, "detail": "Produk tidak ditemukan"}, status_code=400)
        qty = float(it["jumlah"])
        if qty == int(qty): qty = int(qty)
    for it in items_in:
        p = db.get(models.Produk, int(it["produk_id"]))
        qty = float(it["jumlah"])
        if qty == int(qty): qty = int(qty)
        dsc = float(it.get("diskon") or 0)
        sub = (p.harga or 0) * qty - dsc
        total += sub
        if (p.kategori or "").upper() == "BIBIT":
            bibit_total += sub
        rows.append({"nama": p.nama, "jumlah": qty, "harga": p.harga, "diskon": dsc})
        if getattr(p, "stok", None) is not None:
            p.stok -= qty
    dt = float(payload.get("diskon_total") or 0)
    total -= dt
    poin = int(payload.get("poin_dipakai") or 0)
    ag_id = payload.get("anggota_id") or ""
    ag = db.get(models.Anggota, int(ag_id)) if ag_id else None
    if poin > 0:
        if not ag:
            return JSONResponse({"ok": False, "detail": "Pilih anggota dulu untuk pakai poin"}, status_code=400)
        if (ag.poin or 0) < poin:
            return JSONResponse({"ok": False, "detail": "Poin tidak cukup"}, status_code=400)
    metode = payload.get("metode") or "TUNAI"
    tunai = float(payload.get("tunai") or 0)

    if metode == "TUNAI" and tunai < total:
        return JSONResponse(
            {
                "ok": False,
                "detail": "Pembayaran kurang"
            },
            status_code=400
        )

    request_id = payload.get("request_id")

    if request_id:
        cek = db.query(models.Transaksi).filter(
            models.Transaksi.request_id == request_id
        ).first()

        if cek:
            return JSONResponse({
                "ok": True,
                "id": cek.id,
                "duplicate": True
            })

    t = models.Transaksi()
    t.request_id = payload.get("request_id")
    t.items = json.dumps(rows)
    t.total = total
    t.total_diskon = dt + sum(r["diskon"] for r in rows)
    t.metode = payload.get("metode") or "TUNAI"
    t.bayar = float(payload.get("tunai") or 0)

    # simpan pembagian pembayaran
    if t.metode == "NON":
        t.p_tunai = 0
        t.p_nontunai = total

    elif t.metode == "SPLIT" or "NON-TUNAI" in t.metode.upper():
        t.p_tunai = float(payload.get("tunai") or 0)
        t.p_nontunai = total - t.p_tunai

    else:
        t.p_tunai = total
        t.p_nontunai = 0

    t.kembalian = float(payload.get("kembalian") or 0)
    t.poin_dipakai = poin
    t.kode_trx = "RP-MKRS/" + datetime.now().strftime("%d-%m-%Y") + "/" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    db.add(t)
    db.flush()
    if ag:
        if poin > 0:
            ag.poin = (ag.poin or 0) - poin

            db.add(
                models.PoinLog(
                    anggota_id=ag.id,
                    trx_id=t.id,
                    poin=-poin
                )
            )
        if bibit_total > 0 and not poin:
            earn = int(bibit_total * 0.05)
            ag.poin = (ag.poin or 0) + earn
            db.add(models.PoinLog(anggota_id=ag.id, trx_id=t.id, poin=earn))
    try:
        if ag:
            t.poin_setelah = ag.poin or 0
        else:
            t.poin_setelah = 0

        db.commit()

    except Exception as e:
        db.rollback()

        return JSONResponse(
            {
                "ok": False,
                "detail": str(e)
            },
            status_code=500
        )

    return {"ok": True, "id": t.id}



@app.get("/laporan")
def laporan_harian(request: Request, db: Session = Depends(get_db)):
    transaksi_list = transaksi_valid(db)
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

    hari_ini = date.today()

    omzet_hari_ini = sum(
        t.total for t in transaksi_list
        if t.dibuat.date() == hari_ini
    )

    omzet_bulan_ini = sum(
        t.total for t in transaksi_list
        if t.dibuat.year == hari_ini.year
        and t.dibuat.month == hari_ini.month
    )

    jumlah_transaksi = len(transaksi_list)

    rata_rata = (
        total_omzet / jumlah_transaksi
        if jumlah_transaksi
        else 0
    )

    return templates.TemplateResponse(
        request,
        "laporan.html",
        {
            "laporan": laporan,
            "total_omzet": total_omzet,
            "omzet_hari_ini": omzet_hari_ini,
            "omzet_bulan_ini": omzet_bulan_ini,
            "jumlah_transaksi": jumlah_transaksi,
            "rata_rata": rata_rata
        }
    )


@app.get("/laporan/export")

def export_laporan(
    dari: str = "",
    sampai: str = "",
    db: Session = Depends(get_db)
):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from io import BytesIO
    from datetime import datetime
    from fastapi.responses import StreamingResponse

    if dari:
        start_dt = datetime.strptime(dari, "%Y-%m-%d").date()
    else:
        start_dt = date.today().replace(day=1)

    if sampai:
        end_dt = datetime.strptime(sampai, "%Y-%m-%d").date()
    else:
        end_dt = date.today()


    data = [
        t for t in transaksi_valid(db)
        if start_dt <= t.dibuat.date() <= end_dt
    ]


    wb = Workbook()
    ws = wb.active
    ws.title = "Penjualan"


    # IDENTITAS
    ws["A1"] = "CABANG"
    ws["B1"] = ": MEKAR SARI"

    ws["A2"] = "LAPORAN"
    ws["B2"] = ": PENJUALAN"

    ws["A3"] = "PERIODE"
    ws["B3"] = (
        ": "
        + start_dt.strftime("%d-%m-%Y")
        + " s/d "
        + end_dt.strftime("%d-%m-%Y")
    )


    ws["A5"] = "DETAIL PENJUALAN"


    row = 7

    header = [
        "NO",
        "KODE TRANSAKSI",
        "TANGGAL",
        "METODE",
        "TOTAL",
        "STATUS"
    ]


    for i, h in enumerate(header, 1):
        ws.cell(row, i, h)
        ws.cell(row, i).font = Font(bold=True)


    row += 1
    total = 0


    for no, t in enumerate(data, 1):

        ws.cell(row,1,no)
        ws.cell(row,2,t.kode_trx)
        ws.cell(row,3,t.dibuat.strftime("%d-%m-%Y %H:%M"))
        ws.cell(row,4,t.metode or "TUNAI")
        ws.cell(row,5,t.total or 0)
        ws.cell(row,6,t.status)

        total += t.total or 0

        row += 1


    row += 1

    ws.cell(row,1,"TOTAL PENJUALAN")
    ws.cell(row,5,total)


    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 25
    ws.column_dimensions["C"].width = 22
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 15


    file = BytesIO()
    wb.save(file)
    file.seek(0)


    return StreamingResponse(
        file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            "attachment; filename=laporan-penjualan.xlsx"
        }
    )


def hitung_laba(db, start_dt, end_dt):
    trx = [t for t in transaksi_valid(db) if start_dt <= t.dibuat.date() <= end_dt]
    rows = {}
    for t in trx:
        r = rows.setdefault(t.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "pmsk": 0.0, "trx": 0})
        r["trx"] += 1
        item_disc = 0.0
        hpp_t = 0.0
        for it in json.loads(t.items):
            qty = it["jumlah"]
            item_disc += it.get("diskon") or 0
            p = db.query(models.Produk).filter_by(nama=it["nama"]).first()
            if p:
                hpp_t += (p.harga_modal or 0) * qty
        dtot = t.total_diskon or 0
        net_t = t.total or 0
        r["gross"] += net_t + item_disc + dtot
        r["disc"] += item_disc + dtot
        r["net"] += net_t
        r["hpp"] += hpp_t
    for pg in db.query(models.Pengeluaran).filter(models.Pengeluaran.status != 'VOID').all():
        if start_dt <= pg.dibuat.date() <= end_dt:
            r = rows.setdefault(pg.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "pmsk": 0.0, "trx": 0})
            r["op"] += pg.jumlah or 0
    for pm in db.query(models.Pemasukan).all():
        if start_dt <= pm.dibuat.date() <= end_dt:
            r = rows.setdefault(pm.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "pmsk": 0.0, "trx": 0})
            r["pmsk"] += pm.jumlah or 0
    for mm in db.query(models.RekapManual).all():
        if start_dt <= mm.tanggal <= end_dt:
            r = rows.setdefault(mm.tanggal, {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "pmsk": 0.0, "trx": 0})
            r["gross"] += mm.omzet or 0
            r["net"] += mm.omzet or 0
            r["hpp"] += mm.modal or 0
            r["op"] += (mm.omzet or 0) - (mm.modal or 0) - (mm.keuntungan or 0)
            r["trx"] += mm.trx or 0
    tot = {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "pmsk": 0.0, "trx": 0}
    for r in rows.values():
        for k in tot:
            tot[k] += r[k]
    return {"tot": tot, "rows": sorted(rows.items(), reverse=True)}



@app.get("/labarugi")
def labarugi_page(request: Request, start_date: str = "", end_date: str = "", db: Session = Depends(get_db)):
    from datetime import datetime
    if not start_date or not end_date:
        end_dt = datetime.now().date()
        start_dt = end_dt
    else:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    data = hitung_laba(db, start_dt, end_dt)
    return templates.TemplateResponse(request, "labarugi.html", {
        "start_date": start_dt.isoformat(),
        "end_date": end_dt.isoformat(),
        "tot": data["tot"],
        "rows": data["rows"],
    })


@app.post("/pengeluaran")
def tambah_pengeluaran(
    keterangan: str = Form(...),
    jumlah: float = Form(...),
    db: Session = Depends(get_db),
):
    db.add(models.Pengeluaran(keterangan=keterangan, jumlah=jumlah))
    db.commit()
    return RedirectResponse("/labarugi", status_code=303)


@app.post("/pemasukan")
def tambah_pemasukan(keterangan: str = Form(...), jumlah: float = Form(...), db: Session = Depends(get_db)):
    db.add(models.Pemasukan(keterangan=keterangan, jumlah=jumlah))
    db.commit()
    backup_otomatis()
    return {"ok": True}


@app.get("/tutup")
def tutup_page(request: Request, db: Session = Depends(get_db)):
    riwayat = db.query(models.RiwayatTutup).order_by(models.RiwayatTutup.id.desc()).all()
    return templates.TemplateResponse(request, "tutup.html", {"riwayat": riwayat})


@app.get("/tutup/preview")
def tutup_preview(db: Session = Depends(get_db)):
    return buat_ringkasan(db)



def backup_otomatis():
    sekarang = datetime.now()

    folder = os.path.join(
        "backup",
        str(sekarang.year),
        str(sekarang.month).zfill(2)
    )

    os.makedirs(folder, exist_ok=True)

    nama_file = (
        "kasir-auto-"
        + sekarang.strftime("%Y-%m-%d-%H%M%S")
        + ".db"
    )

    tujuan = os.path.join(folder, nama_file)

    shutil.copy2("kasir.db", tujuan)

    ukuran = os.path.getsize(tujuan)

    log = os.path.join("backup", "backup_log.txt")

    with open(log, "a", encoding="utf-8") as f:
        f.write(
            f"{sekarang.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"STATUS : BERHASIL\n"
            f"FILE   : {tujuan}\n"
            f"UKURAN : {ukuran} byte\n"
            f"{'-'*40}\n"
        )


@app.post("/tutup/simpan")
async def tutup_simpan(request: Request, db: Session = Depends(get_db)):
    d = await request.json()
    db.add(models.RiwayatTutup(omzet=d.get("omzet", 0), tunai=d.get("tunai", 0), nontunai=d.get("nontunai", 0), pengeluaran=d.get("pengeluaran", 0), ringkasan=d.get("text", "")))
    db.commit()
    backup_otomatis()
    return {"ok": True}






@app.get("/backup")
def backup_db():
    backup_otomatis()

    return RedirectResponse(
        "/backup-restore",
        status_code=303
    )




@app.post("/backup/create")
def buat_backup_manual():

    folder = Path("backup/manual")

    folder.mkdir(
        parents=True,
        exist_ok=True
    )


    nama = (
        "manual_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".db"
    )


    tujuan = folder / nama


    shutil.copy2(
        "kasir.db",
        tujuan
    )


    return RedirectResponse(
        "/backup-restore",
        status_code=303
    )


@app.post("/restore")
def restore_backup(file: str = Form(...)):
    if not os.path.exists(file):
        raise HTTPException(
            status_code=404,
            detail="File backup tidak ditemukan"
        )

    if not file.endswith(".db"):
        raise HTTPException(
            status_code=400,
            detail="File restore harus database .db"
        )

    if os.path.getsize(file) == 0:
        raise HTTPException(
            status_code=400,
            detail="File backup kosong"
        )

    os.makedirs("backup/sebelum_restore", exist_ok=True)

    cadangan_lama = (
        "backup/sebelum_restore/kasir-sebelum-restore-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".db"
    )

    shutil.copy2("kasir.db", cadangan_lama)

    shutil.copy2(file, "kasir.db")

    # refresh koneksi database setelah restore
    engine.dispose()

    os.makedirs("backup/log_restore", exist_ok=True)

    log_file = (
        "backup/log_restore/restore-"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
        + ".txt"
    )

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(
            "RESTORE DATABASE\\n\\n"
            + "Waktu : "
            + str(datetime.now())
            + "\\n"
            + "Sumber : "
            + file
            + "\\n"
            + "Backup sebelum restore : "
            + cadangan_lama
            + "\\n"
        )

    catat_backup(
        "RESTORE",
        file,
        "Database berhasil dipulihkan"
    )

    return RedirectResponse(
        "/backup-restore",
        status_code=303
    )



@app.get("/restore/history")
def restore_history():

    hasil = []

    folder = "backup/log_restore"

    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file.endswith(".txt"):
                path = os.path.join(folder, file)

                with open(path, "r", encoding="utf-8") as f:
                    isi = f.read()

                hasil.append({
                    "nama": file,
                    "isi": isi,
                    "waktu": datetime.fromtimestamp(
                        os.path.getmtime(path)
                    ).strftime("%d/%m/%Y %H:%M")
                })

    return sorted(
        hasil,
        key=lambda x:x["waktu"],
        reverse=True
    )



@app.get("/backup-restore")
def backup_restore(request: Request):

    hasil = []

    folder = "backup"

    if os.path.exists(folder):

        for root, dirs, files in os.walk(folder):

            for file in files:

                if file.endswith(".db"):

                    path = os.path.join(root,file)

                    if "auto" in root or "auto" in file or file.startswith("kasir-auto"):
                        jenis = "Otomatis"

                    elif "manual" in root or "manual" in file:
                        jenis = "Manual"

                    elif "restore" in root or "restore" in file or "sebelum_restore" in file:
                        jenis = "Restore"

                    else:
                        jenis = "Lainnya"


                    hasil.append({
                        "file": path,
                        "nama": file,
                        "jenis": jenis,
                        "ukuran": str(round(os.path.getsize(path)/1024,1))+" KB",
                        "waktu": datetime.fromtimestamp(
                            os.path.getmtime(path)
                        ).strftime("%d/%m/%Y %H:%M")
                    })


    hasil = sorted(
        hasil,
        key=lambda x:x["waktu"],
        reverse=True
    )


    total_auto = len(
        [x for x in hasil if x["jenis"]=="Otomatis"]
    )

    total_manual = len(
        [x for x in hasil if x["jenis"]=="Manual"]
    )

    total_restore = len(
        [x for x in hasil if x["jenis"]=="Restore"]
    )


    total_ukuran = sum(
        os.path.getsize(x["file"])
        for x in hasil
    )

    total_ukuran = str(
        round(total_ukuran/1024,1)
    )+" KB"


    return templates.TemplateResponse(
        request,
        "backup_restore.html",
        {
            "backup": hasil,

            "total_auto": total_auto,

            "total_manual": total_manual,

            "total_restore": total_restore,

            "total_ukuran": total_ukuran,

            "restore_info": restore_history()
        }
    )


@app.get("/backup/download")
def download_backup(file: str):
    if not os.path.exists(file):
        raise HTTPException(status_code=404, detail="Backup tidak ditemukan")

    return FileResponse(
        file,
        filename=os.path.basename(file),
        media_type="application/octet-stream"
    )




@app.post("/backup/delete")
def delete_backup(file: str = Form(...)):
    print("DELETE FILE:", file)

    if not os.path.exists(file):
        raise HTTPException(
            status_code=404,
            detail="Backup tidak ditemukan"
        )

    if not file.startswith("backup"):
        raise HTTPException(
            status_code=403,
            detail="File tidak valid"
        )

    semua = []

    for root, dirs, files in os.walk("backup"):
        for nama in files:
            if nama.endswith(".db"):
                semua.append(
                    os.path.join(root, nama)
                )

    terbaru = max(
        semua,
        key=os.path.getmtime
    )

    if os.path.abspath(file) == os.path.abspath(terbaru):
        raise HTTPException(
            status_code=403,
            detail="Backup terbaru tidak boleh dihapus"
        )

    os.remove(file)

    catat_backup(
        "DELETE",
        file,
        "Backup dihapus manual"
    )

    return RedirectResponse(
        "/backup-restore",
        status_code=303
    )



@app.post("/backup/clean")
def clean_backup():

    semua = []

    for root, dirs, files in os.walk("backup"):
        for nama in files:
            if nama.endswith(".db"):
                path = os.path.join(root, nama)
                semua.append(path)

    if len(semua) <= 1:
        return RedirectResponse(
            "/backup-restore",
            status_code=303
        )

    terbaru = max(
        semua,
        key=os.path.getmtime
    )

    for file in semua:
        if file != terbaru:
            os.remove(file)

    return RedirectResponse(
        "/backup-restore",
        status_code=303
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
    transaksi_list = transaksi_valid(db)
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


def hitung_pembelian(d1, d2, db):

    data = db.query(models.Pembelian).filter(
        models.Pembelian.status == "SELESAI"
    ).all()

    total = 0
    jumlah = 0

    for p in data:
        if p.dibuat:
            tanggal = p.dibuat.date()

            if d1 <= tanggal <= d2:
                total += p.total or 0
                jumlah += 1

    return total, jumlah, data


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


def hitung_laba_ai(d1, d2, transaksi_list, pengeluaran_list, produk_list):
    pmap = {}
    for p in produk_list:
        pmap[p.nama] = p
    omzet = 0.0
    modal = 0.0
    keluar = 0.0
    for t in transaksi_list:
        if t.dibuat and d1 <= t.dibuat.date() <= d2:
            omzet += t.total or 0
            if t.total_modal:
                modal += t.total_modal
            else:
                for it in json.loads(t.items):
                    pr = pmap.get(it["nama"])
                    if pr:
                        modal += (pr.harga_modal or 0) * it["jumlah"]
    for p in pengeluaran_list:
        if p.dibuat and d1 <= p.dibuat.date() <= d2:
            keluar += p.jumlah or 0
    laba = omzet - modal - keluar
    margin = (laba / omzet * 100) if omzet else 0.0
    return omzet, modal, keluar, laba, margin





def style_excel_laporan(ws, judul, periode=""):
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

    ws.merge_cells("A1:D1")
    ws["A1"] = "MEKAR SARI"
    ws["A1"].font = Font(bold=True, size=16)
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:D2")
    ws["A2"] = judul
    ws["A2"].font = Font(bold=True, size=14)
    ws["A2"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A3:D3")
    ws["A3"] = "Periode : " + periode
    ws["A3"].alignment = Alignment(horizontal="center")


    # header tabel
    for cell in ws[4]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")


    garis = Side(border_style="thin")

    for row in ws.iter_rows(min_row=4):
        for cell in row:
            cell.border = Border(
                left=garis,
                right=garis,
                top=garis,
                bottom=garis
            )


    # lebar kolom aman
    ukuran = {
        "A":25,
        "B":22,
        "C":18,
        "D":15
    }

    for kolom, lebar in ukuran.items():
        ws.column_dimensions[kolom].width = lebar


    # format rupiah kolom total
    for cell in ws["C"]:
        if isinstance(cell.value,(int,float)):
            cell.number_format = '"Rp" #,##0'


    ws.freeze_panes = "A5"



    from openpyxl.styles import PatternFill

    # format header tabel
    for row in ws.iter_rows():
        for cell in row:
            if cell.row == 6 and cell.value:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(
                    "solid",
                    fgColor="D9EAF7"
                )
                cell.alignment = Alignment(
                    horizontal="center"
                )

    # tebalkan total akhir
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and "TOTAL" in cell.value:
                cell.font = Font(bold=True)

    from openpyxl.styles import PatternFill

    # ukuran kolom profesional
    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 15

    # header tabel
    for cell in ws[6]:
        if cell.value:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(
                fill_type="solid",
                fgColor="D9EAF7"
            )
            cell.alignment = Alignment(
                horizontal="center"
            )

    # total akhir
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and "TOTAL" in cell.value:
                cell.font = Font(bold=True)

    ws.freeze_panes = "A6"


def format_rupiah_excel(cell):
    cell.number_format = '"Rp" #,##0'


def rp(x):
    return "Rp " + format(int(round(x)), ",").replace(",", ".")


def jawab_ai(q, db):
    q = (q or "").lower()
    today = date.today()
    transaksi_list = transaksi_valid(db)
    pengeluaran_list = db.query(models.Pengeluaran).filter(models.Pengeluaran.status != 'VOID').all()
    produk_list = db.query(models.Produk).all()
    bibit = [p for p in produk_list if (p.kategori or "") == "BIBIT"]
    nama_bibit = set(p.nama for p in bibit)
    if "notes" in q or "aroma" in q or "wangi" in q:
        t2 = cari_produk(q, produk_list)
        if t2:
            short2 = t2.nama.split(" - ")[1] if " - " in t2.nama else t2.nama
            return t2.nama + ":\n" + format_notes(N.get(t2.nama) or "Data notes belum ada untuk produk ini.") + "\n\nMau saya carikan parfum dengan notes menyerupai " + short2 + "? Jawab: ya"
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


LAST_PRODUK = [""]

@app.get("/ai/jawab")
def ai_jawab(q: str, ctx: str = "", db: Session = Depends(get_db)):
    if not ctx:
        ctx = LAST_PRODUK[0]
    j = jawab_ai2(q, db, ctx)
    t = cari_produk(q, db.query(models.Produk).all())
    prod = t.nama if t else ctx
    LAST_PRODUK[0] = prod or ""
    db.add(models.PesanAI(pertanyaan=q, jawaban=j))
    db.commit()
    return {"jawab": j, "produk": prod}


@app.get("/ai/riwayat")
def ai_riwayat(n: int = 300, db: Session = Depends(get_db)):
    rows = db.query(models.PesanAI).order_by(models.PesanAI.id.desc()).limit(n).all()
    rows.reverse()
    return [{"q": r.pertanyaan, "a": r.jawaban} for r in rows]






def jawab_ai2(q, db, ctx=""):
    ql = (q or "").lower()
    transaksi_list = transaksi_valid(db)
    produk_list = db.query(models.Produk).all()
    pengeluaran_list = db.query(models.Pengeluaran).filter(models.Pengeluaran.status != 'VOID').all()
    terjual = {}
    for t in transaksi_list:
        for it in json.loads(t.items):
            terjual[it["nama"]] = terjual.get(it["nama"], 0) + it["jumlah"]
    if "bibit" in ql and ("terjual" in ql or "jual" in ql or "penjualan" in ql or "laku" in ql or "ml" in ql) and ("hari" in ql or "kemarin" in ql or "lusa" in ql or "lalu" in ql or "sekarang" in ql or re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", ql)):
        off = None
        if "lusa" in ql:
            off = 2
        elif "kemarin" in ql:
            off = 1
        elif "hari ini" in ql or "sekarang" in ql:
            off = 0
        else:
            mnum = re.search(r"(\d+)\s*hari\s+(?:yang\s+)?lalu", ql)
            mdate = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", ql)
            if mnum:
                off = int(mnum.group(1))
            elif mdate:
                try:
                    from datetime import datetime as _dt4
                    dd = _dt4.strptime(mdate.group(0).replace("/", "-"), "%d-%m-%Y").date()
                    off = (date.today() - dd).days
                except Exception:
                    off = None
        if off is not None and off >= 0:
            today = date.today()
            target = today - timedelta(days=off)
            kat_map = {}
            for p in produk_list:
                kat_map[p.nama] = (p.kategori or "").lower()
            ml = 0
            omz = 0.0
            ntrx = 0
            for t in transaksi_list:
                if t.dibuat and t.dibuat.date() == target:
                    hit = 0
                    for it in json.loads(t.items):
                        if kat_map.get(it["nama"]) == "bibit":
                            hit += it["jumlah"]
                            omz += (it.get("harga") or 0) * it["jumlah"]
                    if hit:
                        ntrx += 1
                    ml += hit
            label = "hari ini" if off == 0 else ("kemarin" if off == 1 else ("kemarin lusa" if off == 2 else target.strftime("%d/%m/%Y")))
            return "BIBIT " + label + " (" + target.strftime("%d/%m/%Y") + "):\nTerjual : " + str(ml) + " ml\nOmzet : " + rp(omz) + "\nJumlah transaksi: " + str(ntrx) + "\n\n(Sinkron dengan Riwayat & Laporan)"
    kat_found = None
    for kd in sorted(set((p.kategori or "").lower() for p in produk_list if p.kategori), key=len, reverse=True):
        if kd and kd in ql:
            kat_found = kd
            break
    if kat_found and ("terjual" in ql or "jual" in ql or "penjualan" in ql or "laku" in ql) and ("hari" in ql or "kemarin" in ql or "lusa" in ql or "lalu" in ql or "sekarang" in ql or re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", ql)):
        off = None
        if "lusa" in ql:
            off = 2
        elif "kemarin" in ql:
            off = 1
        elif "hari ini" in ql or "sekarang" in ql:
            off = 0
        else:
            mnum = re.search(r"(\d+)\s*hari\s+(?:yang\s+)?lalu", ql)
            mdate = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", ql)
            if mnum:
                off = int(mnum.group(1))
            elif mdate:
                try:
                    from datetime import datetime as _dt3
                    dd = _dt3.strptime(mdate.group(0).replace("/", "-"), "%d-%m-%Y").date()
                    off = (date.today() - dd).days
                except Exception:
                    off = None
        if off is not None and off >= 0:
            today = date.today()
            target = today - timedelta(days=off)
            kat_map = {}
            for p in produk_list:
                kat_map[p.nama] = (p.kategori or "").lower()
            pcs = 0
            omz = 0.0
            ntrx = 0
            for t in transaksi_list:
                if t.dibuat and t.dibuat.date() == target:
                    hit = 0
                    for it in json.loads(t.items):
                        if kat_map.get(it["nama"]) == kat_found:
                            hit += it["jumlah"]
                            omz += (it.get("harga") or 0) * it["jumlah"]
                    if hit:
                        ntrx += 1
                    pcs += hit
            label = "hari ini" if off == 0 else ("kemarin" if off == 1 else ("kemarin lusa" if off == 2 else target.strftime("%d/%m/%Y")))
            return "Kategori " + kat_found.upper() + " " + label + " (" + target.strftime("%d/%m/%Y") + "):\nTerjual : " + str(pcs) + " pcs\nOmzet : " + rp(omz) + "\nJumlah transaksi: " + str(ntrx) + "\n\n(Sinkron dengan Riwayat & Laporan)"
    if "diskon" in ql and ("hari" in ql or "kemarin" in ql or "lusa" in ql or "lalu" in ql or "sekarang" in ql or re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", ql)):
        off = None
        if "lusa" in ql:
            off = 2
        elif "kemarin" in ql:
            off = 1
        elif "hari ini" in ql or "sekarang" in ql:
            off = 0
        else:
            mnum = re.search(r"(\d+)\s*hari\s+(?:yang\s+)?lalu", ql)
            mdate = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", ql)
            if mnum:
                off = int(mnum.group(1))
            elif mdate:
                try:
                    from datetime import datetime as _dt2
                    dd = _dt2.strptime(mdate.group(0).replace("/", "-"), "%d-%m-%Y").date()
                    off = (date.today() - dd).days
                except Exception:
                    off = None
        if off is not None and off >= 0:
            today = date.today()
            target = today - timedelta(days=off)
            trx = [t for t in transaksi_list if t.dibuat and t.dibuat.date() == target]
            tot_d = sum(t.total_diskon or 0 for t in trx)
            n_d = sum(1 for t in trx if (t.total_diskon or 0) > 0)
            label = "hari ini" if off == 0 else ("kemarin" if off == 1 else ("kemarin lusa" if off == 2 else target.strftime("%d/%m/%Y")))
            return "Total diskon " + label + " (" + target.strftime("%d/%m/%Y") + "):\n" + rp(tot_d) + "\nJumlah transaksi pakai diskon: " + str(n_d) + "\n\n(Sinkron dengan Riwayat & Laporan)"
    kat_stok = None
    if "stok" in ql or "sisa" in ql:
        for kd in sorted(set((p.kategori or "").lower() for p in produk_list if p.kategori), key=len, reverse=True):
            if kd and kd in ql:
                kat_stok = kd
                break
    if kat_stok:
        off = 0
        if "lusa" in ql:
            off = 2
        elif "kemarin" in ql:
            off = 1
        elif "hari ini" in ql or "sekarang" in ql:
            off = 0
        else:
            mnum = re.search(r"(\d+)\s*hari\s+(?:yang\s+)?lalu", ql)
            mdate = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", ql)
            if mnum:
                off = int(mnum.group(1))
            elif mdate:
                try:
                    from datetime import datetime as _dt6
                    dd = _dt6.strptime(mdate.group(0).replace("/", "-"), "%d-%m-%Y").date()
                    off = (date.today() - dd).days
                except Exception:
                    off = 0
        if off is not None and off >= 0:
            today = date.today()
            target = today - timedelta(days=off)
            stok_now = sum(p.stok or 0 for p in produk_list if (p.kategori or "").lower() == kat_stok)
            sold_after = 0
            if off > 0:
                kat_map = {}
                for p in produk_list:
                    kat_map[p.nama] = (p.kategori or "").lower()
                for t in transaksi_list:
                    if t.dibuat and t.dibuat.date() > target:
                        for it in json.loads(t.items):
                            if kat_map.get(it["nama"]) == kat_stok:
                                sold_after += it["jumlah"]
            stok_then = stok_now + sold_after
            unit = "ml" if kat_stok == "bibit" else "pcs"
            label = "hari ini" if off == 0 else ("kemarin" if off == 1 else ("kemarin lusa" if off == 2 else target.strftime("%d/%m/%Y")))
            return "Sisa stok " + kat_stok.upper() + " " + label + " (" + target.strftime("%d/%m/%Y") + "):\n" + str(stok_then) + " " + unit + "\n\n(Stok sekarang: " + str(stok_now) + " " + unit + " • Terjual setelah tanggal itu: " + str(sold_after) + " " + unit + ")\n(Sinkron dengan Produk & Riwayat)"
    if ("omzet" in ql or "omset" in ql or "penjualan" in ql) and ("hari" in ql or "kemarin" in ql or "lusa" in ql or "lalu" in ql or "sekarang" in ql or re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", ql)):
        from datetime import datetime as _dt
        off = None
        if "lusa" in ql:
            off = 2
        elif "kemarin" in ql:
            off = 1
        elif "hari ini" in ql or "sekarang" in ql:
            off = 0
        else:
            mnum = re.search(r"(\d+)\s*hari\s+(?:yang\s+)?lalu", ql)
            mdate = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", ql)
            if mnum:
                off = int(mnum.group(1))
            elif mdate:
                try:
                    dd = _dt.strptime(mdate.group(0).replace("/", "-"), "%d-%m-%Y").date()
                    off = (date.today() - dd).days
                except Exception:
                    off = None
        if off is not None and off >= 0:
            today = date.today()
            target = today - timedelta(days=off)
            trx = [t for t in transaksi_list if t.dibuat and t.dibuat.date() == target]
            tot = sum(t.total or 0 for t in trx)
            tun = sum(split_tunai_non(t)[0] for t in trx)
            non = sum(split_tunai_non(t)[1] for t in trx)
            label = "hari ini" if off == 0 else ("kemarin" if off == 1 else ("kemarin lusa" if off == 2 else target.strftime("%d/%m/%Y")))
            peng_list = [p for p in db.query(models.Pengeluaran).filter(models.Pengeluaran.status != 'VOID').all() if p.dibuat and p.dibuat.date() == target]
            tot_peng = sum(p.jumlah or 0 for p in peng_list)
            tunai_bersih = tun - tot_peng
            out = ("Omzet sinkron " + label + " (" + target.strftime("%d/%m/%Y") + "):\nomzet : " + rp(tot) + "\nTUNAI : " + rp(tun) + "\nNON-TUNAI : " + rp(non))
            if tot_peng > 0:
                out += "\nPengeluaran : " + rp(tot_peng) + "\nRINCIAN PENGELUARAN:"
                for p in peng_list:
                    out += "\n- " + (p.keterangan or "Pengeluaran").upper() + " " + rp(p.jumlah or 0)
                out += "\nTUNAI setelah pengeluaran : " + rp(tunai_bersih)
                out += "\nNON-TUNAI tidak dipotong : " + rp(non)
            else:
                out += "\nPengeluaran : tidak ada\nTUNAI setelah pengeluaran : " + rp(tunai_bersih)
            out += "\n\n(Sinkron dengan Dashboard, Riwayat & Laporan)"
            return out
    if ql.strip() in ["ya", "iya", "y", "yes", "mau", "boleh", "ok", "oke"] and ctx:
        tgt = None
        for p in produk_list:
            if p.nama == ctx:
                tgt = p
                break
        if tgt:
            return jawab_mirip(tgt, produk_list)
    if ctx and ("notes" in ql or "aroma" in ql or "wangi" in ql) and "apa saja" not in ql and cari_produk(ql, produk_list) is None:
        tgt = None
        for p in produk_list:
            if p.nama == ctx:
                tgt = p
                break
        if tgt:
            short = tgt.nama.split(" - ")[1] if " - " in tgt.nama else tgt.nama
            return tgt.nama + ":\n" + format_notes(N.get(tgt.nama)) + "\n\nMau saya carikan parfum dengan notes menyerupai " + short + "? Jawab: ya"
    if "mirip" in ql or "serupa" in ql or "menyerupai" in ql:
        target = cari_produk(ql, produk_list)
        if not target:
            return "Sebutkan nama parfumnya. Contoh: yang mirip sauvage"
        return jawab_mirip(target, produk_list)
    target = cari_produk(ql, produk_list)
    if target is None and ctx and any(k in ql for k in ["notes", "note", "aroma", "wangi", "brand", "merk", "merek", "stok", "harga", "modal", "jual", "untung", "kode", "kategori", "gender", "lain"]):
        for p in produk_list:
            if p.nama == ctx:
                target = p
                break
    if target and not ("notes" in ql or "aroma" in ql or "wangi" in ql):
        if "brand" in ql or "merk" in ql or "merek" in ql:
            short = target.nama.split(" - ")[1] if " - " in target.nama else target.nama
            brand = target.nama.split(" - ")[0] if " - " in target.nama else (target.kode or "-")
            return short + " dari brand/merk: " + brand
        if "lain" in ql:
            brand = target.nama.split(" - ")[0] if " - " in target.nama else None
            if brand:
                others = acak([p for p in produk_list if p.nama.startswith(brand + " -") and p.nama != target.nama], 5)
                if others:
                    return "Produk lain dari " + brand + ":\n" + "\n".join(str(i + 1) + ". " + p.nama for i, p in enumerate(others))
            return "Tidak ada produk lain dari brand ini."
        if "ada" in ql or "mengandung" in ql or "pakai" in ql or "pake" in ql:
            nts_low = (N.get(target.nama) or "").lower()
            bad = STOP_WORDS + ["apakah", "ada", "nya", "mengandung", "pakai", "pake", "tidak", "gak", "apa", "notes", "aroma", "wangi"]
            sisa = [w for w in re.split("[^a-z0-9]+", ql) if len(w) >= 3 and w not in bad]
            ntoks_t = set(re.split("[^a-z0-9]+", target.nama.lower()))
            sisa = [w for w in sisa if w not in ntoks_t]
            if sisa:
                ing = sisa[0]
                terms = NOTE_SYNONYMS.get(ing, [ing])
                for tm in terms:
                    if tm in nts_low:
                        return "Ya, " + target.nama + " mengandung " + ing + ".\n" + format_notes(N.get(target.nama))
                return "Tidak ada " + ing + " di " + target.nama + ".\nNotesnya:\n" + format_notes(N.get(target.nama))
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
            out += "\n" + format_notes(nts)
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
        omzet, modal, keluar, laba, margin = hitung_laba_ai(month_start, date.today(), transaksi_list, pengeluaran_list, produk_list)
        return "Laba bulan ini:\nOmzet " + rp(omzet) + "\nModal (HPP) " + rp(modal) + "\nPengeluaran " + rp(keluar) + "\nKeuntungan " + rp(laba) + "\nMargin " + str(int(margin)) + "%\n\n(Sinkron dengan menu Laba Rugi)"
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
            for w in ["parfume", "parfum", "notes", "note", "aroma", "wangi", "apa", "saja", "yang", "ini", "dengan", "laris", "terlaris", "hari", "bulan", "minggu", "ada", "nya", "apakah", "mengandung", "pakai", "pake", "tidak", "gak", "punya", "dan", "atau", "di", "?"]:
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
    for p in produk_list:
        for w in re.split("[^a-z0-9]+", p.nama.lower()):
            if len(w) >= 7 and w in ql:
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

def jawab_mirip(tgt, produk_list):
    my_notes = (N.get(tgt.nama) or "").lower()
    tokens = set(w for w in re.split("[^a-z]+", my_notes) if len(w) > 3)
    scores = []
    for p in produk_list:
        if p.nama == tgt.nama:
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
        return "Tidak ditemukan parfum mirip " + tgt.nama + "."
    out = "Notes menyerupai " + tgt.nama + ":\n"
    for i, (s, p) in enumerate(top):
        out += str(i + 1) + ". " + p.nama + " (" + G.get(p.nama, "unisex") + ")\n"
    return out


def cocok_scope(p, scope, nilai):
    v = (nilai or "").strip().upper()
    if scope == "SEMUA":
        return True
    if scope == "KODE":
        return (p.kode or "").upper() == v
    if scope == "KATEGORI":
        return (p.kategori or "").upper() == v
    return False


@app.post("/harga/preview")
def harga_preview(
    scope: str = Form(...),
    nilai: str = Form(""),
    persen: float = Form(0),
    db: Session = Depends(get_db),
):
    rows = []
    for p in db.query(models.Produk).all():
        if cocok_scope(p, scope, nilai):
            baru = bulat_harga((p.harga or 0) * (100 + persen) / 100)
            rows.append({"nama": p.nama, "lama": p.harga, "baru": baru})
    return {"rows": rows[:20], "total": len(rows)}


@app.post("/harga/terapkan")
def harga_terapkan(
    scope: str = Form(...),
    nilai: str = Form(""),
    persen: float = Form(0),
    db: Session = Depends(get_db),
):
    n = 0
    for p in db.query(models.Produk).all():
        if cocok_scope(p, scope, nilai):
            p.harga = float(bulat_harga((p.harga or 0) * (100 + persen) / 100))
            n += 1
    db.commit()
    return {"n": n}

def split_tunai_non(t):
    tun = t.p_tunai or 0.0
    non = t.p_nontunai or 0.0
    if tun == 0 and non == 0:
        met = (t.metode or "").upper()
        if ("NON" in met) or ("QRIS" in met) or ("EDC" in met) or ("TRANSFER" in met):
            non = t.total or 0
        else:
            tun = t.total or 0
    return tun, non


def transaksi_valid(db):
    return db.query(models.Transaksi).filter((models.Transaksi.void == None) | (models.Transaksi.void == 0)).all()

def format_notes(s):
    if not s:
        return "-"
    if " | " not in s:
        return s
    return s.replace(" | ", "\n").replace("ASLI: ", "Produk asli: ").replace("TOP: ", "Top notes: ").replace("MID: ", "Middle notes: ").replace("BASE: ", "Base notes: ").replace("ACCORD: ", "Main accords: ").replace("LONG: ", "Longevity: ").replace("SILL: ", "Sillage: ")


@app.get("/produk/fetch_notes/{produk_id}")
def fetch_notes_online(produk_id: int, refresh: int = 0, db: Session = Depends(get_db)):
    from app import fragella
    produk = db.get(models.Produk, produk_id)
    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")
    existing = N.get(produk.nama)
    if existing and refresh == 0:
        return {"ok": True, "notes": existing, "gratis": True}
    text, err = fragella.cari_notes_online(produk.nama)
    if err:
        return {"ok": False, "pesan": err}
    N[produk.nama] = text
    try:
        with open("app/notes_data.py", "a", encoding="utf-8") as f:
            f.write('N["' + produk.nama.replace('"', "'") + '"] = "' + text.replace('"', "'") + '"\n')
    except Exception:
        pass
    return {"ok": True, "notes": text, "gratis": False}
@app.get("/produk/{produk_id}")
def produk_detail(produk_id: int, request: Request, db: Session = Depends(get_db)):
    produk = db.get(models.Produk, produk_id)
    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")
    gerakan = []
    for t in db.query(models.Transaksi).order_by(models.Transaksi.id.desc()).all():
        kode = t.kode_trx or ("TRX-" + str(t.id))
        for it in json.loads(t.items):
            if it["nama"] == produk.nama:
                if t.void:
                    gerakan.append({"waktu": t.dibuat, "jenis": "MASUK", "jumlah": it["jumlah"], "ket": "VOID " + kode})
                else:
                    gerakan.append({"waktu": t.dibuat, "jenis": "KELUAR", "jumlah": it["jumlah"], "ket": "TRX " + kode})
    for m in db.query(models.StokMasuk).filter_by(nama=produk.nama).order_by(models.StokMasuk.id.desc()).all():
        gerakan.append({"waktu": m.dibuat, "jenis": "MASUK", "jumlah": m.jumlah, "ket": m.keterangan or "MASUK BARANG"})
    gerakan.sort(key=lambda x: x["waktu"], reverse=True)
    total_keluar = sum(g["jumlah"] for g in gerakan if g["jenis"] == "KELUAR")
    total_masuk = sum(g["jumlah"] for g in gerakan if g["jenis"] == "MASUK")
    return templates.TemplateResponse(
        request,
        "produk_detail.html",
        {
            "produk": produk,
            "gender": G.get(produk.nama, "unisex"),
            "notes": format_notes(N.get(produk.nama)) or "Belum ada notes.",
            "gerakan": gerakan,
            "total_keluar": total_keluar,
            "total_masuk": total_masuk,
        },
    )


@app.post("/dashboard/restock/{produk_id}")
async def dashboard_restock(produk_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    jumlah = int(data.get("jumlah") or 0)
    harga_modal = float(data.get("harga_modal") or 0)
    keterangan = data.get("keterangan") or "Restock Dashboard"

    produk = db.get(models.Produk, produk_id)

    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")

    if jumlah <= 0:
        return JSONResponse(
            {"ok": False, "detail": "Jumlah harus lebih dari 0"},
            status_code=400
        )

    stok_lama = produk.stok or 0

    produk.stok = stok_lama + jumlah

    if harga_modal > 0:
        produk.harga_modal = harga_modal

    db.add(models.StokMasuk(
        nama=produk.nama,
        jumlah=jumlah,
        jenis="MASUK",
        stok_lama=stok_lama,
        stok_baru=produk.stok,
        selisih=jumlah,
        keterangan=keterangan
    ))

    db.add(models.Pengeluaran(
        keterangan="Restock " + produk.nama,
        jumlah=jumlah * harga_modal
    ))

    db.commit()

    return {"ok": True}


@app.post("/produk/{produk_id}/masuk")
def stok_masuk(produk_id: int, jumlah: int = Form(...), keterangan: str = Form(""), db: Session = Depends(get_db)):
    produk = db.get(models.Produk, produk_id)
    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")
    produk.stok = (produk.stok or 0) + jumlah
    db.add(models.StokMasuk(
        nama=produk.nama,
        jumlah=jumlah,
        jenis="MASUK",
        keterangan=keterangan
    ))
    db.commit()
    return RedirectResponse("/produk/" + str(produk_id), status_code=303)

@app.post("/stok/masuk_massal")
async def masuk_massal(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    total = 0
    n = 0
    kode_beli = "BELI-" + datetime.now().strftime("%d%m%y") + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))

    for row in data:
        nama = (row.get("nama") or "").strip()
        try:
            jumlah = int(row.get("jumlah") or 0)
            total_invoice = float(row.get("total") or 0)
            harga_modal = total_invoice / jumlah if jumlah > 0 else 0
        except Exception:
            continue
        if not nama or jumlah <= 0:
            continue
        p = db.query(models.Produk).filter_by(nama=nama).first()
        if not p:
            continue
        p.stok = (p.stok or 0) + jumlah

        # update harga modal saja, harga jual tetap
        p.harga_modal = harga_modal

        db.add(models.StokMasuk(
            nama=nama,
            jumlah=jumlah,
            jenis="MASUK",
            kode_beli=kode_beli,
            keterangan=
            "BELI " + str(jumlah) +
            " pcs TOTAL Rp " + str(int(total_invoice)) +
            " MODAL/PCS Rp " + str(int(harga_modal))
        ))

        total += total_invoice
        n += 1
    if n > 0:
        ket = "Pembelian stok massal (" + str(n) + " produk)"
        peng = models.Pengeluaran()
        if hasattr(peng, "keterangan"):
            peng.keterangan = ket
        elif hasattr(peng, "nama"):
            peng.nama = ket
        peng.jumlah = total
        peng.kode_beli = kode_beli
        db.add(peng)
    db.commit()
    return {"ok": True, "total": total, "n": n}






@app.get("/pembelian/{id}")
def detail_pembelian(id: int, request: Request, db: Session = Depends(get_db)):
    pembelian = db.get(models.Pembelian, id)

    if not pembelian:
        raise HTTPException(404, "Pembelian tidak ditemukan")

    detail = db.query(models.PembelianDetail).filter_by(
        pembelian_id=id
    ).all()

    return templates.TemplateResponse(
        request,
        "detail_pembelian.html",
        {
            "pembelian": pembelian,
            "detail": detail
        }
    )

@app.post("/pembelian/draft")
async def buat_pembelian_draft(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    kode_beli = "BELI-" + datetime.now().strftime("%d%m%y") + "-" + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=4)
    )

    total = 0
    detail = []

    for row in data:
        nama = (row.get("nama") or "").strip()

        try:
            jumlah = int(row.get("jumlah") or 0)
            invoice = float(row.get("total") or 0)
        except Exception:
            continue

        if not nama or jumlah <= 0:
            continue

        p = db.query(models.Produk).filter_by(nama=nama).first()

        if not p:
            continue

        modal_baru = invoice / jumlah

        detail.append({
            "produk_id": p.id,
            "nama": p.nama,
            "jumlah": jumlah,
            "invoice": invoice,
            "lama": p.harga_modal or 0,
            "baru": modal_baru
        })

        total += invoice

    if not detail:
        return {"ok": False, "pesan": "Tidak ada data"}

    pembelian = models.Pembelian(
        kode_beli=kode_beli,
        total=total,
        status="DRAFT"
    )

    db.add(pembelian)
    db.flush()

    for d in detail:
        db.add(models.PembelianDetail(
            pembelian_id=pembelian.id,
            produk_id=d["produk_id"],
            nama=d["nama"],
            jumlah_ml=d["jumlah"],
            total_invoice=d["invoice"],
            harga_modal_lama=d["lama"],
            harga_modal_baru=d["baru"]
        ))

    db.commit()

    return {
        "ok": True,
        "kode_beli": kode_beli,
        "total": total,
        "jumlah_produk": len(detail)
    }





@app.post("/pembelian/update_detail/{detail_id}")
async def update_detail_pembelian(detail_id: int, request: Request, db: Session = Depends(get_db)):

    data = await request.json()

    detail = db.get(models.PembelianDetail, detail_id)

    if not detail:
        raise HTTPException(404, "Detail pembelian tidak ditemukan")

    jumlah = int(data.get("jumlah") or 0)
    total_invoice = float(data.get("total_invoice") or 0)

    if jumlah <= 0:
        return {"ok": False, "pesan": "Jumlah tidak valid"}

    detail.jumlah_ml = jumlah
    detail.total_invoice = total_invoice
    detail.harga_modal_baru = total_invoice / jumlah

    pembelian = db.get(models.Pembelian, detail.pembelian_id)

    if pembelian:
        semua = db.query(models.PembelianDetail).filter_by(
            pembelian_id=pembelian.id
        ).all()

        pembelian.total = sum(
            x.total_invoice or 0 for x in semua
        )

    db.commit()

    return {
        "ok": True,
        "modal_baru": detail.harga_modal_baru
    }


@app.post("/pembelian/setujui/{id}")
def setujui_pembelian(id: int, db: Session = Depends(get_db)):

    pembelian = db.get(models.Pembelian, id)

    if not pembelian:
        raise HTTPException(404, "Pembelian tidak ditemukan")

    if pembelian.status != "DRAFT":
        return RedirectResponse(
            "/pembelian",
            status_code=303
        )

    detail = db.query(models.PembelianDetail).filter_by(
        pembelian_id=id
    ).all()

    for d in detail:
        produk = db.get(models.Produk, d.produk_id)

        if produk:
            stok_lama = produk.stok or 0

            produk.stok += d.jumlah_ml
            produk.harga_modal = d.harga_modal_baru

            db.add(models.StokMasuk(
                nama=produk.nama,
                jumlah=d.jumlah_ml,
                jenis="MASUK",
                kode_beli=pembelian.kode_beli,
                stok_lama=stok_lama,
                stok_baru=produk.stok,
                selisih=d.jumlah_ml,
                keterangan="Pembelian " + pembelian.kode_beli
            ))

    db.add(models.Pengeluaran(
        keterangan="Pembelian " + pembelian.kode_beli,
        kode_beli=pembelian.kode_beli,
        jenis="PEMBELIAN",
        status="AKTIF",
        jumlah=pembelian.total
    ))

    pembelian.status = "SELESAI"

    db.commit()

    return RedirectResponse(
        "/pembelian",
        status_code=303
    )


@app.post("/pembelian/void/{id}")
def void_pembelian(id: int, db: Session = Depends(get_db)):

    pembelian = db.get(models.Pembelian, id)

    if not pembelian:
        raise HTTPException(404, "Pembelian tidak ditemukan")

    if pembelian.status != "SELESAI":
        return RedirectResponse(
            "/pembelian",
            status_code=303
        )

    detail = db.query(models.PembelianDetail).filter_by(
        pembelian_id=id
    ).all()


    for d in detail:

        produk = db.get(models.Produk, d.produk_id)

        if produk:

            stok_lama = produk.stok or 0

            produk.stok -= d.jumlah_ml

            # kembalikan harga modal sebelum pembelian
            produk.harga_modal = d.harga_modal_lama

            db.add(models.StokMasuk(
                nama=produk.nama,
                jumlah=-d.jumlah_ml,
                jenis="VOID PEMBELIAN",
                kode_beli=pembelian.kode_beli,
                stok_lama=stok_lama,
                stok_baru=produk.stok,
                selisih=-d.jumlah_ml,
                keterangan="VOID Pembelian " + pembelian.kode_beli
            ))


    peng = db.query(models.Pengeluaran).filter_by(
        kode_beli=pembelian.kode_beli
    ).first()

    if peng:
        peng.status = "VOID"

    pembelian.status = "VOID"

    db.commit()

    return RedirectResponse(
        "/pembelian",
        status_code=303
    )


@app.post("/stok/update_massal")
async def update_stok_massal(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    n = 0
    from datetime import datetime

    for row in data:
        try:
            produk_id = int(row.get("id"))
            stok_baru = int(row.get("stok"))
        except Exception:
            continue

        produk = db.query(models.Produk).filter_by(id=produk_id).first()

        if produk:
            stok_lama = produk.stok or 0
            selisih = stok_baru - stok_lama

            if selisih != 0:
                db.add(
                    models.StokMasuk(
                        nama=produk.nama,
                        jumlah=selisih,
                        jenis="KOREKSI STOK",
                        stok_lama=stok_lama,
                        stok_baru=stok_baru,
                        selisih=selisih,
                        keterangan="STOCK OPNAME " + datetime.now().strftime("%d/%m/%Y %H:%M")
                    )
                )

            produk.stok = stok_baru
            n += 1

    db.commit()

    return {
        "ok": True,
        "n": n
    }


@app.post("/pengeluaran/cepat")
async def pengeluaran_cepat(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    try:
        jumlah = float(data.get("jumlah") or 0)
    except Exception:
        jumlah = 0
    ket = (data.get("keterangan") or "").strip()
    if jumlah <= 0 or not ket:
        return {"ok": False}
    peng = models.Pengeluaran()
    if hasattr(peng, "keterangan"):
        peng.keterangan = ket
    elif hasattr(peng, "nama"):
        peng.nama = ket
    peng.jumlah = jumlah
    db.add(peng)
    db.commit()
    backup_otomatis()
    return {"ok": True}

def buat_ringkasan(db):
    from datetime import date as _date
    today = _date.today()
    trx = [t for t in transaksi_valid(db) if t.dibuat.date() == today]
    omzet = sum(t.total or 0 for t in trx)
    tunai = sum(split_tunai_non(t)[0] for t in trx)
    nontunai = sum(split_tunai_non(t)[1] for t in trx)
    satuan = {"BIBIT": "ML", "BOTOL": "PCS", "CAMPURAN": "ML", "AKSESORIS": "ML"}
    kat = {}
    for t in trx:
        for it in json.loads(t.items):
            p = db.query(models.Produk).filter_by(nama=it["nama"]).first()
            k = ((p.kategori or "LAIN").upper()) if p else "LAIN"
            harga_it = it.get("harga") or (p.harga if p else 0) or 0
            a = kat.setdefault(k, {"rp": 0.0, "qty": 0})
            a["rp"] += harga_it * it["jumlah"] - (it.get("diskon") or 0)
            a["qty"] += it["jumlah"]
    peng_list = []
    total_peng = 0.0
    for pg in db.query(models.Pengeluaran).filter(models.Pengeluaran.status != 'VOID').all():
        if pg.dibuat.date() == today:
            ket = pg.keterangan if hasattr(pg, "keterangan") else pg.nama
            peng_list.append((ket or "PENGELUARAN", pg.jumlah or 0))
            total_peng += pg.jumlah or 0

    def rp(x):
        return "Rp " + format(int(round(x)), ",").replace(",", ".")

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    L = []
    L.append("MEKAR SARI")
    L.append("Refill Perfumery")
    L.append("-----------------------------------------")
    L.append("Tanggal : " + now)
    L.append("-----------------------------------------")
    for k in ["BIBIT", "BOTOL", "CAMPURAN", "AKSESORIS"] + sorted([x for x in kat if x not in ("BIBIT", "BOTOL", "CAMPURAN", "AKSESORIS")]):
        a = kat.get(k)
        if not a or a["rp"] <= 0:
            continue
        L.append("- " + k + " : " + rp(a["rp"]) + " / " + str(a["qty"]) + " " + satuan.get(k, "PCS"))
    L.append("-----------------------------------------")
    L.append("PENGELUARAN")
    if peng_list:
        for ket, j in peng_list:
            L.append("- " + str(ket) + " " + rp(j))
    else:
        L.append("- Tidak ada pengeluaran")
    L.append("-----------------------------------------")
    L.append("METODE PEMBAYARAN")
    L.append("- TUNAI : " + rp(tunai))
    L.append("- NON-TUNAI : " + rp(nontunai))
    L.append("-----------------------------------------")
    L.append("- TOTAL OMZET : " + rp(omzet))
    return {"text": "\n".join(L), "omzet": omzet, "tunai": tunai, "nontunai": nontunai, "pengeluaran": total_peng}

MOODS = {
    "manis": ["sweet", "vanilla", "caramel", "gourmand"],
    "segar": ["citrus", "fresh", "aquatic", "mint"],
    "malam": ["warm", "spicy", "oud", "amber"],
    "siang": ["citrus", "fresh", "aquatic", "light"],
    "kantor": ["fresh", "clean", "light", "citrus"],
    "romantis": ["floral", "rose", "romantic"],
    "sport": ["sporty", "fresh", "green"],
    "mewah": ["luxurious", "woody", "smoky"],
}

def jawab_fitur(q, db):
    import re as _re
    ql = q.lower()
    produk_list = db.query(models.Produk).all()

    def rp(x):
        return "Rp " + format(int(round(x)), ",").replace(",", ".")

    if "briefing" in ql:
        from datetime import date as _d, timedelta as _td
        today = _d.today()
        yest = today - _td(days=1)
        tr = transaksi_valid(db)
        om_y = sum(t.total or 0 for t in tr if t.dibuat.date() == yest)
        n_y = sum(1 for t in tr if t.dibuat.date() == yest)
        om_t = sum(t.total or 0 for t in tr if t.dibuat.date() == today)
        jual = {}
        for t in tr:
            if t.dibuat.date() == yest:
                for it in json.loads(t.items):
                    jual[it["nama"]] = jual.get(it["nama"], 0) + it["jumlah"]
        top = sorted(jual.items(), key=lambda x: -x[1])[:3]
        rendah = [p for p in produk_list if (p.stok or 0) < 10][:6]
        out = "BRIEFING PAGI\n"
        out += "Kemarin: omzet " + rp(om_y) + " dari " + str(n_y) + " transaksi.\n"
        out += "Hari ini sejauh ini: " + rp(om_t) + ".\n"
        if top:
            out += "Terlaris kemarin: " + ", ".join(a[0] + " (" + str(a[1]) + " pcs)" for a in top) + ".\n"
        if rendah:
            out += "Stok menipis: " + ", ".join(p.nama + " (" + str(p.stok) + ")" for p in rendah) + ".\n"
        out += "Fokus hari ini: amankan stok terlaris, tawarkan parfum mirip yang terlaris, dan jaga stok bahan refill."
        return out

    if "untung" in ql or "simulasi" in ql or "profit" in ql:
        tgt = cari_produk(ql, produk_list)
        if tgt:
            nums = [int(w) for w in _re.findall(r"\d+", q)]
            qty = nums[0] if nums else 1
            per = (tgt.harga or 0) - (tgt.harga_modal or 0)
            out = "SIMULASI UNTUNG " + tgt.nama + "\n"
            out += "Jual " + rp(tgt.harga or 0) + " - modal " + rp(tgt.harga_modal or 0) + " = untung " + rp(per) + " / pcs\n"
            out += "Kalau terjual " + str(qty) + " pcs = UNTUNG " + rp(per * qty)
            return out

    for mood, keys in MOODS.items():
        if mood in ql and ("rekom" in ql or "cocok" in ql or "acara" in ql or "untuk" in ql or "parfum" in ql or "buat" in ql):
            hits = []
            for p in produk_list:
                nts = (N.get(p.nama) or "").lower()
                if any(k in nts for k in keys):
                    hits.append(p)
            if hits:
                hits.sort(key=lambda p: -(p.stok or 0))
                out = "Rekomendasi suasana '" + mood + "':\n"
                for i, p in enumerate(hits[:5], 1):
                    out += str(i) + ". " + p.nama + " (stok " + str(p.stok) + ", " + rp(p.harga or 0) + ")\n"
                out += "\nMau saya carikan yang mirip? Jawab: ya"
                return out
    return None


@app.get("/struk/{trx_id}")
def struk_page(trx_id: int, request: Request, db: Session = Depends(get_db)):
    t = db.get(models.Transaksi, trx_id)

    if not t:
        raise HTTPException(404, "Transaksi tidak ditemukan")

    teks = buat_teks_struk(db, t)

    items = json.loads(t.items)

    for it in items:
        if not it.get("harga"):
            pr = db.query(models.Produk).filter_by(nama=it["nama"]).first()
            it["harga"] = pr.harga if pr else 0

    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    ag = db.get(models.Anggota, pl.anggota_id) if pl else None

    return templates.TemplateResponse(
        request,
        "struk.html",
        {
            "t": t,
            "items": items,
            "ag": ag,
            "pl": pl,
            "teks": teks,
            "wa_url": "/struk/" + str(trx_id) + "/wa",
            "wa_url": "/struk/" + str(t.id) + "/wa"
        }
    )


@app.get("/struk/{trx_id}/print")
def struk_print(trx_id: int, request: Request, ulang: str = "", db: Session = Depends(get_db)):
    t = db.get(models.Transaksi, trx_id)
    if not t:
        raise HTTPException(404, "Struk tidak ditemukan")
    raw = json.loads(t.items)
    sub = 0.0
    for it in raw:
        if not it.get("harga"):
            pr = db.query(models.Produk).filter_by(nama=it["nama"]).first()
            it["harga"] = pr.harga if pr else 0
        sub += (it["harga"] or 0) * it["jumlah"] - (it.get("diskon") or 0)
    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    ag = db.get(models.Anggota, pl.anggota_id) if pl else None
    from datetime import datetime as _dt
    now = _dt.now()
    BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Des"]
    now_str = "%02d %s %d, %02d.%02d" % (now.day, BULAN[now.month - 1], now.year, now.hour, now.minute)
    return templates.TemplateResponse(request, "struk_print.html", {
        "t": t, "items": raw, "ag": ag, "pl": pl,
        "ulang": bool(ulang), "now_str": now_str, "sub": sub,
        "nontunai": any(x in (t.metode or "").upper() for x in ["NON", "QRIS", "GOPAY", "DANA", "TRANSFER", "EDC"])})



@app.get("/laporan/laba_rugi/excel")

def download_laba_rugi_excel(
    start_date: str = "",
    end_date: str = "",
    db: Session = Depends(get_db)
):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from io import BytesIO
    from datetime import datetime
    from fastapi.responses import StreamingResponse


    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_dt = date.today().replace(day=1)


    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_dt = date.today()


    hasil = hitung_laba(db, start_dt, end_dt)


    wb = Workbook()
    ws = wb.active
    ws.title = "Laba Rugi"


    # IDENTITAS
    ws["A1"] = "CABANG"
    ws["B1"] = ": MEKAR SARI"

    ws["A2"] = "LAPORAN"
    ws["B2"] = ": LABA RUGI"

    ws["A3"] = "PERIODE"
    ws["B3"] = (
        ": "
        + start_dt.strftime("%d-%m-%Y")
        + " s/d "
        + end_dt.strftime("%d-%m-%Y")
    )


    ws["A5"] = "DETAIL LABA RUGI"


    row = 7

    header = [
        "TANGGAL",
        "TRANSAKSI",
        "OMZET",
        "HPP",
        "PENGELUARAN",
        "LABA"
    ]


    for i,h in enumerate(header,1):
        ws.cell(row,i,h)
        ws.cell(row,i).font = Font(bold=True)


    row += 1

    total_laba = 0


    for tanggal, r in sorted(hasil.items()):

        laba = (
            r["net"]
            - r["hpp"]
            - r["op"]
        )

        ws.cell(row,1,str(tanggal))
        ws.cell(row,2,r["trx"])
        ws.cell(row,3,r["net"])
        ws.cell(row,4,r["hpp"])
        ws.cell(row,5,r["op"])
        ws.cell(row,6,laba)

        total_laba += laba

        row += 1


    row += 1

    ws.cell(row,1,"TOTAL LABA")
    ws.cell(row,6,total_laba)


    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 15


    file = BytesIO()
    wb.save(file)
    file.seek(0)


    return StreamingResponse(
        file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            "attachment; filename=laporan-laba-rugi.xlsx"
        }
    )



def download_transaksi_excel(
    start_date: str = "",
    end_date: str = "",
    db: Session = Depends(get_db)
):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from io import BytesIO
    from datetime import datetime
    from fastapi.responses import StreamingResponse


    if start_date:
        start_dt = datetime.strptime(start_date,"%Y-%m-%d").date()
    else:
        start_dt = date.today().replace(day=1)


    if end_date:
        end_dt = datetime.strptime(end_date,"%Y-%m-%d").date()
    else:
        end_dt = date.today()


    data = [
        t for t in transaksi_valid(db)
        if start_dt <= t.dibuat.date() <= end_dt
    ]


    wb = Workbook()
    ws = wb.active
    ws.title = "Penjualan"


    ws["A1"] = "CABANG"
    ws["B1"] = ": MEKAR SARI"

    ws["A2"] = "LAPORAN"
    ws["B2"] = ": PENJUALAN"

    ws["A3"] = "PERIODE"
    ws["B3"] = (
        ": "
        + start_dt.strftime("%d-%m-%Y")
        + " s/d "
        + end_dt.strftime("%d-%m-%Y")
    )


    ws["A5"] = "DETAIL PENJUALAN"


    row = 7

    header = [
        "NO",
        "KODE TRANSAKSI",
        "TANGGAL",
        "METODE",
        "TOTAL",
        "DISKON",
        "BAYAR",
        "STATUS"
    ]


    for i,h in enumerate(header,1):
        ws.cell(row,i,h)
        ws.cell(row,i).font = Font(bold=True)


    row += 1
    total = 0


    for no,t in enumerate(data,1):

        ws.cell(row,1,no)
        ws.cell(row,2,t.kode_trx or "")
        ws.cell(row,3,t.dibuat.strftime("%d-%m-%Y %H:%M"))
        ws.cell(row,4,t.metode or "TUNAI")
        ws.cell(row,5,t.total or 0)
        ws.cell(row,6,t.total_diskon or 0)
        ws.cell(row,7,t.bayar or 0)
        ws.cell(row,8,t.status or "")

        total += t.total or 0

        row += 1


    row += 1

    ws.cell(row,1,"TOTAL PENJUALAN SELESAI")
    ws.cell(row,5,total)


    for col in range(1,9):
        ws.column_dimensions[
            chr(64+col)
        ].width = 18


    file = BytesIO()
    wb.save(file)
    file.seek(0)


    return StreamingResponse(
        file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            "attachment; filename=laporan-penjualan.xlsx"
        }
    )


def riwayat_hari(request: Request, tanggal: str = "", db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    today = date.today()
    if tanggal:
        try:
            d = datetime.strptime(tanggal, "%Y-%m-%d").date()
        except Exception:
            d = today
    else:
        d = today
    if d > today:
        d = today
    trx = [t for t in db.query(models.Transaksi).order_by(models.Transaksi.id.desc()).all() if t.dibuat.date() == d]
    total_hari = sum(t.total or 0 for t in trx if not t.void)
    rows = []
    for t in trx:
        rows.append({
            "t": t,
            "items_str": "; ".join(it["nama"] + " x" + str(it["jumlah"]) for it in json.loads(t.items)),
            "void_action": "/transaksi/void/" + str(t.id),
        })
    return templates.TemplateResponse(request, "riwayat_hari.html", {
        "rows": rows, "total_hari": total_hari, "today": today, "d": d,
        "prev_date": (d - timedelta(days=1)).isoformat(),
        "next_date": (d + timedelta(days=1)).isoformat(),
        "is_today": d == today})



@app.get("/laporan-lengkap")
def laporan_lengkap():
    return RedirectResponse(
        "/laporan",
        status_code=303
    )


@app.get("/laporan-lengkap/excel")

def laporan_lengkap_excel(
    start_date: str = "",
    end_date: str = "",
    db: Session = Depends(get_db)
):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from io import BytesIO
    from datetime import datetime
    from fastapi.responses import StreamingResponse


    if start_date:
        start_dt = datetime.strptime(start_date,"%Y-%m-%d").date()
    else:
        start_dt = date.today().replace(day=1)


    if end_date:
        end_dt = datetime.strptime(end_date,"%Y-%m-%d").date()
    else:
        end_dt = date.today()


    transaksi = [
        t for t in transaksi_valid(db)
        if start_dt <= t.dibuat.date() <= end_dt
    ]


    pembelian = [
        p for p in db.query(models.Pembelian).all()
        if p.dibuat and start_dt <= p.dibuat.date() <= end_dt
        and p.status=="SELESAI"
    ]


    pengeluaran = [
        p for p in db.query(models.Pengeluaran).all()
        if p.dibuat and start_dt <= p.dibuat.date() <= end_dt
        and p.status!="VOID"
    ]


    total_jual = sum(t.total or 0 for t in transaksi)
    total_beli = sum(p.total or 0 for p in pembelian)
    total_keluar = sum(p.jumlah or 0 for p in pengeluaran)


    laba = total_jual - total_beli - total_keluar


    wb = Workbook()
    ws = wb.active
    ws.title="Laporan"


    ws["A1"]="CABANG"
    ws["B1"]=": MEKAR SARI"

    ws["A2"]="LAPORAN"
    ws["B2"]=": LAPORAN LENGKAP"

    ws["A3"]="PERIODE"
    ws["B3"]=": "+start_dt.strftime("%d-%m-%Y")+" s/d "+end_dt.strftime("%d-%m-%Y")


    ws["A5"]="RINGKASAN"


    ringkasan=[
        ("TOTAL TRANSAKSI",len(transaksi)),
        ("TOTAL PENJUALAN",total_jual),
        ("TOTAL PEMBELIAN",total_beli),
        ("TOTAL PENGELUARAN",total_keluar),
        ("LABA BERSIH",laba)
    ]


    row=6

    for a,b in ringkasan:
        ws.cell(row,1,a)
        ws.cell(row,2,b)
        row+=1


    row+=2

    ws.cell(row,1,"DETAIL HARIAN")
    row+=2


    header=[
        "NO",
        "TANGGAL",
        "JUMLAH TRX",
        "PENJUALAN"
    ]


    for i,h in enumerate(header,1):
        ws.cell(row,i,h)
        ws.cell(row,i).font=Font(bold=True)


    row+=1

    harian={}

    for t in transaksi:
        d=t.dibuat.date()
        harian.setdefault(d,0)
        harian[d]+=t.total or 0


    for no,(tgl,total) in enumerate(harian.items(),1):
        ws.cell(row,1,no)
        ws.cell(row,2,tgl.strftime("%d-%m-%Y"))
        ws.cell(row,4,total)
        row+=1


    for col in range(1,6):
        ws.column_dimensions[
            chr(64+col)
        ].width=20


    file=BytesIO()
    wb.save(file)
    file.seek(0)


    return StreamingResponse(
        file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            "attachment; filename=laporan-lengkap.xlsx"
        }
    )


def _rp_filter(v):
    try:
        return format(int(round(float(v))), ",").replace(",", ".")
    except Exception:
        return "0"
templates.env.filters["rp"] = _rp_filter


@app.get("/anggota")
def anggota_page(request: Request, db: Session = Depends(get_db)):
    list_a = db.query(models.Anggota).order_by(models.Anggota.id.desc()).all()
    return templates.TemplateResponse(request, "anggota.html", {"anggota_list": list_a})

@app.post("/anggota/simpan")
def anggota_simpan(nama: str = Form(...), no_hp: str = Form(...), db: Session = Depends(get_db)):
    import random as _rnd, string as _str
    nom = "MS-" + "".join(_rnd.choices(_str.ascii_uppercase + _str.digits, k=6))
    db.add(models.Anggota(nama=nama.strip(), no_hp=no_hp.strip(), nomor_member=nom, poin=0))
    db.commit()
    return RedirectResponse("/anggota", status_code=303)

@app.get("/anggota/list")
def anggota_list(db: Session = Depends(get_db)):
    rows = db.query(models.Anggota).all()
    return [{"id": a.id, "label": (a.nama or "") + " | " + (a.nomor_member or ""), "poin": a.poin or 0} for a in rows]



@app.get("/struk/{trx_id}/wa")
def struk_wa(trx_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Transaksi, trx_id)
    if not t:
        raise HTTPException(404, "tidak ditemukan")
    text = buat_teks_struk(db, t)
    hp = ""
    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    if pl:
        ag = db.get(models.Anggota, pl.anggota_id)
        if ag:
            hp = ag.no_hp or ""
    digits = "".join(ch for ch in hp if ch.isdigit())
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    url = ("https://wa.me/" + digits + "?text=" if digits else "https://wa.me/?text=")
    return {"text": text, "url": url}


def _rpx(x):
    try:
        x = float(x)
    except Exception:
        x = 0.0
    return "Rp" + format(int(round(x)), ",").replace(",", ".")
templates.env.filters["rpx"] = _rpx



def rp0(x):
    return "Rp " + format(int(round(x)), ",").replace(",", ".")

def buat_teks_struk(db, t):
    L = []

    L.append("MEKAR SARI")
    L.append("Refill Perfumery")
    L.append("Jl. Mekar Sari No.5, Bekasi Jaya")
    L.append("Kota Bekasi")
    L.append("HP: 0821-1897-1096")
    L.append("--------------------------------")

    L.append("No : " + (t.kode_trx or ("TRX-" + str(t.id))))
    L.append("Waktu : " + t.dibuat.strftime("%d/%m/%Y %H:%M"))
    L.append("--------------------------------")

    L.append("DETAIL PEMBELIAN")

    for it in json.loads(t.items):
        L.append(it["nama"])
        L.append(
            str(it["jumlah"]) +
            " x " +
            rp0(it.get("harga") or 0) +
            " = " +
            rp0((it.get("harga") or 0) * it["jumlah"])
        )

    L.append("--------------------------------")
    L.append("TOTAL : " + rp0(t.total or 0))

    if t.poin_dipakai:
        L.append("POTONG POIN : -" + rp0(t.poin_dipakai))
        L.append("BAYAR AKHIR : " + rp0((t.total or 0) - (t.poin_dipakai or 0)))

    metode = (t.metode or "TUNAI")
    metode = metode.replace("POIN + NON-TUNAI (", "")
    metode = metode.replace(")", "")

    L.append("METODE : " + metode)

    if "TUNAI" in metode.upper():
        L.append("BAYAR : " + rp0(t.bayar or 0))
        L.append("KEMBALI : " + rp0(t.kembalian or 0))

    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    if pl:
        ag = db.get(models.Anggota, pl.anggota_id)
        if ag:
            L.append("")
            if pl.poin < 0:
                L.append("POIN DIPAKAI : " + rp0(abs(pl.poin)))
            elif pl.poin > 0:
                L.append("POIN TAMBAH : +" + format(int(pl.poin), ",").replace(",", "."))

            L.append("SISA POIN : " + format(int(ag.poin or 0), ",").replace(",", "."))

    L.append("--------------------------------")
    L.append("TERIMA KASIH")
    L.append("Simpan struk ini sebagai")
    L.append("bukti pembayaran yang sah.")

    return "\n".join(L)

