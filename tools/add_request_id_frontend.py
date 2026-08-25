from pathlib import Path

p = Path("templates/kasir.html")
s = p.read_text(encoding="utf-8")

old = '''metode:metode};'''

new = '''metode:metode,request_id:crypto.randomUUID()};'''

if old not in s:
    raise Exception("payload transaksi 1 tidak ditemukan")

s = s.replace(old,new,1)


old2 = '''const payload={items:cart.map(i=>({produk_id:i.id,jumlah:i.jumlah,diskon:i.diskon||0})),diskon_total:dt,anggota_id:(document.getElementById('anggota_sel').value||'')};'''

new2 = '''const payload={items:cart.map(i=>({produk_id:i.id,jumlah:i.jumlah,diskon:i.diskon||0})),diskon_total:dt,anggota_id:(document.getElementById('anggota_sel').value||''),request_id:crypto.randomUUID()};'''

if old2 not in s:
    raise Exception("payload transaksi 2 tidak ditemukan")

s = s.replace(old2,new2,1)

p.write_text(s,encoding="utf-8")

print("OK tambah request_id frontend")
