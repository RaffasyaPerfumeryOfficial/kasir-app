import io
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

old_anchor = '    data = hitung_laba(db, start_dt, end_dt)\n    tot = data["tot"]'
assert old_anchor in s, "anchor excel tidak ketemu"
add_query = old_anchor + '''
    peng_detail = [pg for pg in db.query(models.Pengeluaran).all() if start_dt <= pg.dibuat.date() <= end_dt]'''
s = s.replace(old_anchor, add_query, 1)

old_fmt = '''min_col=3, max_col=8):
        for c in r:
            if isinstance(c.value, (int, float)):
                c.number_format = "#,##0"'''
assert old_fmt in s, "anchor format tidak ketemu"
detail = old_fmt + '''
    row += 2
    ws.cell(row=row, column=1, value="RINCIAN BEBAN OPERASIONAL").font = bold
    row += 1
    for col, h in enumerate(["No", "Tanggal", "Beban Operasional (Rp)", "Keterangan"], 1):
        c = ws.cell(row=row, column=col, value=h)
        c.font = bold
    row += 1
    for i, pg in enumerate(sorted(peng_detail, key=lambda x: x.dibuat), 1):
        ket = pg.keterangan if hasattr(pg, "keterangan") else pg.nama
        ws.cell(row=row, column=1, value=i)
        ws.cell(row=row, column=2, value=pg.dibuat.strftime("%d/%m/%Y %H:%M"))
        ws.cell(row=row, column=3, value=pg.jumlah or 0)
        ws.cell(row=row, column=4, value=ket or "")
        row += 1
    ws.column_dimensions["D"].width = 40'''
s = s.replace(old_fmt, detail, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("excel rincian beban ok")
