from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")


lama = '''        "backup_terakhir": backup_terakhir
    }
'''


baru = '''        "backup_terakhir": backup_terakhir,
        "restore_info": restore_history(),
    }
'''


if lama not in s:
    raise Exception("Bagian data backup_restore tidak ditemukan")


s = s.replace(lama, baru, 1)


p.write_text(s, encoding="utf-8")

print("OK TAMBAH INFO BACKUP RESTORE")
