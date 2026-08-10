import io
m = io.open("app/main.py", encoding="utf-8").read()
anchor = '    if ql.strip() in ["ya", "iya", "y", "yes", "mau", "boleh", "ok", "oke"] and ctx:'
assert anchor in m, "anchor tidak ketemu"
if "Omzet sinkron" not in m:
    handler = '''    if ("omzet" in ql or "omset" in ql or "penjualan" in ql) and ("hari" in ql or "kemarin" in ql or "lusa" in ql or "lalu" in ql or "sekarang" in ql or re.search(r"\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}", ql)):
        from datetime import datetime as _dt
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
                    dd = _dt.strptime(mdate.group(0).replace("/", "-"), "%d-%m-%Y").date()
                    off = (date.today() - dd).days
                except Exception:
                    off = None
        if off is not None and off >= 0:
            today = date.today()
            target = today - timedelta(days=off)
            trx = [t for t in transaksi_list if t.dibuat and t.dibuat.date() == target]
            tot = sum(t.total or 0 for t in trx)
            tun = sum(t.p_tunai or 0 for t in trx)
            non = sum(t.p_nontunai or 0 for t in trx)
            label = "hari ini" if off == 0 else ("kemarin" if off == 1 else ("kemarin lusa" if off == 2 else target.strftime("%d/%m/%Y")))
            return ("Omzet sinkron " + label + " (" + target.strftime("%d/%m/%Y") + "):\\nTOTAL : " + rp(tot) + "\\nTUNAI : " + rp(tun) + "\\nNON-TUNAI : " + rp(non) + "\\nJumlah transaksi: " + str(len(trx)) + "\\n\\n(Sinkron dengan Dashboard, Riwayat & Laporan)")
'''
    m = m.replace(anchor, handler + anchor, 1)
    io.open("app/main.py", "w", encoding="utf-8").write(m)
    print("omzet per tanggal ok")
else:
    print("sudah ada")
