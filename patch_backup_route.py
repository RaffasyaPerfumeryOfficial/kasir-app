from pathlib import Path

p = Path("app/main.py")
s = p.read_text()

lama = '''@app.get("/backup")
def backup_db():
    return FileResponse(
        "kasir.db",
        filename="backup-kasir-" + date.today().isoformat() + ".db",
        media_type="application/octet-stream",
    )'''

baru = '''@app.get("/backup")
def backup_db():
    backup_otomatis()

    return RedirectResponse(
        "/backup-restore",
        status_code=303
    )'''

if lama not in s:
    raise Exception("blok backup lama tidak ditemukan")

s = s.replace(lama, baru, 1)

p.write_text(s)

print("OK - route backup manual diperbaiki")