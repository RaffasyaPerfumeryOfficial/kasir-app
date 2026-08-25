from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '    L.append("Metode : " + (t.metode or "TUNAI"))'

new = '''    metode = (t.metode or "TUNAI")
    metode = metode.replace("POIN + NON-TUNAI (", "")
    metode = metode.replace(")", "")
    L.append("Metode : " + metode)'''

# ganti hanya kemunculan terakhir (bagian WA)
pos = s.rfind(old)

if pos == -1:
    raise Exception("Metode WA tidak ditemukan")

s = s[:pos] + s[pos:].replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK Metode WhatsApp dirapikan")
