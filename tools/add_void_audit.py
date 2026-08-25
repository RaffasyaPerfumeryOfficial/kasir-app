from pathlib import Path

p = Path("app/models.py")
s = p.read_text(encoding="utf-8")

old = '''            if "void" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN void INTEGER"))
'''

new = '''            if "void" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN void INTEGER"))
            if "void_reason" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN void_reason VARCHAR"))
            if "void_time" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN void_time DATETIME"))
            if "void_by" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN void_by VARCHAR"))
'''

if old not in s:
    raise Exception("blok void tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK tambah migrasi void audit")
