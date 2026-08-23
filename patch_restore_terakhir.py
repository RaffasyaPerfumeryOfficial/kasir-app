from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")


cari = '''def backup_restore(request: Request):
    folder = "backup"
'''

ganti = '''def backup_restore(request: Request):

    restore_terakhir = None

    folder_restore = "backup/log_restore"

    if os.path.exists(folder_restore):

        logs = [
            os.path.join(folder_restore, x)
            for x in os.listdir(folder_restore)
            if x.endswith(".txt")
        ]

        if logs:

            terakhir = max(
                logs,
                key=os.path.getmtime
            )

            restore_terakhir = {
                "waktu": datetime.fromtimestamp(
                    os.path.getmtime(terakhir)
                ).strftime("%d/%m/%Y %H:%M"),

                "file": os.path.basename(terakhir)
            }


    folder = "backup"
'''

if cari not in s:
    raise Exception("Posisi backup_restore tidak ditemukan")


s = s.replace(cari, ganti, 1)


cari2 = '''"backup_terakhir": backup_terakhir
'''

ganti2 = '''"backup_terakhir": backup_terakhir,
            "restore_terakhir": restore_terakhir
'''

if cari2 not in s:
    raise Exception("Data template backup tidak ditemukan")


s = s.replace(cari2, ganti2, 1)


p.write_text(s, encoding="utf-8")

print("OK RESTORE TERAKHIR BACKEND")
