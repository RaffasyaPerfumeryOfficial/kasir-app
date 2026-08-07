import io
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
old = '''@app.get("/produk/fetch_notes/{produk_id}")
def fetch_notes_online(produk_id: int, db: Session = Depends(get_db)):
    from app import fragella
    produk = db.get(models.Produk, produk_id)
    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")
    text, err = fragella.cari_notes_online(produk.nama)
    if err:
        return {"ok": False, "pesan": err}
    N[produk.nama] = text
    return {"ok": True, "notes": text}'''
new = '''@app.get("/produk/fetch_notes/{produk_id}")
def fetch_notes_online(produk_id: int, refresh: int = 0, db: Session = Depends(get_db)):
    from app import fragella
    produk = db.get(models.Produk, produk_id)
    if not produk:
        raise HTTPException(404, "Produk tidak ditemukan")
    existing = N.get(produk.nama)
    if existing and refresh == 0:
        return {"ok": True, "notes": existing, "gratis": True}
    text, err = fragella.cari_notes_online(produk.nama)
    if err:
        return {"ok": False, "pesan": err}
    N[produk.nama] = text
    try:
        with open("app/notes_data.py", "a", encoding="utf-8") as f:
            f.write('N["' + produk.nama.replace('"', "'") + '"] = "' + text.replace('"', "'") + '"\\n')
    except Exception:
        pass
    return {"ok": True, "notes": text, "gratis": False}'''
assert old in s, "route lama tidak ketemu"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("hemat ok")
