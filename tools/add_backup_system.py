from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '''app = FastAPI(title="Aplikasi Kasir")
templates = Jinja2Templates(directory="templates")
'''

new = '''app = FastAPI(title="Aplikasi Kasir")

# ================= BACKUP OTOMATIS DATABASE =================

def backup_database():
    db_file = "kasir.db"
    folder = Path("backup")

    if not Path(db_file).exists():
        return

    folder.mkdir(exist_ok=True)

    nama = "kasir_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"
    tujuan = folder / nama

    shutil.copy2(db_file, tujuan)

    # simpan maksimal 30 backup
    files = sorted(
        folder.glob("kasir_*.db"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    for f in files[30:]:
        f.unlink()


@app.on_event("startup")
def auto_backup_database():
    backup_database()

# ================= END BACKUP =================

templates = Jinja2Templates(directory="templates")
'''

if old not in s:
    raise Exception("blok FastAPI tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK tambah backup otomatis")
