from pathlib import Path

p = Path("templates/backup_restore.html")

s = p.read_text(encoding="utf-8")


lama = """
<p>
Backup otomatis dibuat saat <b>Tutup Kasir</b>.
</p>


<form method="post" action="/backup/create">

<button>
💾 Buat Backup Sekarang
</button>

</form>
"""


if lama not in s:
    raise Exception("blok lama tidak ditemukan")


s = s.replace(lama, "", 1)


p.write_text(s, encoding="utf-8")

print("OK HAPUS DUPLIKAT BACKUP")
