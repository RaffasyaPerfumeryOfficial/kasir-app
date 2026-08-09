import io, re
main_p = "app/main.py"
s = io.open(main_p, encoding="utf-8").read()

mvoid = re.search(r'@app\.post\("([^"]*void[^"]*)"\)', s)
void_path = mvoid.group(1) if mvoid else "/void/{trx_id}"
print("void path:", void_path)

if "/riwayat-hari" not in s:
    s += '''

@app.get("/riwayat-hari")
def riwayat_hari(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    trx = [t for t in db.query(models.Transaksi).order_by(models.Transaksi.id.desc()).all() if t.dibuat.date() == today]
    total_hari = sum(t.total or 0 for t in trx if not t.void)
    rows = []
    for t in trx:
        rows.append({
            "t": t,
            "items_str": "; ".join(it["nama"] + " x" + str(it["jumlah"]) for it in json.loads(t.items)),
            "void_action": "''' + void_path + '''".replace("{trx_id}", str(t.id)).replace("{id}", str(t.id)),
        })
    return templates.TemplateResponse(request, "riwayat_hari.html", {"rows": rows, "total_hari": total_hari, "today": today})


@app.get("/laporan-lengkap")
def laporan_lengkap(request: Request, start_date: str = "", end_date: str = "", db: Session = Depends(get_db)):
    from datetime import datetime
    if not start_date or not end_date:
        end_dt = date.today()
        start_dt = end_dt.replace(day=1)
    else:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    per = {}
    for t in transaksi_valid(db):
        d = t.dibuat.date()
        if start_dt <= d <= end_dt:
            r = per.setdefault(d, {"trx": 0, "omzet": 0.0})
            r["trx"] += 1
            r["omzet"] += t.total or 0
    for m in db.query(models.RekapManual).all():
        if start_dt <= m.tanggal <= end_dt:
            r = per.setdefault(m.tanggal, {"trx": 0, "omzet": 0.0})
            r["trx"] += m.trx or 0
            r["omzet"] += m.omzet or 0
    rows = sorted(per.items(), reverse=True)
    total = sum(r["omzet"] for _, r in rows)
    return templates.TemplateResponse(request, "laporan_lengkap.html", {
        "rows": rows, "total": total,
        "start_date": start_dt.isoformat(), "end_date": end_dt.isoformat()})


@app.get("/laporan-lengkap/excel")
def laporan_lengkap_excel(start_date: str = "", end_date: str = "", db: Session = Depends(get_db)):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from io import BytesIO
    from datetime import datetime
    from fastapi.responses import StreamingResponse
    if not start_date or not end_date:
        end_dt = date.today()
        start_dt = end_dt.replace(day=1)
    else:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    per = {}
    for t in transaksi_valid(db):
        d = t.dibuat.date()
        if start_dt <= d <= end_dt:
            r = per.setdefault(d, {"trx": 0, "omzet": 0.0})
            r["trx"] += 1
            r["omzet"] += t.total or 0
    for m in db.query(models.RekapManual).all():
        if start_dt <= m.tanggal <= end_dt:
            r = per.setdefault(m.tanggal, {"trx": 0, "omzet": 0.0})
            r["trx"] += m.trx or 0
            r["omzet"] += m.omzet or 0
    rows = sorted(per.items())
    wb = Workbook()
    ws = wb.active
    ws.title = "Laporan Penjualan"
    ws["A1"] = "SALES COUNTER"; ws["B1"] = "RIVALDI RAMDANI"
    ws["A2"] = "NO HP"; ws["B2"] = "0853-2034-2037"
    ws["A3"] = "CAB"; ws["B3"] = "MEKAR SARI"
    ws["A4"] = "PERIODE"
    ws["B4"] = start_dt.strftime("%d-%B-%Y").upper() + " SAMPAI " + end_dt.strftime("%d-%B-%Y").upper()
    bold = Font(bold=True)
    for r in range(1, 5):
        ws.cell(row=r, column=1).font = bold
    ws["A6"] = "LAPORAN PENJUALAN"
    ws["A6"].font = Font(bold=True, size=14)
    for col, h in enumerate(["No", "Tanggal", "Jumlah Transaksi", "Omzet (Rp)"], 1):
        c = ws.cell(row=8, column=col, value=h)
        c.font = bold
    row = 9
    for i, (d, r) in enumerate(rows, 1):
        ws.cell(row=row, column=1, value=i)
        ws.cell(row=row, column=2, value=d.strftime("%d/%m/%Y"))
        ws.cell(row=row, column=3, value=r["trx"])
        ws.cell(row=row, column=4, value=r["omzet"])
        row += 1
    row += 1
    ws.cell(row=row, column=3, value="TOTAL").font = bold
    ws.cell(row=row, column=4, value=sum(r["omzet"] for _, r in rows)).font = bold
    for col, w in zip("ABCD", [6, 14, 18, 16]):
        ws.column_dimensions[col].width = w
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    fn = "LaporanPenjualan_" + start_dt.strftime("%Y%m%d") + "_" + end_dt.strftime("%Y%m%d") + ".xlsx"
    return StreamingResponse(out, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=" + fn})
'''
    io.open(main_p, "w", encoding="utf-8").write(s)
