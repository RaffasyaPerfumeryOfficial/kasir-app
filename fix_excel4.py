import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

helper = '''
def hitung_laba(db, start_dt, end_dt):
    trx = [t for t in transaksi_valid(db) if start_dt <= t.dibuat.date() <= end_dt]
    rows = {}
    for t in trx:
        r = rows.setdefault(t.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0})
        item_disc = 0.0
        hpp_t = 0.0
        for it in json.loads(t.items):
            qty = it["jumlah"]
            harga = it.get("harga") or 0
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
    for pg in db.query(models.Pengeluaran).all():
        if start_dt <= pg.dibuat.date() <= end_dt:
            r = rows.setdefault(pg.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0})
            r["op"] += pg.jumlah or 0
    tot = {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0}
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


@app.post("/labarugi/pengeluaran")
def labarugi_pengeluaran(keterangan: str = Form(...), jumlah: float = Form(...), db: Session = Depends(get_db)):
    peng = models.Pengeluaran()
    if hasattr(peng, "keterangan"):
        peng.keterangan = keterangan
    elif hasattr(peng, "nama"):
        peng.nama = keterangan
    peng.jumlah = jumlah
    db.add(peng)
    db.commit()
    return RedirectResponse("/labarugi", status_code=303)


'''

pat_lr = re.compile(r'@app\.get\("/labarugi"\)[\s\S]*?(?=\n@app\.)')
assert pat_lr.search(s), "route labarugi lama tidak ketemu"
s = pat_lr.sub(lambda m: helper, s, count=1)

pat_ex = re.compile(r'@app\.get\("/laporan/laba_rugi/excel"\)[\s\S]*?(?=\n@app\.|\Z)')
assert pat_ex.search(s), "route excel tidak ketemu"
new_ex = '''@app.get("/laporan/laba_rugi/excel")
def download_laba_rugi_excel(start_date: str = "", end_date: str = "", db: Session = Depends(get_db)):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from io import BytesIO
    from datetime import datetime, timedelta
    from fastapi.responses import StreamingResponse
    if not start_date or not end_date:
        today = datetime.now().date()
        end_dt = today
        start_dt = today - timedelta(days=29)
    else:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    data = hitung_laba(db, start_dt, end_dt)
    tot = data["tot"]
    wb = Workbook()
    ws = wb.active
    ws.title = "Laba Rugi"
    ws["A1"] = "SALES COUNTER"
    ws["B1"] = "RIVALDI RAMDANI"
    ws["A2"] = "NO HP"
    ws["B2"] = "0853-2034-2037"
    ws["A3"] = "CAB"
    ws["B3"] = "MEKAR SARI"
    ws["A4"] = "PERIODE"
    ws["B4"] = start_dt.strftime("%d-%B-%Y").upper() + " SAMPAI " + end_dt.strftime("%d-%B-%Y").upper()
    bold = Font(bold=True)
    for r in range(1, 5):
        ws.cell(row=r, column=1).font = bold
    ws["A6"] = "LAPORAN LABA RUGI"
    ws["A6"].font = Font(bold=True, size=14)
    ws.merge_cells("A6:H6")
    ws["A6"].alignment = Alignment(horizontal="center")
    heads = ["No", "Tanggal", "Gross Sales", "Diskon", "Pendapatan", "Beban HPP", "Beban Operasional", "Laba Bersih"]
    for col, h in enumerate(heads, 1):
        c = ws.cell(row=8, column=col, value=h)
        c.font = bold
        c.alignment = Alignment(horizontal="center")
    row = 9
    for i, (d, r) in enumerate(data["rows"], 1):
        ws.cell(row=row, column=1, value=i)
        ws.cell(row=row, column=2, value=d.strftime("%d/%m/%Y"))
        ws.cell(row=row, column=3, value=r["gross"])
        ws.cell(row=row, column=4, value=r["disc"])
        ws.cell(row=row, column=5, value=r["net"])
        ws.cell(row=row, column=6, value=r["hpp"])
        ws.cell(row=row, column=7, value=r["op"])
        ws.cell(row=row, column=8, value=r["net"] - r["hpp"] - r["op"])
        row += 1
    row += 1
    ws.cell(row=row, column=2, value="TOTAL").font = bold
    ws.cell(row=row, column=3, value=tot["gross"]).font = bold
    ws.cell(row=row, column=4, value=tot["disc"]).font = bold
    ws.cell(row=row, column=5, value=tot["net"]).font = bold
    ws.cell(row=row, column=6, value=tot["hpp"]).font = bold
    ws.cell(row=row, column=7, value=tot["op"]).font = bold
    ws.cell(row=row, column=8, value=tot["net"] - tot["hpp"] - tot["op"]).font = bold
    for col, w in zip("ABCDEFGH", [6, 14, 14, 12, 14, 14, 18, 14]):
        ws.column_dimensions[col].width = w
    for r in ws.iter_rows(min_row=9, max_row=row, min_col=3, max_col=8):
        for c in r:
            if isinstance(c.value, (int, float)):
                c.number_format = "#,##0"
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    fn = "LabaRugi_" + start_dt.strftime("%Y%m%d") + "_" + end_dt.strftime("%Y%m%d") + ".xlsx"
    return StreamingResponse(out, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=" + fn})


'''
s = pat_ex.sub(lambda m: new_ex, s, count=1)
io.open(p, "w", encoding="utf-8").write(s)
print("route labarugi + excel baru ok")
