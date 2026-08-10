import io, re

# 1) Update hitung_laba di main.py (tambah pmsk)
m = io.open("app/main.py", encoding="utf-8").read()

m = m.replace(
    'r = rows.setdefault(t.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "trx": 0})',
    'r = rows.setdefault(t.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "pmsk": 0.0, "trx": 0})', 1)

m = m.replace(
    'r = rows.setdefault(pg.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "trx": 0})',
    'r = rows.setdefault(pg.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "pmsk": 0.0, "trx": 0})', 1)

anchor_pg = '            r["op"] += pg.jumlah or 0\n    for mm in db.query(models.RekapManual).all():\n'
new_pm = '            r["op"] += pg.jumlah or 0\n    for pm in db.query(models.Pemasukan).all():\n        if start_dt <= pm.dibuat.date() <= end_dt:\n            r = rows.setdefault(pm.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "pmsk": 0.0, "trx": 0})\n            r["pmsk"] += pm.jumlah or 0\n    for mm in db.query(models.RekapManual).all():\n'
m = m.replace(anchor_pg, new_pm, 1)

m = m.replace(
    'r = rows.setdefault(mm.tanggal, {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "trx": 0})',
    'r = rows.setdefault(mm.tanggal, {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "pmsk": 0.0, "trx": 0})', 1)

m = m.replace(
    'tot = {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "trx": 0}',
    'tot = {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "pmsk": 0.0, "trx": 0}', 1)

# 2) Ganti route Excel seluruhnya
pat_excel = re.compile(r'@app\.get\("/laporan/laba_rugi/excel"\)[\s\S]*?(?=\n@app\.)')
new_excel = '''@app.get("/laporan/laba_rugi/excel")
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
    ws.merge_cells("A6:J6")
    ws["A6"].alignment = Alignment(horizontal="center")
    heads = ["No", "Tanggal", "Gross Sales", "Diskon", "Pendapatan", "Pemasukan", "Beban HPP", "Beban Operasional", "Laba Bersih", "Trx"]
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
        ws.cell(row=row, column=6, value=r["pmsk"])
        ws.cell(row=row, column=7, value=r["hpp"])
        ws.cell(row=row, column=8, value=r["op"])
        ws.cell(row=row, column=9, value=r["net"] - r["hpp"] - r["op"] + r["pmsk"])
        ws.cell(row=row, column=10, value=r["trx"])
        row += 1
    row += 1
    ws.cell(row=row, column=2, value="TOTAL").font = bold
    ws.cell(row=row, column=3, value=tot["gross"]).font = bold
    ws.cell(row=row, column=4, value=tot["disc"]).font = bold
    ws.cell(row=row, column=5, value=tot["net"]).font = bold
    ws.cell(row=row, column=6, value=tot["pmsk"]).font = bold
    ws.cell(row=row, column=7, value=tot["hpp"]).font = bold
    ws.cell(row=row, column=8, value=tot["op"]).font = bold
    ws.cell(row=row, column=9, value=tot["net"] - tot["hpp"] - tot["op"] + tot["pmsk"]).font = bold
    ws.cell(row=row, column=10, value=tot["trx"]).font = bold
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    filename = "LabaRugi_" + start_dt.strftime("%Y%m%d") + "_" + end_dt.strftime("%Y%m%d") + ".xlsx"
    return StreamingResponse(out, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=" + filename})


'''
m, c_e = pat_excel.subn(new_excel, m, count=1)
assert c_e == 1, "route excel tidak ketemu"

# 3) Hapus route POST pengeluaran dari labarugi (opsional, tapi biar rapi)
m = m.replace('''@app.post("/labarugi/pengeluaran")
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



''', '', 1)

io.open("app/main.py", "w", encoding="utf-8").write(m)
print("main.py labarugi + excel ok")

# 4) Update template labarugi.html
T = io.open("templates/labarugi.html", encoding="utf-8").read()

old_cards = '''  <div class="card"><h3 style="color:var(--muted);font-size:13px">BEBAN OPERASIONAL</h3><p style="font-size:22px;font-weight:800;color:#d97706">Rp {{ "%0.0f"|format(tot.op) }}</p></div>
  <div class="card" style="border-left:4px solid var(--success)"><h3 style="color:var(--muted);font-size:13px">LABA BERSIH</h3><p style="font-size:22px;font-weight:800;color:var(--success)">Rp {{ "%0.0f"|format(tot.net - tot.hpp - tot.op) }}</p></div>'''
