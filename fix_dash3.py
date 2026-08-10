import io, re
d = io.open("templates/dashboard.html", encoding="utf-8").read()
d, b = re.subn(r'(?i)NON-TUNAI \(KESELURUHAN\)', 'NON-TUNAI (HARI INI)', d)
d, a = re.subn(r'(?i)(?<!NON-)TUNAI \(KESELURUHAN\)', 'TUNAI (HARI INI)', d)
assert a and b, "label tidak ketemu"
io.open("templates/dashboard.html", "w", encoding="utf-8").write(d)
print("label kartu ok")
