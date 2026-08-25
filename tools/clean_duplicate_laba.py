from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

awal = s.find('@app.get("/laporan/laba_rugi/excel")', s.find('@app.get("/laporan/laba_rugi/excel")') + 1)

akhir = s.find('@app.get("/riwayat"', awal)

if awal == -1:
    raise Exception("fungsi kedua tidak ditemukan")

if akhir == -1:
    raise Exception("batas fungsi berikutnya tidak ditemukan")

s = s[:awal] + s[akhir:]

p.write_text(s, encoding="utf-8")

print("OK HAPUS DUPLIKAT LABA RUGI")