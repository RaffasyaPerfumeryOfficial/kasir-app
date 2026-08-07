import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
pat = re.compile(r'    if target and not \("notes" in ql or "aroma" in ql or "wangi" in ql\):[\s\S]*?        return out')
rep = '''    if target and not ("notes" in ql or "aroma" in ql or "wangi" in ql):
        if "stok" in ql or "sisa" in ql or "tersisa" in ql:
            return "Stok " + target.nama + ": " + str(target.stok or 0)
        if "modal" in ql or "grosir" in ql:
            return "Harga modal " + target.nama + ": " + rp(target.harga_modal or 0)
        if "jual" in ql or "pasaran" in ql:
            return "Harga jual " + target.nama + ": " + rp(target.harga)
        if "untung" in ql or "laba" in ql:
            return "Untung per pcs " + target.nama + ": " + rp(target.harga - (target.harga_modal or 0))
        if "kode" in ql or "pabrik" in ql or "brand" in ql:
            return "Kode / pabrik " + target.nama + ": " + (target.kode or "-")
        if "gender" in ql or "untuk siapa" in ql:
            return target.nama + " untuk: " + G.get(target.nama, "unisex")
        if "kategori" in ql:
            return "Kategori " + target.nama + ": " + (target.kategori or "-")
        g = G.get(target.nama, "-")
        nts = N.get(target.nama, "")
        out = target.nama + "\\n"
        out += "Kode / pabrik: " + (target.kode or "-") + "\\n"
        out += "Kategori: " + (target.kategori or "-") + "\\n"
        out += "Gender: " + g + "\\n"
        out += "Harga modal: " + rp(target.harga_modal or 0) + "\\n"
        out += "Harga jual: " + rp(target.harga) + "\\n"
        out += "Untung per pcs: " + rp(target.harga - (target.harga_modal or 0)) + "\\n"
        out += "Stok sekarang: " + str(target.stok or 0) + "\\n"
        out += "Terjual: " + str(terjual.get(target.nama, 0))
        if nts:
            out += "\\nNotes: " + nts
        return out'''
s2 = pat.sub(lambda m: rep, s, count=1)
if s2 == s:
    print("pola tidak ditemukan")
else:
    io.open(p, "w", encoding="utf-8").write(s2)
    print("trim selesai")
