from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

s = s.replace(
'''function kirimWAStruk(){

    var pesan = encodeURIComponent({{ teks|safe }});
''',
'''function kirimWAStruk(){

    alert("Tombol WA aktif");

    var pesan = encodeURIComponent({{ teks|safe }});
'''
)

p.write_text(s,encoding="utf-8")

print("OK tambah test WA")