new_cards = '''  <div class="card"><h3 style="color:var(--muted);font-size:13px">BEBAN OPERASIONAL</h3><p style="font-size:22px;font-weight:800;color:#d97706">Rp {{ "%0.0f"|format(tot.op) }}</p></div>
  <div class="card"><h3 style="color:var(--muted);font-size:13px">PEMASUKAN</h3><p style="font-size:22px;font-weight:800;color:var(--success)">Rp {{ "%0.0f"|format(tot.pmsk) }}</p></div>
  <div class="card" style="border-left:4px solid var(--success)"><h3 style="color:var(--muted);font-size:13px">LABA BERSIH</h3><p style="font-size:22px;font-weight:800;color:var(--success)">Rp {{ "%0.0f"|format(tot.net - tot.hpp - tot.op + tot.pmsk) }}</p></div>'''
T = T.replace(old_cards, new_cards, 1)

old_form = '''  <div class="card">
    <h3>Catat Beban Operasional</h3>
    <form method="post" action="/labarugi/pengeluaran" style="display:flex;flex-direction:column;gap:8px;margin-top:10px">
      <input name="keterangan" placeholder="Keterangan (misal: beli botol, listrik)" required>
      <input name="jumlah" type="number" placeholder="Jumlah (Rp)" required>
      <button class="btn-danger" type="submit">Catat Pengeluaran</button>
    </form>
  </div>'''
T = T.replace(old_form, "", 1)

old_table = '''      <tr><th>Tanggal</th><th style="text-align:right">Gross</th><th style="text-align:right">Diskon</th><th style="text-align:right">Pendapatan</th><th style="text-align:right">HPP</th><th style="text-align:right">Operasional</th><th style="text-align:right">Laba</th><th style="text-align:right">Trx</th></tr>
      {% for d, r in rows %}
      <tr>
        <td>{{ d.strftime("%d/%m/%Y") }}</td>
        <td style="text-align:right">{{ "%0.0f"|format(r.gross) }}</td>
        <td style="text-align:right">{{ "%0.0f"|format(r.disc) }}</td>
        <td style="text-align:right">{{ "%0.0f"|format(r.net) }}</td>
        <td style="text-align:right">{{ "%0.0f"|format(r.hpp) }}</td>
        <td style="text-align:right">{{ "%0.0f"|format(r.op) }}</td>
        <td style="text-align:right"><strong>{{ "%0.0f"|format(r.net - r.hpp - r.op) }}</strong></td>
        <td style="text-align:right">{{ r.trx }}</td>
      </tr>'''
new_table = '''      <tr><th>Tanggal</th><th style="text-align:right">Gross</th><th style="text-align:right">Diskon</th><th style="text-align:right">Pendapatan</th><th style="text-align:right">Pemasukan</th><th style="text-align:right">HPP</th><th style="text-align:right">Operasional</th><th style="text-align:right">Laba</th><th style="text-align:right">Trx</th></tr>
      {% for d, r in rows %}
      <tr>
        <td>{{ d.strftime("%d/%m/%Y") }}</td>
        <td style="text-align:right">{{ "%0.0f"|format(r.gross) }}</td>
        <td style="text-align:right">{{ "%0.0f"|format(r.disc) }}</td>
        <td style="text-align:right">{{ "%0.0f"|format(r.net) }}</td>
        <td style="text-align:right;color:var(--success)">{{ "%0.0f"|format(r.pmsk) }}</td>
        <td style="text-align:right">{{ "%0.0f"|format(r.hpp) }}</td>
        <td style="text-align:right">{{ "%0.0f"|format(r.op) }}</td>
        <td style="text-align:right"><strong>{{ "%0.0f"|format(r.net - r.hpp - r.op + r.pmsk) }}</strong></td>
        <td style="text-align:right">{{ r.trx }}</td>
      </tr>'''
T = T.replace(old_table, new_table, 1)

io.open("templates/labarugi.html", "w", encoding="utf-8").write(T)
print("template labarugi + hapus form ok")
