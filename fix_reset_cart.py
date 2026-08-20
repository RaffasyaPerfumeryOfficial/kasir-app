import io
k = io.open("templates/kasir.html", encoding="utf-8").read()

# 1) reset keranjang saat transaksi sukses
old = "if(d.ok){document.getElementById('modalBayar').style.display='none';window.location.href='/struk/'+d.id;}"
new = "if(d.ok){cart=[];localStorage.removeItem('mekarsari_cart');var da=document.getElementById('diskon_all');if(da)da.value='0';document.getElementById('modalBayar').style.display='none';window.location.href='/struk/'+d.id;}"
assert old in k, "blok sukses bayar tidak ketemu"
k = k.replace(old, new, 1)

# 2) bersihkan sisa removeItem di konfirmasi() (biar cart tidak kehapus saat buka tutup kasir)
k = k.replace("function konfirmasi(){localStorage.removeItem('mekarsari_cart');", "function konfirmasi(){", 1)
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("reset keranjang setelah transaksi ok")
