import io
m = io.open("app/main.py", encoding="utf-8").read()
anchor = "    kat_found = None"
assert anchor in m, "anchor kategori tidak ketemu"
if '"bibit" in ql and (' not in m:
    handler = '''    if "bibit" in ql and ("terjual" in ql or "jual" in ql or "penjualan" in ql or "laku" in ql or "ml" in ql) and ("hari" in ql or "kemarin" in ql or "lusa" in ql or "lalu" in ql or "sekarang" in ql or re.search(r"\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}", ql)):
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
            return "BIBIT " + label + " (" + target.strftime("%d/%m/%Y") + "):\\nTerjual : " + str(ml) + " ml\\nOmzet : " + rp(omz) + "\\nJumlah transaksi: " + str(ntrx) + "\\n\\n(Sinkron dengan Riwayat & Laporan)"
'''
    m = m.replace(anchor, handler + anchor, 1)
    io.open("app/main.py", "w", encoding="utf-8").write(m)
    print("ai ml bibit ok")
else:
    print("sudah ada")
