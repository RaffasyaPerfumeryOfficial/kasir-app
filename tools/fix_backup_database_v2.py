from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")


start = s.find("def backup_database(jenis=\"auto\"):")

end = s.find("\n\n@app.on_event", start)


if start == -1:
    raise Exception("fungsi backup_database tidak ditemukan")

if end == -1:
    raise Exception("akhir fungsi backup tidak ditemukan")


new_func = '''def backup_database(jenis="auto"):
    db_file = "kasir.db"

    folder = Path("backup") / jenis
    folder.mkdir(parents=True, exist_ok=True)

    if not Path(db_file).exists():
        return


    if jenis == "auto":

        nama = "auto_" + datetime.now().strftime("%Y%m%d") + ".db"

        tujuan = folder / nama

        # hanya 1 backup otomatis per hari
        if tujuan.exists():
            return

    else:

        nama = jenis + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"

        tujuan = folder / nama


    shutil.copy2(db_file, tujuan)


    # maksimal 30 file tiap kategori
    files = sorted(
        folder.glob("*.db"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )


    for f in files[30:]:
        f.unlink()
'''


s = s[:start] + new_func + s[end:]

p.write_text(s, encoding="utf-8")

print("OK patch backup_database v2")
