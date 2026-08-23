from pathlib import Path

p = Path("templates/backup_restore.html")

s = p.read_text(encoding="utf-8")


lama = """
<h3>Database Backup</h3>

Backup otomatis dibuat saat <b>Tutup Kasir</b>.

<form method="post" action="/backup/create">

<button class="btn-backup">
💾 Buat Backup Sekarang
</button>

</form>
"""


baru = """
<div class="backup-header">

<div>

<h3>💾 Database Backup</h3>

<div class="backup-info">

Backup otomatis:
<br>
✓ Saat Tutup Kasir
<br>
✓ Backup manual
<br>
✓ Sebelum Restore otomatis

</div>

</div>


<form method="post" action="/backup/create">

<button class="btn-backup">
＋ Buat Backup Sekarang
</button>

</form>


</div>
"""


if lama not in s:
    raise Exception("Bagian Database Backup tidak ditemukan")


s=s.replace(lama,baru,1)


p.write_text(s,encoding="utf-8")


print("OK HEADER BACKUP UI")
