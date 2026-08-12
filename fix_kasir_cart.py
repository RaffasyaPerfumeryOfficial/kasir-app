import io

k = io.open("templates/kasir.html", encoding="utf-8").read()

# 1. Ganti let cart=[]; dengan load dari localStorage
old_cart = "let cart=[];"
new_cart = "let cart=JSON.parse(localStorage.getItem('mekarsari_cart')||'[]');"
k = k.replace(old_cart, new_cart, 1)

# 2. Simpan ke localStorage di fungsi render()
old_render_save = "T=hitung();\nsetTxt('total'"
new_render_save = "T=hitung();\nlocalStorage.setItem('mekarsari_cart',JSON.stringify(cart));\nsetTxt('total'"
k = k.replace(old_render_save, new_render_save, 1)

# 3. Update hapusSemua agar hapus localStorage
old_hapus_semua = "function hapusSemua(){cart=[];render();}"
new_hapus_semua = "function hapusSemua(){cart=[];localStorage.removeItem('mekarsari_cart');render();}"
k = k.replace(old_hapus_semua, new_hapus_semua, 1)

# 4. Kategori kosongkan pencarian
old_kat = '<select id="kat" onchange="filter()"'
new_kat = '<select id="kat" onchange="document.getElementById(\'cari\').value=\'\';filter()"'
k = k.replace(old_kat, new_kat, 1)

# 5. Bersihkan cart saat konfirmasi sukses
old_konfirmasi = "function konfirmasi(){"
new_konfirmasi = "function konfirmasi(){localStorage.removeItem('mekarsari_cart');"
if old_konfirmasi in k:
    k = k.replace(old_konfirmasi, new_konfirmasi, 1)

# 6. Sembunyikan produk di awal (baru muncul kalau dicari/dipilih kategori)
last_script_idx = k.rfind('</script>')
k = k[:last_script_idx] + "document.querySelectorAll('.produk-item').forEach(function(el){el.style.display='none';});\nrender();\n" + k[last_script_idx:]

io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("kasir cart + filter ok")
