import io
s = io.open("templates/struk_print.html", encoding="utf-8").read()
old = "<div>{{ t.kode_trx or ('TRX-' ~ t.id) }}</div>"
new = '<div style="font-weight:bold;font-size:13px;letter-spacing:1px">{{ t.kode_trx or (\'TRX-\' ~ t.id) }}</div>'
if old in s:
    s = s.replace(old, new, 1)
    io.open("templates/struk_print.html", "w", encoding="utf-8").write(s)
    print("kode struk bold ok")
elif new in s:
    print("sudah bold")
else:
    print("POLA TIDAK KETEMU")
