from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")


cari = '''"backup_terakhir": backup_terakhir'''


ganti = '''"backup_terakhir": backup_terakhir,
            "restore_info": restore_history()'''


if cari not in s:
    raise Exception("backup_terakhir tidak ditemukan")


s = s.replace(cari, ganti, 1)


p.write_text(s, encoding="utf-8")

print("OK TAMBAH RESTORE INFO")
