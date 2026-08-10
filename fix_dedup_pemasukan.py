import sqlite3
con = sqlite3.connect("kasir.db")
cur = con.cursor()
rows = cur.execute("select id, keterangan, jumlah, dibuat from pemasukan order by id").fetchall()
print("=== SEMUA PEMASUKAN TERCATAT ===")
for r in rows:
    print("id", r[0], "|", r[1], "|", r[2], "|", r[3])
seen = {}
hapus = []
for r in rows:
    key = (r[1], r[2])
    if key in seen:
        hapus.append(r[0])
    else:
        seen[key] = r[0]
for i in hapus:
    cur.execute("delete from pemasukan where id=?", (i,))
    print(">> HAPUS double id", i)
con.commit()
con.close()
print("selesai. terhapus:", len(hapus), "| sisa:", len(rows) - len(hapus))
