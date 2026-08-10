import io
m = io.open("app/main.py", encoding="utf-8").read()
old = """    tunai = sum(t.p_tunai or 0 for t in trx)
    nontunai = sum(t.p_nontunai or 0 for t in trx)"""
new = """    tunai = sum(split_tunai_non(t)[0] for t in trx)
    nontunai = sum(split_tunai_non(t)[1] for t in trx)"""
assert old in m, "blok ringkasan tidak ketemu"
m = m.replace(old, new, 1)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("wa tunai/non sinkron ok")
