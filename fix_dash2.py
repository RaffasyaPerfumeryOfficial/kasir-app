import io, re

m = io.open("app/main.py", encoding="utf-8").read()
old = """    for t in transaksi_list:
        tunai_total += t.p_tunai or 0.0
        nontunai_total += t.p_nontunai or 0.0
        if t.dibuat and t.dibuat.date() == today:
            omzet_hari_ini += t.total
            transaksi_hari_ini += 1"""
new = """    for t in transaksi_list:
        if t.dibuat and t.dibuat.date() == today:
            omzet_hari_ini += t.total
            transaksi_hari_ini += 1
            tunai_total += t.p_tunai or 0.0
            nontunai_total += t.p_nontunai or 0.0"""
assert old in m, "blok dashboard tidak ketemu"
m = m.replace(old, new, 1)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("hitung tunai/non hari ini ok")

d = io.open("templates/dashboard.html", encoding="utf-8").read()
d, a = re.subn(r'(?i)TUNAI \(KESELURUHAN\)', 'TUNAI (HARI INI)', d)
d, b = re.subn(r'(?i)NON-TUNAI \(KESELURUHAN\)', 'NON-TUNAI (HARI INI)', d)
assert a and b, "label tidak ketemu"
io.open("templates/dashboard.html", "w", encoding="utf-8").write(d)
print("label kartu ok")
