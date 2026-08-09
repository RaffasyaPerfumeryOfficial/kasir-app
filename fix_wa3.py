import io, re

m = io.open("app/main.py", encoding="utf-8").read()

# 1) route struk layar (cari biasa, tanpa regex)
marker = '@app.get("/struk/{trx_id}")'
i = m.find(marker)
assert i != -1, "route struk benar-benar tidak ada"
nxt_app = m.find('\n@app.', i + 10)
nxt_def = m.find('\ndef ', i + 10)
cands = [x for x in [nxt_app, nxt_def] if x != -1]
j = min(cands) if cands else len(m)
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
m = m[:i] + new1 + m[j:]
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("route struk + wa langsung ok")

# 2) template: tombol WA tanpa fetch
pat3 = re.compile(r'<script>\s*var WA_URL[\s\S]*?</script>')
new3 = '''<script>
var WA_URL="{{ wa_url|safe }}";
function kirimWAStruk(){window.open(WA_URL,'_blank');}
</script>'''
t1 = io.open("templates/struk.html", encoding="utf-8").read()
t1, c1 = pat3.subn(new3, t1, count=1)
assert c1 == 1, "script struk tidak ketemu"
io.open("templates/struk.html", "w", encoding="utf-8").write(t1)
t2 = io.open("templates/struk_print.html", encoding="utf-8").read()
t2, c2 = pat3.subn(new3, t2, count=1)
assert c2 == 1, "script print tidak ketemu"
io.open("templates/struk_print.html", "w", encoding="utf-8").write(t2)
print("tombol wa langsung ok")
