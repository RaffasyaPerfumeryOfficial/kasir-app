from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '''    t.void = 1
    for it in json.loads(t.items):
'''

new = '''    t.void = 1
    t.void_reason = "Dibatalkan kasir"
    t.void_time = datetime.now()
    t.void_by = "Admin"

    for it in json.loads(t.items):
'''

if old not in s:
    raise Exception("blok void tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK tambah audit void route")
