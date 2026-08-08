import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

pat_post = re.compile(r'@app\.post\("/tutup[^"]*"\)[\s\S]*?(?=\n@app\.)')
while pat_post.search(s):
    s = pat_post.sub(lambda m: "", s, count=1)

pat_get = re.compile(r'@app\.get\("/tutup"\)[\s\S]*?(?=\n@app\.)')
assert pat_get.search(s), "route tutup lama tidak ketemu"
new_get = '''@app.get("/tutup")
def tutup_page(request: Request, db: Session = Depends(get_db)):
    riwayat = db.query(models.RiwayatTutup).order_by(models.RiwayatTutup.id.desc()).all()
    return templates.TemplateResponse(request, "tutup.html", {"riwayat": riwayat})


@app.get("/tutup/preview")
def tutup_preview(db: Session = Depends(get_db)):
    return buat_ringkasan(db)


@app.post("/tutup/simpan")
async def tutup_simpan(request: Request, db: Session = Depends(get_db)):
    d = await request.json()
    db.add(models.RiwayatTutup(omzet=d.get("omzet", 0), tunai=d.get("tunai", 0), nontunai=d.get("nontunai", 0), pengeluaran=d.get("pengeluaran", 0), ringkasan=d.get("text", "")))
    db.commit()
    return {"ok": True}


'''
s = pat_get.sub(lambda m: new_get, s, count=1)
io.open(p, "w", encoding="utf-8").write(s)
print("tutup route ok")
