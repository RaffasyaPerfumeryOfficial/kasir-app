from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '''def void_transaksi(trx_id: int, db: Session = Depends(get_db)):'''

new = '''def void_transaksi(
    trx_id: int,
    void_reason: str = Form("Tanpa alasan"),
    db: Session = Depends(get_db)
):'''

if old not in s:
    raise Exception("fungsi void tidak ditemukan")

s = s.replace(old,new,1)


old2 = '''    t.void_reason = "Dibatalkan kasir"'''

new2 = '''    t.void_reason = void_reason'''

if old2 not in s:
    raise Exception("void_reason lama tidak ditemukan")

s = s.replace(old2,new2,1)


p.write_text(s,encoding="utf-8")

print("OK patch void reason input")
