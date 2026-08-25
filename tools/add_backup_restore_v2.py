from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

insert = '''

@app.get("/backup/list")
def backup_list():
    folder = Path("backup")
    folder.mkdir(exist_ok=True)

    data = []

    for f in sorted(folder.glob("kasir_*.db"), reverse=True):
        data.append({
            "nama": f.name,
            "ukuran": round(f.stat().st_size / 1024, 1)
        })

    return data


@app.post("/backup/manual")
def backup_manual():
    backup_database()
    return RedirectResponse("/backup-restore", status_code=303)


@app.post("/backup/restore/{nama}")
def backup_restore(nama: str):

    folder = Path("backup")
    file_backup = folder / nama

    if not file_backup.exists():
        raise HTTPException(404, "Backup tidak ditemukan")

    # backup kondisi sekarang sebelum restore
    sekarang = folder / (
        "sebelum_restore_" +
        datetime.now().strftime("%Y%m%d_%H%M%S") +
        ".db"
    )

    shutil.copy2("kasir.db", sekarang)

    shutil.copy2(file_backup, "kasir.db")

    return RedirectResponse(
        "/backup-restore",
        status_code=303
    )

'''

pos = s.find('@app.get("/manajemen")')

if pos == -1:
    raise Exception("lokasi insert tidak ditemukan")

s = s[:pos] + insert + s[pos:]

p.write_text(s,encoding="utf-8")

print("OK backup restore backend")
