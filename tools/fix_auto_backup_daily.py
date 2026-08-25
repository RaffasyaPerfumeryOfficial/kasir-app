from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")


start = s.find("def backup_database():")

end = s.find("\n\n@app.on_event", start)


if start == -1 or end == -1:
    raise Exception("fungsi backup_database tidak ditemukan")


new_func = '''def backup_database():
    db_file = "kasir.db"

    folder = Path("backup/auto")
    folder.mkdir(parents=True, exist_ok=True)

    if not Path(db_file).exists():
        return


    nama = "auto_" + datetime.now().strftime("%Y%m%d") + ".db"
    tujuan = folder / nama


    # cegah backup berulang saat reload
    if tujuan.exists():
        return


    shutil.copy2(db_file, tujuan)


    # maksimal simpan 30 backup otomatis
    files = sorted(
        folder.glob("auto_*.db"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )


    for f in files[30:]:
        f.unlink()
'''


s = s[:start] + new_func + s[end:]

p.write_text(s, encoding="utf-8")

print("OK replace backup_database")
