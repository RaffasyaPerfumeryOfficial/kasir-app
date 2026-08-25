from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

marker = '''@app.get("/tutup/preview")
def tutup_preview(db: Session = Depends(get_db)):
    return buat_ringkasan(db)
'''

pos1 = s.find(marker)

if pos1 == -1:
    raise Exception("tutup_preview pertama tidak ditemukan")

pos2 = s.find(marker, pos1 + 1)

if pos2 == -1:
    raise Exception("tutup_preview kedua tidak ditemukan")

s = s[:pos2] + s[pos2:].replace(marker, "", 1)

p.write_text(s, encoding="utf-8")

print("OK hapus duplicate tutup_preview")