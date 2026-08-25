from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '    L.append("?? *TERIMA KASIH*")'

new = '''    L.append("")
    L.append("TERIMA KASIH")'''

if old not in s:
    raise Exception("Footer WhatsApp tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK footer WhatsApp dibersihkan")
