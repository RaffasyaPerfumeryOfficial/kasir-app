from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

old = 'window.open(url, "_blank");'
new = 'window.location.href = url;'

if old not in s:
    raise Exception("Kode window.open tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK WA redirect diperbaiki")
