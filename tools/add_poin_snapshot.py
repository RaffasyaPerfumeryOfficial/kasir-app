from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = """    try:
        db.commit()
"""

new = """    try:
        if ag:
            t.poin_setelah = ag.poin or 0
        else:
            t.poin_setelah = 0

        db.commit()
"""

if old not in s:
    raise Exception("Lokasi db.commit transaksi tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s, encoding="utf-8")
print("OK snapshot poin transaksi ditambahkan")
