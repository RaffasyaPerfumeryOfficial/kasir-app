import io
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

bad1 = '''                    if it["nama"] in nama_bibit:
                    if boleh(it["nama"], ql):
                        hit[it["nama"]] = hit.get(it["nama"], 0) + it["jumlah"]'''
good = '''                    if it["nama"] in nama_bibit and boleh(it["nama"], q):
                        hit[it["nama"]] = hit.get(it["nama"], 0) + it["jumlah"]'''
s = s.replace(bad1, good)

bad2 = '''                    if it["nama"] in nama_bibit:
                        if boleh(it["nama"], ql):
                        hit[it["nama"]] = hit.get(it["nama"], 0) + it["jumlah"]'''
s = s.replace(bad2, good)

io.open(p, "w", encoding="utf-8").write(s)
print("fix2 selesai")
