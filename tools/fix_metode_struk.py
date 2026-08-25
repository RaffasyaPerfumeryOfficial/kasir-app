from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '"nontunai": "NON" in (t.metode or "").upper()'

new = '"nontunai": any(x in (t.metode or "").upper() for x in ["NON", "QRIS", "GOPAY", "DANA", "TRANSFER", "EDC"])'

if old not in s:
    raise Exception("Bagian metode tidak ditemukan")

s = s.replace(old,new)

p.write_text(s,encoding="utf-8")

print("OK metode pembayaran diperbaiki")
