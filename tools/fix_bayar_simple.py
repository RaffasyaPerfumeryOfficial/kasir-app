from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

s = s.replace(
'    L.append("Bayar : " + rp0(t.bayar or 0))\n    L.append("Kembali : " + rp0(t.kembalian or 0))',
'''    if (t.metode or "").upper() == "TUNAI":
        L.append("Bayar : " + rp0(t.bayar or 0))
        L.append("Kembali : " + rp0(t.kembalian or 0))'''
)

p.write_text(s, encoding="utf-8")

print("OK Bayar Kembali WhatsApp diperbaiki")
