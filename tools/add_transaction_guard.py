from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '''    t = models.Transaksi()
'''

new = '''    request_id = payload.get("request_id")

    if request_id:
        cek = db.query(models.Transaksi).filter(
            models.Transaksi.request_id == request_id
        ).first()

        if cek:
            return JSONResponse({
                "ok": True,
                "id": cek.id,
                "duplicate": True
            })

    t = models.Transaksi()
'''

if old not in s:
    raise Exception("blok Transaksi tidak ditemukan")

s = s.replace(old,new,1)


old2 = '''    t = models.Transaksi()
    t.items = json.dumps(rows)
'''

new2 = '''    t = models.Transaksi()
    t.request_id = payload.get("request_id")
    t.items = json.dumps(rows)
'''

if old2 not in s:
    raise Exception("blok isi transaksi tidak ditemukan")

s = s.replace(old2,new2,1)

p.write_text(s,encoding="utf-8")

print("OK tambah anti double transaksi backend")
