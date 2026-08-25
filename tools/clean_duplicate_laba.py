from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

target = '@app.get("/laporan/laba_rugi/excel")'

pos1 = s.find(target)

if pos1 == -1:
    raise Exception("fungsi pertama tidak ditemukan")

pos2 = s.find(target, pos1 + 1)

if pos2 == -1:
    raise Exception("fungsi kedua tidak ditemukan")

akhir = s.find("@app.", pos2 + 10)

if akhir == -1:
    raise Exception("batas fungsi berikutnya tidak ditemukan")

s = s[:pos2] + s[akhir:]

p.write_text(s, encoding="utf-8")

print("OK HAPUS DUPLIKAT LABA RUGI")