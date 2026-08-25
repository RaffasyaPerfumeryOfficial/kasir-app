from pathlib import Path

# tambah request_id di model
p = Path("app/models.py")
s = p.read_text(encoding="utf-8")

old = '''    kode_trx = Column(String, default="")
'''

new = '''    kode_trx = Column(String, default="")
    request_id = Column(String, unique=True)
'''

if old not in s:
    raise Exception("kolom kode_trx tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")


# tambah migrasi sqlite
p = Path("app/models.py")
s = p.read_text(encoding="utf-8")

old = '''            if "kode_trx" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN kode_trx VARCHAR"))
'''

new = '''            if "kode_trx" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN kode_trx VARCHAR"))
            if "request_id" not in cols:
                conn.execute(text("ALTER TABLE transaksi ADD COLUMN request_id VARCHAR"))
'''

if old in s:
    s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK tambah request_id model + migrasi")
