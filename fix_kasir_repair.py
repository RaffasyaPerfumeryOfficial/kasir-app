import io, re
k = io.open("templates/kasir.html", encoding="utf-8").read()

# 1) bersihkan blok filter rusak + let duplikat (sampai sebelum getMet)
pat = re.compile(r'function filter\(\)\{[\s\S]*?(?=function getMet)')
assert pat.search(k), "blok filter tidak ketemu"
clean = '''function filter(){
var q=(document.getElementById('cari').value||'').toLowerCase();
var k=(document.getElementById('kat').value||'').toLowerCase();
var semua=(k===''||k.indexOf('semua')===0);
var items=document.querySelectorAll('.produk-item');
items.forEach(function(el){
var nama=el.dataset.nama||'';
var kat=el.dataset.kat||'';
var show=(nama.indexOf(q)!==-1)&&(semua||kat===k);
el.style.display=show?'':'none';
});
}
let anggotaData=null;
'''
k = pat.sub(lambda m: clean, k, count=1)
print("filter bersih")

# 2) penanda di baris tabel produk (<tr>)
mfor = re.search(r'\{%\s*for\s+p\s+in\s+(\w+)\s*%\}', k)
assert mfor, "loop produk tidak ketemu"
start = mfor.end()
endfor = k.find('{% endfor %}', start)
block = k[start:endfor]
if 'produk-item' not in block:
    tr = re.search(r'<tr([^>]*)>', block)
    if tr:
        oldtr = tr.group(0)
        newtr = '<tr class="produk-item" data-nama="{{ p.nama|lower }}" data-kat="{{ (p.kategori or \'\')|lower }}"' + oldtr[3:]
        block = block.replace(oldtr, newtr, 1)
        k = k[:start] + block + k[endfor:]
        print("penanda tr ok")
else:
    print("penanda sudah ada")

# 3) hapus onclick reset kolom cari (kalau masih ada)
k = k.replace(' onclick="this.value=\'\';filter()"', '')

io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("kasir diperbaiki")
