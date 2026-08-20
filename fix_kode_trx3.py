import io, re
m = io.open("app/main.py", encoding="utf-8").read()
old_line = re.search(r't\.kode_trx = .*', m)
assert old_line, "baris kode_trx tidak ketemu"
new_line = 't.kode_trx = "RP-MKRS/" + datetime.now().strftime("%d-%m-%Y") + "/" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))'
m = m.replace(old_line.group(0), new_line, 1)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("kode trx acak ok")
