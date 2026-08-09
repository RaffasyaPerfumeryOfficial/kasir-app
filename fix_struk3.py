import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
pat = re.compile(r'@app\.get\("/struk/\{trx_id\}/print"\)[\s\S]*?(?=\n@app\.|\Z)')
assert pat.search(s), "route print tidak ketemu"
new = '''@app.get("/struk/{trx_id}/print")
def struk_print(trx_id: int, request: Request, db: Session = Depends(get_db)):
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
    return templates.TemplateResponse(request, "struk_print.html", {"t": t, "items": raw, "ag": ag, "pl": pl})


'''
s = pat.sub(lambda m: new, s, count=1)
io.open(p, "w", encoding="utf-8").write(s)
print("route print ok")

t = io.open("templates/struk_print.html", encoding="utf-8").read()
if "{% if ag %}" not in t:
    t = t.replace('<div class="c">Terima kasih', '''{% if ag %}
<div class="line"></div>
<table>
<tr><td>Anggota</td><td class="r">{{ ag.nama }}</td></tr>
<tr><td>Poin +</td><td class="r">{{ "%0.0f"|format(pl.poin or 0) }}</td></tr>
<tr><td>Total poin</td><td class="r">{{ "%0.0f"|format(ag.poin or 0) }}</td></tr>
</table>
{% endif %}
<div class="c">Terima kasih''', 1)
    io.open("templates/struk_print.html", "w", encoding="utf-8").write(t)
print("print 80mm ok")
