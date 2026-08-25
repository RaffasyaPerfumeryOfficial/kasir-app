from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")


old = '''def backup_database(jenis="auto"):
    db_file = "kasir.db"

    folder = Path("backup") / jenis
    folder.mkdir(parents=True, exist_ok=True)

    if not Path(db_file).exists():
        return

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


new = '''def backup_database(jenis="auto"):
    db_file = "kasir.db"

    folder = Path("backup") / jenis
    folder.mkdir(parents=True, exist_ok=True)

    if not Path(db_file).exists():
        return


    # auto hanya 1x sehari
    if jenis == "auto":
        nama = "auto_" + datetime.now().strftime("%Y%m%d") + ".db"

        tujuan = folder / nama

        if tujuan.exists():
            return

    else:
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


if old not in s:
    raise Exception("blok backup_database tidak cocok")


s=s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK fix backup auto harian")
