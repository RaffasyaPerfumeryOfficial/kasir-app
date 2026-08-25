from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

start = s.find("def backup_database():")

end = s.find("\n\n@app.on_event(\"startup\")", start)

if start == -1 or end == -1:
    raise Exception("blok backup tidak ditemukan")

new = '''def backup_database(jenis="auto"):
    db_file = "kasir.db"

    if not Path(db_file).exists():
        return

    folder = Path("backup") / jenis
    folder.mkdir(parents=True, exist_ok=True)

    nama = jenis + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"

    tujuan = folder / nama

    shutil.copy2(db_file, tujuan)

    # simpan maksimal 30 backup per jenis
    files = sorted(
        folder.glob("*.db"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    for f in files[30:]:
        f.unlink()
'''

s = s[:start] + new + s[end:]

s = s.replace(
    "backup_database()",
    "backup_database(\"auto\")",
    1
)

p.write_text(s, encoding="utf-8")

print("OK backup v2")
