from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")


old = '''    L.append("")
    L.append("Bayar : " + rp0(t.bayar or 0))
    L.append("Kembali : " + rp0(t.kembalian or 0))
    L.append("")
    L.append("Metode : " + (t.metode or "TUNAI"))'''


new = '''    if (t.metode or "").upper() == "TUNAI":
        L.append("")
        L.append("Bayar : " + rp0(t.bayar or 0))
        L.append("Kembali : " + rp0(t.kembalian or 0))

    L.append("")
    
    metode = (t.metode or "TUNAI")
    metode = metode.replace("POIN + NON-TUNAI (", "")
    metode = metode.replace(")", "")

    L.append("Metode : " + metode)'''


if old not in s:
    raise Exception("Bagian Bayar WhatsApp tidak ditemukan")


s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK WhatsApp bayar dirapikan")