import io
m = io.open("app/main.py", encoding="utf-8").read()
anchor = '    if ("omzet" in ql or "omset" in ql or "penjualan" in ql) and ('
assert anchor in m, "anchor omzet tidak ketemu"
if "kat_stok" not in m:
    handler = '''    kat_stok = None
    if "stok" in ql or "sisa" in ql:
        for kd in sorted(set((p.kategori or "").lower() for p in produk_list if p.kategori), key=len, reverse=True):
            if kd and kd in ql:
                kat_stok = kd
                break
    if kat_stok:
        off = 0
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
                    from datetime import datetime as _dt6
                    dd = _dt6.strptime(mdate.group(0).replace("/", "-"), "%d-%m-%Y").date()
                    off = (date.today() - dd).days
                except Exception:
                    off = 0
        if off is not None and off >= 0:
            today = date.today()
            target = today - timedelta(days=off)
            stok_now = sum(p.stok or 0 for p in produk_list if (p.kategori or "").lower() == kat_stok)
            sold_after = 0
            if off > 0:
                kat_map = {}
                for p in produk_list:
                    kat_map[p.nama] = (p.kategori or "").lower()
                for t in transaksi_list:
                    if t.dibuat and t.dibuat.date() > target:
                        for it in json.loads(t.items):
                            if kat_map.get(it["nama"]) == kat_stok:
                                sold_after += it["jumlah"]
            stok_then = stok_now + sold_after
            unit = "ml" if kat_stok == "bibit" else "pcs"
            label = "hari ini" if off == 0 else ("kemarin" if off == 1 else ("kemarin lusa" if off == 2 else target.strftime("%d/%m/%Y")))
            return "Sisa stok " + kat_stok.upper() + " " + label + " (" + target.strftime("%d/%m/%Y") + "):\\n" + str(stok_then) + " " + unit + "\\n\\n(Stok sekarang: " + str(stok_now) + " " + unit + " • Terjual setelah tanggal itu: " + str(sold_after) + " " + unit + ")\\n(Sinkron dengan Produk & Riwayat)"
'''
    m = m.replace(anchor, handler + anchor, 1)
    io.open("app/main.py", "w", encoding="utf-8").write(m)
    print("ai stok semua kategori ok")
else:
    print("sudah ada")
