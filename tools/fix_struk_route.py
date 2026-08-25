from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = """    teks = buat_teks_struk(db, t)

    return templates.TemplateResponse(
        request,
        "struk.html",
        {
            "t": t,
            "teks": teks
        }
    )
"""

new = """    teks = buat_teks_struk(db, t)

    items = json.loads(t.items)

    for it in items:
        if not it.get("harga"):
            pr = db.query(models.Produk).filter_by(nama=it["nama"]).first()
            it["harga"] = pr.harga if pr else 0

    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    ag = db.get(models.Anggota, pl.anggota_id) if pl else None

    return templates.TemplateResponse(
        request,
        "struk.html",
        {
            "t": t,
            "items": items,
            "ag": ag,
            "pl": pl,
            "teks": teks,
            "wa_url": "/struk/" + str(t.id) + "/wa"
        }
    )
"""

if old not in s:
    raise Exception("kode struk lama tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK patch struk")
