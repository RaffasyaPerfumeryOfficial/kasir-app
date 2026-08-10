import io
m = io.open("app/main.py", encoding="utf-8").read()

# 1) helper laba yang aman & sinkron
if "def hitung_laba_ai" not in m:
    anchor = "def rp(x):"
    i = m.find(anchor)
    assert i != -1
    helper = '''def hitung_laba_ai(d1, d2, transaksi_list, pengeluaran_list, produk_list):
    pmap = {}
    for p in produk_list:
        pmap[p.nama] = p
    omzet = 0.0
    modal = 0.0
    keluar = 0.0
    for t in transaksi_list:
        if t.dibuat and d1 <= t.dibuat.date() <= d2:
            omzet += t.total or 0
            if t.total_modal:
                modal += t.total_modal
            else:
                for it in json.loads(t.items):
                    pr = pmap.get(it["nama"])
                    if pr:
                        modal += (pr.harga_modal or 0) * it["jumlah"]
    for p in pengeluaran_list:
        if p.dibuat and d1 <= p.dibuat.date() <= d2:
            keluar += p.jumlah or 0
    laba = omzet - modal - keluar
    margin = (laba / omzet * 100) if omzet else 0.0
    return omzet, modal, keluar, laba, margin


'''
    m = m[:i] + helper + m[i:]
    print("helper laba ok")

# 2) ganti blok bulan ini dengan versi sinkron
old = '''    if ("laba" in ql or "untung" in ql or "keuntungan" in ql or "margin" in ql) and "bulan" in ql:
        month_start = date.today().replace(day=1)
        omzet = 0.0
        modal = 0.0
        keluar = 0.0
        for t in transaksi_list:
            if t.dibuat and t.dibuat.date() >= month_start:
                omzet += t.total
                modal += t.total_modal or 0.0
        for p in pengeluaran_list:
            if p.dibuat.date() >= month_start:
                keluar += p.jumlah
        laba = omzet - modal - keluar
        margin = (laba / omzet * 100) if omzet else 0.0
        return "Laba bulan ini:\\nOmzet " + rp(omzet) + "\\nModal " + rp(modal) + "\\nPengeluaran " + rp(keluar) + "\\nKeuntungan " + rp(laba) + "\\nMargin " + str(int(margin)) + "%"'''
new = '''    if ("laba" in ql or "untung" in ql or "keuntungan" in ql or "margin" in ql) and "bulan" in ql:
        month_start = date.today().replace(day=1)
        omzet, modal, keluar, laba, margin = hitung_laba_ai(month_start, date.today(), transaksi_list, pengeluaran_list, produk_list)
        return "Laba bulan ini:\\nOmzet " + rp(omzet) + "\\nModal (HPP) " + rp(modal) + "\\nPengeluaran " + rp(keluar) + "\\nKeuntungan " + rp(laba) + "\\nMargin " + str(int(margin)) + "%\\n\\n(Sinkron dengan menu Laba Rugi)"'''
assert old in m, "blok bulan ini tidak ketemu"
m = m.replace(old, new, 1)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("laba bulan ini sinkron ok")
