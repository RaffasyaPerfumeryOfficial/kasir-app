from pathlib import Path

p = Path("templates/riwayat.html")
s = p.read_text(encoding="utf-8")

old = '''{% endblock %}

<script>
function cekVoid(form){
    let alasan = prompt("Masukkan alasan VOID:");

    if(!alasan){
        alert("VOID dibatalkan. Alasan wajib diisi.");
        return false;
    }

    form.querySelector("input[name='void_reason']").value = alasan;
    return true;
}
</script>'''

new = '''<script>
function cekVoid(form){
    let alasan = prompt("Masukkan alasan VOID:");

    if(!alasan){
        alert("VOID dibatalkan. Alasan wajib diisi.");
        return false;
    }

    form.querySelector("input[name='void_reason']").value = alasan;
    return true;
}
</script>

{% endblock %}'''

if old not in s:
    raise Exception("blok script akhir tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK pindahkan script void")
