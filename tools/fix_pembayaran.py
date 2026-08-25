from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '''    t.bayar = float(payload.get("tunai") or 0)
    t.kembalian = float(payload.get("kembalian") or 0)
    t.poin_dipakai = poin
'''

new = '''    t.bayar = float(payload.get("tunai") or 0)

    # simpan pembagian pembayaran
    if t.metode == "NON":
        t.p_tunai = 0
        t.p_nontunai = total

    elif t.metode == "SPLIT":
        t.p_tunai = float(payload.get("tunai") or 0)
        t.p_nontunai = total - t.p_tunai

    else:
        t.p_tunai = total
        t.p_nontunai = 0

    t.kembalian = float(payload.get("kembalian") or 0)
    t.poin_dipakai = poin
'''

if old not in s:
    raise Exception("Blok pembayaran tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK patch pembayaran p_tunai p_nontunai")
