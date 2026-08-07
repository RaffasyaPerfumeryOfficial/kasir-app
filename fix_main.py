import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

pat6 = re.compile(r'[ \t]*if boleh\(it\["nama"\], ql\):[\s\S]*?hit\[it\["nama"\]\] = hit\.get\(it\["nama"\], 0\) \+ it\["jumlah"\]')
rep6 = '''                    if boleh(it["nama"], ql):
                        hit[it["nama"]] = hit.get(it["nama"], 0) + it["jumlah"]'''
s = pat6.sub(lambda m: rep6, s, count=1)

pat9 = re.compile(r'[ \t]*if it\["nama"\] in nama_bibit and boleh\(it\["nama"\], q\):[\s\S]*?hit\[it\["nama"\]\] = hit\.get\(it\["nama"\], 0\) \+ it\["jumlah"\]')
rep9 = '''                    if it["nama"] in nama_bibit and boleh(it["nama"], q):
                        hit[it["nama"]] = hit.get(it["nama"], 0) + it["jumlah"]'''
s = pat9.sub(lambda m: rep9, s, count=1)

pat3 = re.compile(r'[ \t]*cands = pilih_pool\(cands, ql\)[\s\S]*?men = acak\(\[p for p in cands if G\.get\(p\.nama, ""\)\.startswith\("pria"\)\], 2\)')
rep3 = '''                    cands = pilih_pool(cands, ql)
                    best = sorted([p for p in cands if terjual.get(p.nama, 0) > 0], key=lambda p: terjual[p.nama], reverse=True)[:3]
                    never = acak([p for p in cands if terjual.get(p.nama, 0) == 0], 3)
                    women = acak([p for p in cands if G.get(p.nama, "").startswith("wanita")], 2)
                    men = acak([p for p in cands if G.get(p.nama, "").startswith("pria")], 2)'''
s = pat3.sub(lambda m: rep3, s, count=1)

io.open(p, "w", encoding="utf-8").write(s)
print("fix selesai")
