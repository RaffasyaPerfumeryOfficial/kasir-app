import io, re
from datetime import date

# 1) Model RekapManual
m = io.open("app/models.py", encoding="utf-8").read()
if "class RekapManual" not in m:
    m += '''
from sqlalchemy import Date

class RekapManual(Base):
    __tablename__ = "rekap_manual"
    id = Column(Integer, primary_key=True)
    tanggal = Column(Date)
    omzet = Column(Float, default=0)
    modal = Column(Float, default=0)
    keuntungan = Column(Float, default=0)
    margin = Column(String)
    trx = Column(Integer, default=0)
'''
    io.open("app/models.py", "w", encoding="utf-8").write(m)
print("model ok")

# 2) Buat tabel + isi data 1-7 Agustus
from app import models
from app.db import Base, engine, SessionLocal
Base.metadata.create_all(bind=engine)
db = SessionLocal()
DATA = [
    (1, 1300206, 535606, 764600, "59%", 37),
    (2, 1283350, 522263, 761087, "59%", 32),
    (3, 1006856, 424573, 582283, "58%", 25),
    (4, 569860, 269427, 300433, "53%", 15),
    (5, 849675, 358288, 491387, "58%", 18),
    (6, 315500, 163800, 151700, "62%", 9),
    (7, 420000, 214000, 205200, "56%", 13),
]
for d, om, mo, un, mg, tx in DATA:
    if not db.query(models.RekapManual).filter_by(tanggal=date(2026, 8, d)).first():
        db.add(models.RekapManual(tanggal=date(2026, 8, d), omzet=om, modal=mo, keuntungan=un, margin=mg, trx=tx))
db.commit()
db.close()
print("data 1-7 masuk")

# 3) hitung_laba versi baru (gabungkan rekap manual + jumlah trx)
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
pat = re.compile(r'def hitung_laba\(db, start_dt, end_dt\):[\s\S]*?(?=\n@app\.get\("/labarugi"\))')
assert pat.search(s), "hitung_laba tidak ketemu"
new_fn = '''def hitung_laba(db, start_dt, end_dt):
    trx = [t for t in transaksi_valid(db) if start_dt <= t.dibuat.date() <= end_dt]
    rows = {}
    for t in trx:
        r = rows.setdefault(t.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "trx": 0})
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
    for pg in db.query(models.Pengeluaran).all():
        if start_dt <= pg.dibuat.date() <= end_dt:
            r = rows.setdefault(pg.dibuat.date(), {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "trx": 0})
            r["op"] += pg.jumlah or 0
    for mm in db.query(models.RekapManual).all():
        if start_dt <= mm.tanggal <= end_dt:
            r = rows.setdefault(mm.tanggal, {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "trx": 0})
            r["gross"] += mm.omzet or 0
            r["net"] += mm.omzet or 0
            r["hpp"] += mm.modal or 0
            r["op"] += (mm.omzet or 0) - (mm.modal or 0) - (mm.keuntungan or 0)
            r["trx"] += mm.trx or 0
    tot = {"gross": 0.0, "disc": 0.0, "net": 0.0, "hpp": 0.0, "op": 0.0, "trx": 0}
    for r in rows.values():
        for k in tot:
            tot[k] += r[k]
    return {"tot": tot, "rows": sorted(rows.items(), reverse=True)}


'''
s = pat.sub(lambda x: new_fn, s, count=1)

# 4) Excel: tambah kolom Trx
s = s.replace('heads = ["No", "Tanggal", "Gross Sales", "Diskon", "Pendapatan", "Beban HPP", "Beban Operasional", "Laba Bersih"]',
              'heads = ["No", "Tanggal", "Gross Sales", "Diskon", "Pendapatan", "Beban HPP", "Beban Operasional", "Laba Bersih", "Trx"]', 1)
s = s.replace('''        ws.cell(row=row, column=8, value=r["net"] - r["hpp"] - r["op"])
        row += 1''',
              '''        ws.cell(row=row, column=8, value=r["net"] - r["hpp"] - r["op"])
        ws.cell(row=row, column=9, value=r["trx"])
        row += 1''', 1)
s = s.replace('    ws.cell(row=row, column=8, value=tot["net"] - tot["hpp"] - tot["op"]).font = bold',
              '    ws.cell(row=row, column=8, value=tot["net"] - tot["hpp"] - tot["op"]).font = bold\n    ws.cell(row=row, column=9, value=tot["trx"]).font = bold', 1)
s = s.replace('for col, w in zip("ABCDEFGH", [6, 14, 14, 12, 14, 14, 18, 14]):',
              'for col, w in zip("ABCDEFGHI", [6, 14, 14, 12, 14, 14, 18, 14, 6]):', 1)
io.open(p, "w", encoding="utf-8").write(s)
print("hitung_laba + excel ok")

# 5) Halaman labarugi: tambah kolom TRX
t = io.open("templates/labarugi.html", encoding="utf-8").read()
t = t.replace('<th style="text-align:right">Laba</th></tr>', '<th style="text-align:right">Laba</th><th style="text-align:right">Trx</th></tr>', 1)
t = t.replace('''<td style="text-align:right"><strong>{{ "%0.0f"|format(r.net - r.hpp - r.op) }}</strong></td>
      </tr>''', '''<td style="text-align:right"><strong>{{ "%0.0f"|format(r.net - r.hpp - r.op) }}</strong></td>
        <td style="text-align:right">{{ r.trx }}</td>
      </tr>''', 1)
io.open("templates/labarugi.html", "w", encoding="utf-8").write(t)
print("halaman ok")
