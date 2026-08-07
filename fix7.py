import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

s = s.replace("db.query(models.Transaksi).all()", "transaksi_valid(db)")

old_exp = "    transaksi_list = db.query(models.Transaksi).order_by(models.Transaksi.id).all()"
new_exp = "    transaksi_list = sorted(transaksi_valid(db), key=lambda t: t.id)"
assert old_exp in s, "export lama"
s = s.replace(old_exp, new_exp, 1)

pat = re.compile(r'@app\.get\("/riwayat"\)[\s\S]*?@app\.get\("/struk/\{trx_id\}"\)')
assert pat.search(s), "riwayat lama"
chunk = '''def filter_transaksi(semua, flt, dari, sampai, q):
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
    content = "\\ufeff" + "\\n".join(lines)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transaksi.csv"},
    )


@app.post("/transaksi/void/{trx_id}")
def void_transaksi(trx_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Transaksi, trx_id)
    if not t:
        raise HTTPException(404, "Transaksi tidak ditemukan")
    if t.void:
        return RedirectResponse("/riwayat", status_code=303)
    t.void = 1
    for it in json.loads(t.items):
        p = db.query(models.Produk).filter_by(nama=it["nama"]).first()
        if p:
            p.stok = (p.stok or 0) + it["jumlah"]
    db.commit()
    return RedirectResponse("/riwayat", status_code=303)


@app.get("/struk/{trx_id}")'''
s = pat.sub(lambda m: chunk, s, count=1)
io.open(p, "w", encoding="utf-8").write(s)
print("void backend ok")
