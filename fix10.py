import io
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
old = '''@app.get("/ai/jawab")
def ai_jawab(q: str, ctx: str = "", db: Session = Depends(get_db)):
    j = jawab_ai2(q, db, ctx)
    t = cari_produk(q, db.query(models.Produk).all())
    prod = t.nama if t else ctx
    db.add(models.PesanAI(pertanyaan=q, jawaban=j))
    db.commit()
    return {"jawab": j, "produk": prod}'''
new = '''LAST_PRODUK = [""]

@app.get("/ai/jawab")
def ai_jawab(q: str, ctx: str = "", db: Session = Depends(get_db)):
    if not ctx:
        ctx = LAST_PRODUK[0]
    j = jawab_ai2(q, db, ctx)
    t = cari_produk(q, db.query(models.Produk).all())
    prod = t.nama if t else ctx
    LAST_PRODUK[0] = prod or ""
    db.add(models.PesanAI(pertanyaan=q, jawaban=j))
    db.commit()
    return {"jawab": j, "produk": prod}'''
assert old in s, "route ai lama"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("konteks ok")
