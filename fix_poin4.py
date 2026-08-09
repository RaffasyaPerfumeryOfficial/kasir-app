import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
pat = re.compile(r'@app\.get\("/anggota/list"\)[\s\S]*?(?=\n@app\.)')
assert pat.search(s), "route anggota/list tidak ketemu"
new = '''@app.get("/anggota/list")
def anggota_list(db: Session = Depends(get_db)):
    rows = db.query(models.Anggota).all()
    return [{"id": a.id, "label": (a.nama or "") + " | " + (a.nomor_member or ""), "poin": a.poin or 0} for a in rows]


'''
s = pat.sub(lambda m: new, s, count=1)
io.open(p, "w", encoding="utf-8").write(s)
print("anggota/list kini kirim poin")
