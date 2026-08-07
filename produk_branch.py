    target = None
    for p in produk_list:
        if p.nama.lower() in ql:
            target = p
            break
    if target and not ("notes" in ql or "aroma" in ql or "wangi" in ql):
        g = G.get(target.nama, "-")
        nts = N.get(target.nama, "")
        out = target.nama + "\n"
        out += "Kode / pabrik: " + (target.kode or "-") + "\n"
        out += "Kategori: " + (target.kategori or "-") + "\n"
        out += "Gender: " + g + "\n"
        out += "Harga modal: " + rp(target.harga_modal or 0) + "\n"
        out += "Harga jual: " + rp(target.harga) + "\n"
        out += "Untung per pcs: " + rp(target.harga - (target.harga_modal or 0)) + "\n"
        out += "Stok sekarang: " + str(target.stok or 0) + "\n"
        out += "Terjual: " + str(terjual.get(target.nama, 0))
        if nts:
            out += "\nNotes: " + nts
        return out
    if "kode" in ql or "pabrik" in ql or "brand" in ql or "dari apa" in ql:
        codes = set((p.kode or "").lower() for p in produk_list if p.kode)
        found = None
        for kod in codes:
            if re.search(r"\b" + re.escape(kod) + r"\b", ql):
                found = kod
                break
        if found:
            pool = [p for p in produk_list if (p.kode or "").lower() == found]
            pool = acak(pilih_pool(pool, ql), 15)
            if pool:
                return "Produk kode " + found.upper() + ":\n" + "\n".join(str(i + 1) + ". " + p.nama + " (stok " + str(p.stok or 0) + ")" for i, p in enumerate(pool))
    if "stok" in ql:
        if "kosong" in ql or "habis" in ql:
            pool = acak([p for p in produk_list if (p.stok or 0) == 0 and boleh(p.nama, ql)], 10)
            if pool:
                return "Stok kosong:\n" + "\n".join(str(i + 1) + ". " + p.nama for i, p in enumerate(pool))
            return "Tidak ada stok kosong."
        if "menipis" in ql or "hampir" in ql or "20" in ql:
            pool = acak([p for p in produk_list if 0 < (p.stok or 0) < 20 and boleh(p.nama, ql)], 10)
            if pool:
                return "Stok hampir habis (<20):\n" + "\n".join(str(i + 1) + ". " + p.nama + " (stok " + str(p.stok or 0) + ")" for i, p in enumerate(pool))
            return "Tidak ada stok di bawah 20."
