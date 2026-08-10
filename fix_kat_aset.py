import io
k = io.open("templates/kasir.html", encoding="utf-8").read()
old = '{t:"3. Beban Perlengkapan & Peralatan Kantor",s:["Alat Tulis Kantor (ATK)","Konsumsi & Dapur Kantor","Perlengkapan Habis Pakai","Sewa Peralatan"]}'
new = '{t:"3. Beban Perlengkapan & Peralatan Kantor",s:["Alat Tulis Kantor (ATK)","Konsumsi & Dapur Kantor","Perlengkapan Habis Pakai","Sewa Peralatan","Pembelian Peralatan Kantor (Kursi/Meja/Lemari)"]}'
assert old in k, "kategori 3 tidak ketemu"
k = k.replace(old, new, 1)
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("sub peralatan kantor ok")
