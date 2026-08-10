import io

# 1) bersihkan dashboard
d = io.open("templates/dashboard.html", encoding="utf-8").read()
i = d.find('<div class="card" style="margin-top:15px;text-align:right">')
if i != -1:
    j = d.rfind('{% endblock %}')
    d = d[:i] + d[j:]
    io.open("templates/dashboard.html", "w", encoding="utf-8").write(d)
    print("dashboard bersih")

# 2) pasang di kasir sebelah + Pengeluaran
k = io.open("templates/kasir.html", encoding="utf-8").read()
if "modalPemasukan" not in k:
    a = k.find('+ Pengeluaran</button>')
    assert a != -1, "tombol pengeluaran tidak ketemu"
    e = k.find('</button>', a) + len('</button>')
    btn = '\n<button type="button" onclick="openPemasukan()" style="background:#16a34a;color:white;padding:10px 16px;border:0;border-radius:8px;font-weight:700;margin-left:8px">+ Pemasukan</button>'
    k = k[:e] + btn + k[e:]
    UI = '''
<div id="modalPemasukan" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:60">
  <div style="background:white;max-width:480px;margin:8vh auto;padding:20px;border-radius:12px;max-height:84vh;overflow-y:auto">
    <h3>Pemasukan</h3>
    <div id="pmStep1"><div id="pmKatList"></div></div>
    <div id="pmStep2" style="display:none">
      <p id="pmJudul" style="font-weight:700;margin:6px 0"></p>
      <p style="margin:6px 0">Nominal:</p>
      <input id="pmNominal" type="text" inputmode="numeric" placeholder="0" style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px">
      <p style="margin:6px 0">Keterangan (tulis manual):</p>
      <input id="pmKet" type="text" placeholder="contoh: bunga kredivo" style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px">
      <div style="display:flex;gap:10px;margin-top:12px">
        <button type="button" onclick="simpanPemasukan()" style="flex:1;background:#4f46e5;color:white;padding:10px;border:0;border-radius:8px;font-weight:700">Simpan</button>
        <button type="button" onclick="openPemasukan()" style="flex:1;background:#64748b;color:white;padding:10px;border:0;border-radius:8px;font-weight:700">Kembali</button>
      </div>
    </div>
  </div>
</div>
<script>
var KAT_MASUK=[
{t:"a. Penerimaan Non-Operasional",s:["Pendapatan Bunga & Bagi Hasil","Pendapatan Investasi","Keuntungan Penjualan Aset Tetap (Gain on Disposal of Assets)","Keuntungan Selisih Kurs (Foreign Exchange Gain)","Penerimaan Klaim Asuransi"]},
{t:"b. Penerimaan Operasional Lainnya",s:["Pendapatan Sewa","Pendapatan Komisi / Fee Base","Penerimaan Biaya Pengiriman (Shipping Fee Refund)","Penjualan Limbah / Sisa Produksi (Scrap Sales)"]},
{t:"c. Penerimaan Pendanaan & Modal",s:["Setoran Modal Pemilik/Pemegang Saham","Pencairan Pinjaman Bank / Pihak Ketiga","Pengembalian Deposit / Uang Muka (Refund)"]},
{t:"d. Pengembalian Kasbon & Piutang Non-Usaha",s:["Pengembalian Kasbon Karyawan","Pelunasan Piutang Non-Usaha"]}
];
var pmSub='';
function openPemasukan(){
document.getElementById('pmStep2').style.display='none';
document.getElementById('pmStep1').style.display='block';
var el=document.getElementById('pmKatList');el.innerHTML='';
KAT_MASUK.forEach(function(k){
var b=document.createElement('button');b.type='button';b.textContent=k.t;
b.style.cssText='display:block;width:100%;margin:6px 0;padding:12px;border:1px solid #cbd5e1;border-radius:8px;background:#f8fafc;text-align:left;font-weight:600';
b.onclick=function(){pmOpenSub(k);};el.appendChild(b);
});
document.getElementById('modalPemasukan').style.display='block';
}
function pmOpenSub(k){
var el=document.getElementById('pmKatList');el.innerHTML='';
var back=document.createElement('button');back.type='button';back.textContent='‹ Kembali ke kategori';
back.style.cssText='display:block;width:100%;margin:6px 0;padding:10px;border:1px solid #cbd5e1;border-radius:8px;background:#e2e8f0;text-align:left;font-weight:600';
back.onclick=openPemasukan;el.appendChild(back);
k.s.forEach(function(sub){
var b=document.createElement('button');b.type='button';b.textContent=sub;
b.style.cssText='display:block;width:100%;margin:6px 0;padding:12px;border:1px solid #cbd5e1;border-radius:8px;background:#f8fafc;text-align:left;font-weight:600';
b.onclick=function(){
pmSub=sub;
document.getElementById('pmJudul').textContent=k.t+' › '+sub;
document.getElementById('pmNominal').value='';
document.getElementById('pmKet').value='';
document.getElementById('pmStep1').style.display='none';
document.getElementById('pmStep2').style.display='block';
};
el.appendChild(b);
});
}
function simpanPemasukan(){
var nom=parseInt((document.getElementById('pmNominal').value||'').replace(/[^\\d]/g,''))||0;
var ket=(document.getElementById('pmKet').value||'').trim();
if(nom<=0){alert('Nominal harus lebih dari 0');return;}
var fd=new FormData();
fd.append('keterangan',pmSub+(ket?' - '+ket:''));
fd.append('jumlah',nom);
fetch('/pemasukan',{method:'POST',body:fd}).then(function(r){return r.json();}).then(function(d){
if(d.ok){document.getElementById('modalPemasukan').style.display='none';alert('Pemasukan tercatat ✅');}
else{alert('Gagal menyimpan');}
});
}
</script>
'''
    idx = k.rfind('{% endblock %}')
    k = k[:idx] + UI + k[idx:]
    io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
    print("kasir + pemasukan ok")
