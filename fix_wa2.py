import io, re

m = io.open("app/main.py", encoding="utf-8").read()

# 1) route struk layar: sisipkan wa_url langsung
pat1 = re.compile(r'@app\.get\("/struk/\{trx_id\}"\)[\s\S]*?(?=\n@app\.)')
assert pat1.search(m), "route struk tidak ketemu"
new1 = '''@app.get("/struk/{trx_id}")
def struk_page(trx_id: int, request: Request, db: Session = Depends(get_db)):
    from urllib.parse import quote
    t = db.get(models.Transaksi, trx_id)
    if not t:
        raise HTTPException(404, "Struk tidak ditemukan")
    raw = json.loads(t.items)
    for it in raw:
        if not it.get("harga"):
            pr = db.query(models.Produk).filter_by(nama=it["nama"]).first()
            it["harga"] = pr.harga if pr else 0
    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    ag = db.get(models.Anggota, pl.anggota_id) if pl else None
    text = buat_teks_struk(db, t)
    hp = (ag.no_hp or "") if ag else ""
    digits = "".join(ch for ch in hp if ch.isdigit())
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    wa_url = ("https://wa.me/" + digits + "?text=" if digits else "https://wa.me/?text=") + quote(text)
    return templates.TemplateResponse(request, "struk.html", {"t": t, "items": raw, "ag": ag, "pl": pl, "wa_url": wa_url})


'''
m = pat1.sub(lambda x: new1, m, count=1)

# 2) route struk print: sama
pat2 = re.compile(r'@app\.get\("/struk/\{trx_id\}/print"\)[\s\S]*?(?=\n@app\.|\Z)')
assert pat2.search(m), "route print tidak ketemu"
new2 = '''@app.get("/struk/{trx_id}/print")
def struk_print(trx_id: int, request: Request, ulang: str = "", db: Session = Depends(get_db)):
    from urllib.parse import quote
    t = db.get(models.Transaksi, trx_id)
    if not t:
        raise HTTPException(404, "Struk tidak ditemukan")
    raw = json.loads(t.items)
    sub = 0.0
    for it in raw:
        if not it.get("harga"):
            pr = db.query(models.Produk).filter_by(nama=it["nama"]).first()
            it["harga"] = pr.harga if pr else 0
        sub += (it["harga"] or 0) * it["jumlah"] - (it.get("diskon") or 0)
    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    ag = db.get(models.Anggota, pl.anggota_id) if pl else None
    from datetime import datetime as _dt
    now = _dt.now()
    BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Des"]
    now_str = "%02d %s %d, %02d.%02d" % (now.day, BULAN[now.month - 1], now.year, now.hour, now.minute)
    text = buat_teks_struk(db, t)
    hp = (ag.no_hp or "") if ag else ""
    digits = "".join(ch for ch in hp if ch.isdigit())
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    wa_url = ("https://wa.me/" + digits + "?text=" if digits else "https://wa.me/?text=") + quote(text)
    return templates.TemplateResponse(request, "struk_print.html", {
        "t": t, "items": raw, "ag": ag, "pl": pl,
        "ulang": bool(ulang), "now_str": now_str, "sub": sub,
        "nontunai": "NON" in (t.metode or "").upper(), "wa_url": wa_url})


'''
m = pat2.sub(lambda x: new2, m, count=1)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("route wa langsung ok")

# 3) template: tombol WA tanpa fetch
t1 = io.open("templates/struk.html", encoding="utf-8").read()
pat3 = re.compile(r'<script>\s*var WA_URL[\s\S]*?</script>')
new3 = '''<script>
var WA_URL="{{ wa_url|safe }}";
function kirimWAStruk(){window.open(WA_URL,'_blank');}
</script>'''
t1, c1 = pat3.subn(new3, t1, count=1)
assert c1 == 1, "script struk tidak ketemu"
io.open("templates/struk.html", "w", encoding="utf-8").write(t1)

t2 = io.open("templates/struk_print.html", encoding="utf-8").read()
t2, c2 = pat3.subn(new3, t2, count=1)
assert c2 == 1, "script print tidak ketemu"
io.open("templates/struk_print.html", "w", encoding="utf-8").write(t2)
print("tombol wa langsung ok")
