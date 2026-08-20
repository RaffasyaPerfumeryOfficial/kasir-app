import io
s = io.open("templates/struk_print.html", encoding="utf-8").read()
old = "body { width: 72mm; margin: 0 auto; font-family: 'Courier New', monospace; font-size: 12px; color: #000; padding: 4mm 2mm; }"
new = "body { width: 72mm; margin: 0 auto; font-family: 'Courier New', monospace; font-size: 12px; color: #000; padding: 0mm 2mm 4mm 2mm; }"
assert old in s, "padding body tidak ketemu"
s = s.replace(old, new, 1)
io.open("templates/struk_print.html", "w", encoding="utf-8").write(s)
print("margin atas struk ok")
