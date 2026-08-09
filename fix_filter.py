import io, re

k = io.open("templates/kasir.html", encoding="utf-8").read()

# 1) Tambahkan penanda ke setiap card produk
pat_for = re.search(r'\{%\s*for\s+p\s+in\s+[a-zA-Z_]+\s*%\}', k)
if pat_for:
    start = pat_for.end()
    end_for = k.find('{% endfor %}', start)
    if end_for != -1:
        block = k[start:end_for]
        div_match = re.search(r'(<div[^>]*)>', block)
        if div_match:
            old_div = div_match.group(0)
            if 'produk-item' not in old_div:
                new_div = old_div.rstrip('>') + ' class="produk-item" data-nama="{{ p.nama|lower }}" data-kat="{{ (p.kategori or \'\')|lower }}">'
                block = block.replace(old_div, new_div, 1)
                k = k[:start] + block + k[end_for:]
                print("penanda produk ditambahkan")

# 2) Ganti function filter() dengan versi yang bekerja
old_filter = re.search(r'function filter\(\)\{[\s\S]*?\n\}', k)
if old_filter:
    new_filter = '''function filter(){
var q=(document.getElementById('cari').value||'').toLowerCase();
var k=document.getElementById('kat').value;
var items=document.querySelectorAll('.produk-item');
items.forEach(function(el){
var nama=el.dataset.nama||'';
var kat=el.dataset.kat||'';
var show=(nama.indexOf(q)!==-1)&&(k===''||kat===k.toLowerCase()||k==='Semua'.toLowerCase());
el.style.display=show?'':'none';
});
}'''
    k = k[:old_filter.start()] + new_filter + k[old_filter.end():]
    print("fungsi filter diperbaiki")

# 3) Hapus onclick yang mereset kolom pencarian
if 'onclick="this.value=\'\';filter()"' in k:
    k = k.replace('onclick="this.value=\'\';filter()"', '')
    print("reset klik dihapus")

io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("selesai")
