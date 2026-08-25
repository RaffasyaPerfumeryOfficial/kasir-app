from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '''    L.append("-----------------------------------------")
    L.append("Terima kasih")
    L.append("Parfum Anda, cerita Anda.")
    return "\\n".join(L)
'''

new = '''    L.append("-----------------------------------------")
    L.append("")
    L.append("           TERIMA KASIH")
    L.append("")
    L.append("Simpan struk ini sebagai bukti yang sah")
    return "\\n".join(L)
'''

if old not in s:
    raise Exception("footer lama tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK footer WA diperbaiki")
