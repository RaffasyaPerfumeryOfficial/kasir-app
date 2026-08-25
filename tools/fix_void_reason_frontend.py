from pathlib import Path

p = Path("templates/riwayat.html")
s = p.read_text(encoding="utf-8")

old = '''<form method="post" action="/transaksi/void/{{ tr.id }}" style="display:inline" onsubmit="return confirm('Void transaksi ini? Stok dikembalikan & omzet berkurang.')">
          <button class="btn-danger" type="submit">Void</button>
        </form>'''

new = '''<form method="post" action="/transaksi/void/{{ tr.id }}" style="display:inline" onsubmit="return cekVoid(this)">
          <input type="hidden" name="void_reason">
          <button class="btn-danger" type="submit">Void</button>
        </form>'''

if old not in s:
    raise Exception("blok void html tidak cocok")

s = s.replace(old,new,1)

if "function cekVoid" not in s:
    s += '''
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
</script>
'''

p.write_text(s,encoding="utf-8")

print("OK patch popup alasan void")
