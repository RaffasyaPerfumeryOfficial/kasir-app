from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

blocks = s.split('@app.get("/transaksi/excel")')

if len(blocks) != 5:
    raise Exception(f"Jumlah blok tidak sesuai: {len(blocks)-1}")

# ambil versi terakhir
keep = blocks[-1]

s_baru = (
    blocks[0]
    + '@app.get("/transaksi/excel")'
    + keep
)

p.write_text(s_baru, encoding="utf-8")

print("OK CLEAN DUPLICATE EXCEL")