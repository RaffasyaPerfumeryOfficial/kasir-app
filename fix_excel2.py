import io, re

p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

pat = re.compile(r'@app\.get\("/laporan/laba_rugi/excel"\)[\s\S]*?(?=\n@app\.|\Z)')
assert pat.search(s), "route lama tidak ketemu"

new_routes = '''@app.get("/laporan/laba_rugi/excel")
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
    trx_list = [t for t in transaksi_valid(db) if start_dt <= t.dibuat.date() <= end_dt]
    peng_list = [pg for pg in db.query(models.Pengeluaran).all() if start_dt <= pg.dibuat.date() <= end_dt]
    total_omzet = sum(t.total or 0 for t in trx_list)
    total_pengeluaran = sum(pg.jumlah or 0 for pg in peng_list)
    laba = total_omzet - total_pengeluaran
    per_hari = {}
    for t in trx_list:
        a = per_hari.setdefault(t.dibuat.date(), {"omzet": 0.0, "peng": 0.0})
        a["omzet"] += t.total or 0
    for pg in peng_list:
        a = per_hari.setdefault(pg.dibuat.date(), {"omzet": 0.0, "peng": 0.0})
        a["peng"] += pg.jumlah or 0
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
    ws.merge_cells("A6:E6")
    ws["A6"].alignment = Alignment(horizontal="center")
    for col, h in enumerate(["No", "Tanggal", "Omzet (Rp)", "Pengeluaran (Rp)", "Laba (Rp)"], 1):
        c = ws.cell(row=8, column=col, value=h)
        c.font = bold
        c.alignment = Alignment(horizontal="center")
    row = 9
    for i, d in enumerate(sorted(per_hari), 1):
        a = per_hari[d]
        ws.cell(row=row, column=1, value=i)
        ws.cell(row=row, column=2, value=d.strftime("%d/%m/%Y"))
        ws.cell(row=row, column=3, value=a["omzet"])
        ws.cell(row=row, column=4, value=a["peng"])
        ws.cell(row=row, column=5, value=a["omzet"] - a["peng"])
        row += 1
    row += 1
    ws.cell(row=row, column=2, value="TOTAL").font = bold
    ws.cell(row=row, column=3, value=total_omzet).font = bold
    ws.cell(row=row, column=4, value=total_pengeluaran).font = bold
    ws.cell(row=row, column=5, value=laba).font = bold
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 16
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 16
    for r in ws.iter_rows(min_row=9, max_row=row, min_col=3, max_col=5):
        for c in r:
            if isinstance(c.value, (int, float)):
                c.number_format = "#,##0"
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    fn = "LabaRugi_" + start_dt.strftime("%Y%m%d") + "_" + end_dt.strftime("%Y%m%d") + ".xlsx"
    return StreamingResponse(out, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=" + fn})


@app.get("/transaksi/excel")
def download_transaksi_excel(start_date: str = "", end_date: str = "", db: Session = Depends(get_db)):
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
    trx_list = [t for t in db.query(models.Transaksi).order_by(models.Transaksi.id).all() if start_dt <= t.dibuat.date() <= end_dt]
    wb = Workbook()
    ws = wb.active
    ws.title = "Transaksi"
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
    ws["A6"] = "DAFTAR TRANSAKSI (PER STRUK)"
    ws["A6"].font = Font(bold=True, size=14)
    ws.merge_cells("A6:G6")
    ws["A6"].alignment = Alignment(horizontal="center")
    for col, h in enumerate(["No", "Waktu", "Kode Struk", "Metode", "Items", "Total (Rp)", "Status"], 1):
        c = ws.cell(row=8, column=col, value=h)
        c.font = bold
        c.alignment = Alignment(horizontal="center")
    row = 9
    for i, t in enumerate(trx_list, 1):
        items = "; ".join(it["nama"] + " x" + str(it["jumlah"]) for it in json.loads(t.items))
        ws.cell(row=row, column=1, value=i)
        ws.cell(row=row, column=2, value=t.dibuat.strftime("%d/%m/%Y %H:%M"))
        ws.cell(row=row, column=3, value=t.kode_trx or ("TRX-" + str(t.id)))
        ws.cell(row=row, column=4, value=t.metode or "TUNAI")
        ws.cell(row=row, column=5, value=items)
        ws.cell(row=row, column=6, value=t.total or 0)
        ws.cell(row=row, column=7, value="VOID" if t.void else "SAH")
        row += 1
    row += 1
    ws.cell(row=row, column=5, value="TOTAL").font = bold
    ws.cell(row=row, column=6, value=sum(t.total or 0 for t in trx_list if not t.void)).font = bold
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 28
    ws.column_dimensions["D"].width = 22
    ws.column_dimensions["E"].width = 50
    ws.column_dimensions["F"].width = 14
    ws.column_dimensions["G"].width = 8
    for r in ws.iter_rows(min_row=9, max_row=row, min_col=6, max_col=6):
        for c in r:
            if isinstance(c.value, (int, float)):
                c.number_format = "#,##0"
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    fn = "Transaksi_" + start_dt.strftime("%Y%m%d") + "_" + end_dt.strftime("%Y%m%d") + ".xlsx"
    return StreamingResponse(out, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=" + fn})


'''
s = pat.sub(lambda m: new_routes, s, count=1)
io.open(p, "w", encoding="utf-8").write(s)
print("route excel rapih ok")

t = io.open("templates/transaksi.html", encoding="utf-8").read()
if "Download Excel" not in t:
    block = '''
<div class="card" style="margin:15px 0">
  <form method="get" action="/transaksi/excel" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
    <input type="date" name="start_date" id="trx_start" style="padding:8px;border:1px solid #cbd5e1;border-radius:6px">
    <span>s/d</span>
    <input type="date" name="end_date" id="trx_end" style="padding:8px;border:1px solid #cbd5e1;border-radius:6px">
    <button type="submit" style="background:#16a34a;color:white;padding:8px 16px;border:0;border-radius:6px">📥 Download Excel (per struk)</button>
    <button type="button" onclick="setTrxPeriode(30)">30 Hari</button>
    <button type="button" onclick="setTrxPeriode(7)">7 Hari</button>
    <button type="button" onclick="setTrxPeriode(0)">Hari Ini</button>
  </form>
</div>
<script>
function setTrxPeriode(hari){
const now=new Date();const end=now.toISOString().split('T')[0];let start;
if(hari===0){start=end;}else{const d=new Date();d.setDate(d.getDate()-hari+1);start=d.toISOString().split('T')[0];}
document.getElementById('trx_start').value=start;document.getElementById('trx_end').value=end;
}
window.addEventListener('load',function(){setTrxPeriode(30);});
</script>
'''
    idx = t.find("</div>", t.find("topbar"))
    if idx == -1:
        idx = t.find("{% block content %}") + len("{% block content %}")
    t = t[:idx] + "\n" + block + t[idx:]
    io.open("templates/transaksi.html", "w", encoding="utf-8").write(t)
print("tombol transaksi ok")
