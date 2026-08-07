import io
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
old = '''@app.get("/ai/jawab")
def ai_jawab(q: str, db: Session = Depends(get_db)):
    return {"jawab": jawab_ai2(q, db)}'''
new = '''@app.get("/ai/jawab")
def ai_jawab(q: str, db: Session = Depends(get_db)):
    j = jawab_ai2(q, db)
    db.add(models.PesanAI(pertanyaan=q, jawaban=j))
    db.commit()
    return {"jawab": j}


@app.get("/ai/riwayat")
def ai_riwayat(n: int = 300, db: Session = Depends(get_db)):
    rows = db.query(models.PesanAI).order_by(models.PesanAI.id.desc()).limit(n).all()
    rows.reverse()
    return [{"q": r.pertanyaan, "a": r.jawaban} for r in rows]'''
assert old in s, "route lama tidak ketemu"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("riwayat backend ok")
