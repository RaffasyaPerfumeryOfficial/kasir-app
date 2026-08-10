import io
m = io.open("app/main.py", encoding="utf-8").read()
anchor = '    if ("omzet" in ql or "omset" in ql or "penjualan" in ql) and ('
assert anchor in m, "anchor omzet tidak ketemu"
if '"diskon" in ql and (' not in m:
    handler = '''    if "diskon" in ql and ("hari" in ql or "kemarin" in ql or "lusa" in ql or "lalu" in ql or "sekarang" in ql or re.search(r"\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}", ql)):
        off = None
        if "lusa" in ql:
            off = 2
        elif "kemarin" in ql:
            off = 1
        elif "hari ini" in ql or "sekarang" in ql:
            off = 0
        else:
            mnum = re.search(r"(\\d+)\\s*hari\\s+(?:yang\\s+)?lalu", ql)
            mdate = re.search(r"(\\d{1,2})[/-](\\d{1,2})[/-](\\d{2,4})", ql)
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
            return "Total diskon " + label + " (" + target.strftime("%d/%m/%Y") + "):\\n" + rp(tot_d) + "\\nJumlah transaksi pakai diskon: " + str(n_d) + "\\n\\n(Sinkron dengan Riwayat & Laporan)"
'''
    m = m.replace(anchor, handler + anchor, 1)
    io.open("app/main.py", "w", encoding="utf-8").write(m)
    print("ai diskon ok")
else:
    print("sudah ada")
