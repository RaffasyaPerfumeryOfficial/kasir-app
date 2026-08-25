from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '''        {
            "t": t,
            "teks": teks
        }
'''

new = '''        {
            "t": t,
            "teks": teks,
            "wa_url": "/struk/" + str(trx_id) + "/wa"
        }
'''

if old not in s:
    raise Exception("bagian struk_page tidak ditemukan")

s=s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK tambah wa_url")
