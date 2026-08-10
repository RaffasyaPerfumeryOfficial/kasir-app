import io
k = io.open("templates/kasir.html", encoding="utf-8").read()
old = '{t:"7. Beban Profesional & Perizinan",s:["Jasa Profesional","Perizinan & Retribusi","Lisensi Software"]}\n];'
new = '{t:"7. Beban Profesional & Perizinan",s:["Jasa Profesional","Perizinan & Retribusi","Lisensi Software"]},\n{t:"8. Kas & Bank",s:["Beban Bunga Pinjaman","Beban Administrasi Bank / Pinjaman","Pembayaran Angsuran","Biaya Admin di Awal (Potongan Pencairan)"]}\n];'
assert old in k, "kategori 7 tidak ketemu"
k = k.replace(old, new, 1)
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("kategori kas & bank ok")
