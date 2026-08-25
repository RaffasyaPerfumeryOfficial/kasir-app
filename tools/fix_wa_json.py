from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

old = '''var pesan = {{ teks|safe }};'''

new = '''var pesan = {{ teks|tojson }};'''

if old not in s:
    raise Exception("bagian pesan tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK whatsapp json fix")
