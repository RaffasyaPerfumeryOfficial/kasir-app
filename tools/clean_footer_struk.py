from pathlib import Path

p = Path("templates/struk_print.html")
s = p.read_text(encoding="utf-8")

s = s.replace("`n`n", "")
s = s.replace("\\n\\n", "")

p.write_text(s, encoding="utf-8")

print("OK hapus karakter n aneh")
