import io
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

old1 = '''    target = None
    for p in produk_list:
        if p.nama.lower() in ql:
            target = p
            break
    if target and not ("notes" in ql or "aroma" in ql or "wangi" in ql):'''
new1 = '''    target = cari_produk(ql, produk_list)
    if target and not ("notes" in ql or "aroma" in ql or "wangi" in ql):'''
assert old1 in s, "old1 tidak ketemu"
s = s.replace(old1, new1, 1)

old2 = '''        target = None
        for p in produk_list:
            if p.nama.lower() in ql:
                target = p
                break
        if not target:
            clean = ql
            for w in ["mirip", "serupa", "menyerupai", "parfum", "yang", "apa", "dengan"]:
                clean = clean.replace(w, "")
            clean = clean.strip()
            for p in produk_list:
                if clean and clean in p.nama.lower():
                    target = p
                    break'''
new2 = '''        target = cari_produk(ql, produk_list)'''
assert old2 in s, "old2 tidak ketemu"
s = s.replace(old2, new2, 1)

old3 = '''        has_name = any(p.nama.lower() in ql for p in produk_list)'''
new3 = '''        has_name = ("apa saja" not in ql) and cari_produk(ql, produk_list) is not None'''
assert old3 in s, "old3 tidak ketemu"
s = s.replace(old3, new3, 1)

old4 = '''    if "notes" in q or "aroma" in q or "wangi" in q:
        clean = q.replace("notes", "").replace("aroma", "").replace("wangi", "").strip()
        for p in produk_list:
            if p.nama.lower() in q or (clean and clean in p.nama.lower()):
                return p.nama + ":\\n" + (N.get(p.nama) or "Data notes belum ada untuk produk ini.")
        return "Produk tidak ditemukan. Contoh pertanyaan: notes AFNAN - 9PM"'''
new4 = '''    if "notes" in q or "aroma" in q or "wangi" in q:
        t2 = cari_produk(q, produk_list)
        if t2:
            return t2.nama + ":\\n" + (N.get(t2.nama) or "Data notes belum ada untuk produk ini.")
        return "Produk tidak ditemukan. Contoh pertanyaan: notes AFNAN - 9PM"'''
assert old4 in s, "old4 tidak ketemu"
s = s.replace(old4, new4, 1)

io.open(p, "w", encoding="utf-8").write(s)
print("fuzzy selesai")
