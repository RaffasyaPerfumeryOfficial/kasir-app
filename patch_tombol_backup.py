from pathlib import Path

p = Path("templates/backup_restore.html")

s = p.read_text(encoding="utf-8")


lama = """
<a href="/backup/download?file={{ b.file }}">
<button type="button">
Download
</button>
</a>

<form method="post" action="/restore" style="display:inline">
<input type="hidden" name="file" value="{{ b.file }}">

<button onclick="return confirm('PERINGATAN! Database aktif akan diganti. Backup sebelum restore akan dibuat otomatis. Lanjutkan restore?')">
Restore
</button>

</form>

<form method="post" action="/backup/delete" style="display:inline">
<input type="hidden" name="file" value="{{ b.file }}">
<button onclick="return confirm('Hapus backup ini?')" style="background:#dc2626">
Hapus
</button>
</form>
"""


baru = """
<div class="backup-actions">

<a href="/backup/download?file={{ b.file }}">
<button type="button" class="action-btn download">
⬇ Download
</button>
</a>


<form method="post" action="/restore">

<input type="hidden" name="file" value="{{ b.file }}">

<button 
class="action-btn restore"
onclick="return confirm('PERINGATAN! Database aktif akan diganti. Backup sebelum restore akan dibuat otomatis. Lanjutkan restore?')">
↻ Restore
</button>

</form>


<form method="post" action="/backup/delete">

<input type="hidden" name="file" value="{{ b.file }}">

<button 
class="action-btn delete"
onclick="return confirm('Hapus backup ini?')">
🗑 Hapus
</button>

</form>

</div>
"""


if lama not in s:
    raise Exception("blok tombol tidak ditemukan")


s=s.replace(lama,baru)


tambahan="""

.backup-actions{
display:flex;
gap:8px;
align-items:center;
}


.backup-actions form{
margin:0;
}


.action-btn{
padding:8px 14px;
border:none;
border-radius:10px;
font-weight:600;
font-size:13px;
cursor:pointer;
color:white;
}


.download{
background:#2563eb;
}


.restore{
background:#7c3aed;
}


.delete{
background:#dc2626;
}


.action-btn:hover{
opacity:.85;
}

"""


s=s.replace(
"</style>",
tambahan+"</style>"
)


p.write_text(s,encoding="utf-8")

print("OK TOMBOL BACKUP")