print("routes baru ok")

b = io.open("templates/base.html", encoding="utf-8").read()
n1 = b.count(">Transaksi</a>")
b = b.replace(">Transaksi</a>", ">Riwayat</a>")
n2 = b.count('href="/riwayat"')
b = b.replace('href="/riwayat"', 'href="/riwayat-hari"')
n3 = b.count('href="/laporan"')
b = b.replace('href="/laporan"', 'href="/laporan-lengkap"')
io.open("templates/base.html", "w", encoding="utf-8").write(b)
print("sidebar diganti:", n1, n2, n3)

T1 = '''{% extends "base.html" %}
{% block title %}Riwayat{% endblock %}
{% block content %}
<div class="topbar">
  <h2>Riwayat Transaksi</h2>
  <span class="badge">Hari ini {{ today.strftime("%d/%m/%Y") }} • reset otomatis jam 00:00</span>
</div>
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
<div class="card" style="margin-bottom:15px">Total penjualan hari ini (tanpa VOID): <strong style="font-size:20px">Rp {{ "%0.0f"|format(total_hari) }}</strong></div>
<div class="card">
  <table style="width:100%">
    <tr><th>ID Transaksi</th><th>Waktu</th><th>Metode</th><th>Items</th><th style="text-align:right">Total</th><th>Status</th><th>Aksi</th></tr>
    {% for r in rows %}
    <tr>
      <td>{{ r.t.kode_trx or ('TRX-' ~ r.t.id) }}</td>
      <td>{{ r.t.dibuat.strftime("%d/%m/%Y %H:%M") }}</td>
      <td>{{ r.t.metode or 'TUNAI' }}</td>
      <td>{{ r.items_str }}</td>
      <td style="text-align:right">{{ "%0.0f"|format(r.t.total or 0) }}</td>
      <td>{% if r.t.void %}<span class="badge" style="background:#fee2e2;color:var(--danger)">VOID</span>{% else %}<span class="badge" style="background:#dcfce7;color:var(--success)">SAH</span>{% endif %}</td>
      <td>
        <a href="/struk/{{ r.t.id }}">Struk</a>
        {% if not r.t.void %}
        <form method="post" action="{{ r.void_action }}" style="display:inline" onsubmit="return confirm('Void transaksi ini?')">
          <button class="btn-danger" type="submit">Void</button>
        </form>
        {% endif %}
      </td>
    </tr>
    {% else %}
    <tr><td colspan="7">Belum ada transaksi hari ini.</td></tr>
    {% endfor %}
  </table>
</div>
<script>
function setTrxPeriode(hari){
const now=new Date();const end=now.toISOString().split('T')[0];let start;
if(hari===0){start=end;}else{const d=new Date();d.setDate(d.getDate()-hari+1);start=d.toISOString().split('T')[0];}
document.getElementById('trx_start').value=start;document.getElementById('trx_end').value=end;
}
window.addEventListener('load',function(){setTrxPeriode(0);});
</script>
{% endblock %}
'''
io.open("templates/riwayat_hari.html", "w", encoding="utf-8").write(T1)

T2 = '''{% extends "base.html" %}
{% block title %}Laporan{% endblock %}
{% block content %}
<div class="topbar"><h2>Laporan Penjualan</h2></div>
<div class="card" style="margin:15px 0">
  <form method="get" action="/laporan-lengkap" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
    <input type="date" name="start_date" value="{{ start_date }}" style="padding:8px;border:1px solid #cbd5e1;border-radius:6px">
    <span>s/d</span>
    <input type="date" name="end_date" value="{{ end_date }}" style="padding:8px;border:1px solid #cbd5e1;border-radius:6px">
    <button type="submit">Tampilkan</button>
  </form>
  <form method="get" action="/laporan-lengkap/excel" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px">
    <input type="date" name="start_date" value="{{ start_date }}" style="padding:8px;border:1px solid #cbd5e1;border-radius:6px">
    <span>s/d</span>
    <input type="date" name="end_date" value="{{ end_date }}" style="padding:8px;border:1px solid #cbd5e1;border-radius:6px">
    <button type="submit" style="background:#16a34a;color:white;padding:8px 16px;border:0;border-radius:6px">📥 Download Excel</button>
  </form>
</div>
<div class="card" style="margin-bottom:15px">Total omzet periode ini (termasuk rekap 1-7): <strong style="font-size:20px">Rp {{ "%0.0f"|format(total) }}</strong></div>
<div class="card">
  <table style="width:100%">
    <tr><th>Tanggal</th><th style="text-align:right">Jumlah Transaksi</th><th style="text-align:right">Omzet</th></tr>
    {% for d, r in rows %}
    <tr>
      <td>{{ d.strftime("%d/%m/%Y") }}</td>
      <td style="text-align:right">{{ r.trx }}</td>
      <td style="text-align:right"><strong>{{ "%0.0f"|format(r.omzet) }}</strong></td>
    </tr>
    {% else %}
    <tr><td colspan="3">Tidak ada data di periode ini.</td></tr>
    {% endfor %}
  </table>
</div>
{% endblock %}
'''
io.open("templates/laporan_lengkap.html", "w", encoding="utf-8").write(T2)
print("template ok")
