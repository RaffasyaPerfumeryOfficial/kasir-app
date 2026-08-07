import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

old1 = "def jawab_ai2(q, db):"
new1 = 'def jawab_ai2(q, db, ctx=""):'
assert old1 in s, "old1"
s = s.replace(old1, new1, 1)

old2 = '    if "mirip" in ql or "serupa" in ql or "menyerupai" in ql:'
new2 = '''    if ql.strip() in ["ya", "iya", "y", "yes", "mau", "boleh", "ok", "oke"] and ctx:
        tgt = None
        for p in produk_list:
            if p.nama == ctx:
                tgt = p
                break
        if tgt:
            return jawab_mirip(tgt, produk_list)
    if ctx and ("notes" in ql or "aroma" in ql or "wangi" in ql) and "apa saja" not in ql and cari_produk(ql, produk_list) is None:
        tgt = None
        for p in produk_list:
            if p.nama == ctx:
                tgt = p
                break
        if tgt:
            short = tgt.nama.split(" - ")[1] if " - " in tgt.nama else tgt.nama
            return tgt.nama + ":\\nNotes: " + (N.get(tgt.nama) or "-") + "\\n\\nMau saya carikan parfum dengan notes menyerupai " + short + "? Jawab: ya"
    if "mirip" in ql or "serupa" in ql or "menyerupai" in ql:'''
assert old2 in s, "old2"
s = s.replace(old2, new2, 1)

pat3 = re.compile(r'        my_notes = \(N\.get\(target\.nama\) or ""\)\.lower\(\)[\s\S]*?        return out')
assert pat3.search(s), "old3"
s = pat3.sub(lambda m: '        return jawab_mirip(target, produk_list)', s, count=1)

old4 = '''    target = cari_produk(ql, produk_list)
    if target and not ("notes" in ql or "aroma" in ql or "wangi" in ql):
        if "stok" in ql or "sisa" in ql or "tersisa" in ql:'''
new4 = '''    target = cari_produk(ql, produk_list)
    if target is None and ctx and any(k in ql for k in ["notes", "note", "aroma", "wangi", "brand", "merk", "merek", "stok", "harga", "modal", "jual", "untung", "kode", "kategori", "gender", "lain"]):
        for p in produk_list:
            if p.nama == ctx:
                target = p
                break
    if target and not ("notes" in ql or "aroma" in ql or "wangi" in ql):
        if "brand" in ql or "merk" in ql or "merek" in ql:
            short = target.nama.split(" - ")[1] if " - " in target.nama else target.nama
            brand = target.nama.split(" - ")[0] if " - " in target.nama else (target.kode or "-")
            return short + " dari brand/merk: " + brand
        if "lain" in ql:
            brand = target.nama.split(" - ")[0] if " - " in target.nama else None
            if brand:
                others = acak([p for p in produk_list if p.nama.startswith(brand + " -") and p.nama != target.nama], 5)
                if others:
                    return "Produk lain dari " + brand + ":\\n" + "\\n".join(str(i + 1) + ". " + p.nama for i, p in enumerate(others))
            return "Tidak ada produk lain dari brand ini."
        if "stok" in ql or "sisa" in ql or "tersisa" in ql:'''
assert old4 in s, "old4"
s = s.replace(old4, new4, 1)

old5 = '''        t2 = cari_produk(q, produk_list)
        if t2:
            return t2.nama + ":\\n" + (N.get(t2.nama) or "Data notes belum ada untuk produk ini.")'''
new5 = '''        t2 = cari_produk(q, produk_list)
        if t2:
            short2 = t2.nama.split(" - ")[1] if " - " in t2.nama else t2.nama
            return t2.nama + ":\\n" + (N.get(t2.nama) or "Data notes belum ada untuk produk ini.") + "\\n\\nMau saya carikan parfum dengan notes menyerupai " + short2 + "? Jawab: ya"'''
assert old5 in s, "old5"
s = s.replace(old5, new5, 1)

old6 = '''@app.get("/ai/jawab")
def ai_jawab(q: str, db: Session = Depends(get_db)):
    j = jawab_ai2(q, db)
    db.add(models.PesanAI(pertanyaan=q, jawaban=j))
    db.commit()
    return {"jawab": j}'''
new6 = '''@app.get("/ai/jawab")
def ai_jawab(q: str, ctx: str = "", db: Session = Depends(get_db)):
    j = jawab_ai2(q, db, ctx)
    t = cari_produk(q, db.query(models.Produk).all())
    prod = t.nama if t else ctx
    db.add(models.PesanAI(pertanyaan=q, jawaban=j))
    db.commit()
    return {"jawab": j, "produk": prod}'''
assert old6 in s, "old6"
s = s.replace(old6, new6, 1)

io.open(p, "w", encoding="utf-8").write(s)
print("percakapan ok")
