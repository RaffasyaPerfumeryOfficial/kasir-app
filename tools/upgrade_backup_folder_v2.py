from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")


old = """def backup_database():
    db_file = "kasir.db"
    folder = Path("backup")

    if not Path(db_file).exists():
        return

    folder.mkdir(exist_ok=True)

    nama = "kasir_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"
    tujuan = folder / nama

    shutil.copy2(db_file, tujuan)

    files = sorted(
        folder.glob("kasir_*.db"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    for f in files[30:]:
        f.unlink()
"""


new = """def backup_database(jenis="auto"):
    db_file = "kasir.db"

    if not Path(db_file).exists():
        return

    folder = Path("backup") / jenis
    folder.mkdir(parents=True, exist_ok=True)

    nama = jenis + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"

    tujuan = folder / nama

    shutil.copy2(db_file, tujuan)

    files = sorted(
        folder.glob("*.db"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    for f in files[30:]:
        f.unlink()
"""


if old not in s:
    raise Exception("fungsi backup lama tidak ditemukan")


s=s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK backup v2")
