from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

target = '"teks": teks'

if target not in s:
    raise Exception("teks tidak ditemukan")

s = s.replace(
    target,
    '"teks": teks,\n            "wa_url": "/struk/" + str(trx_id) + "/wa"',
    1
)

p.write_text(s, encoding="utf-8")

print("OK wa_url ditambahkan")
