from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

old = "https://wa.me/?text="
new = "https://api.whatsapp.com/send?text="

if old not in s:
    raise Exception("URL WhatsApp lama tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK WA API diganti")
