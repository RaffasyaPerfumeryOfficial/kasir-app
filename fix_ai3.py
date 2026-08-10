import io
m = io.open("app/main.py", encoding="utf-8").read()

# 1) helper: hitung tunai/non yang aman untuk transaksi lama & baru
if "def split_tunai_non" not in m:
    anchor = "def transaksi_valid"
    i = m.find(anchor)
    assert i != -1, "transaksi_valid tidak ketemu"
    helper = '''def split_tunai_non(t):
    tun = t.p_tunai or 0.0
    non = t.p_nontunai or 0.0
    if tun == 0 and non == 0:
        met = (t.metode or "").upper()
        if ("NON" in met) or ("QRIS" in met) or ("EDC" in met) or ("TRANSFER" in met):
            non = t.total or 0
        else:
            tun = t.total or 0
    return tun, non


'''
    m = m[:i] + helper + m[i:]
    print("helper ok")

# 2) AI: pakai helper
old_ai = """            tun = sum(t.p_tunai or 0 for t in trx)
            non = sum(t.p_nontunai or 0 for t in trx)"""
new_ai = """            tun = sum(split_tunai_non(t)[0] for t in trx)
            non = sum(split_tunai_non(t)[1] for t in trx)"""
assert old_ai in m, "blok ai tidak ketemu"
m = m.replace(old_ai, new_ai, 1)

# 3) Dashboard: pakai helper (biar ikut sinkron)
old_d = """            tunai_total += t.p_tunai or 0.0
            nontunai_total += t.p_nontunai or 0.0"""
new_d = """            _t, _n = split_tunai_non(t)
            tunai_total += _t
            nontunai_total += _n"""
assert old_d in m, "blok dashboard tidak ketemu"
m = m.replace(old_d, new_d, 1)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("ai + dashboard sinkron ok")
