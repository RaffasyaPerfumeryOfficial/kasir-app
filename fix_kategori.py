import io, re
k = io.open("templates/kasir.html", encoding="utf-8").read()

NEW_MODAL = '''<div id="modalPengeluaran" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:60">
  <div style="background:white;max-width:560px;margin:4vh auto;padding:20px;border-radius:12px;max-height:92vh;overflow-y:auto">
    <div id="peng_step1">
      <h3 style="margin-bottom:10px">📂 Pilih Kategori Beban</h3>
      <div id="katList"></div>
      <button type="button" style="width:100%;margin-top:10px;background:#64748b" onclick="tutupPengeluaran()">Batal</button>
    </div>
    <div id="peng_step2" style="display:none">
      <h3 style="margin-bottom:10px" id="katJudul"></h3>
      <div id="subList"></div>
      <div style="display:flex;gap:10px;margin-top:10px">
        <button type="button" style="flex:1" onclick="showStep(1)">⬅ Kembali</button>
        <button type="button" style="flex:1;background:#64748b" onclick="tutupPengeluaran()">Batal</button>
      </div>
    </div>
    <div id="peng_step3" style="display:none">
      <h3 style="margin-bottom:4px" id="subJudul"></h3>
      <p style="color:var(--muted);font-size:13px;margin-bottom:10px">Isi nominal & keterangan, lalu Simpan.</p>
      <p style="margin:8px 0 4px;font-weight:600">Nominal (Rp) *</p>
      <input id="peng_nominal" type="number" placeholder="0" onclick="this.value=''">
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0">
        <button type="button" onclick="tambahNominal('peng_nominal',10000)">10rb</button>
        <button type="button" onclick="tambahNominal('peng_nominal',20000)">20rb</button>
        <button type="button" onclick="tambahNominal('peng_nominal',50000)">50rb</button>
        <button type="button" onclick="tambahNominal('peng_nominal',100000)">100rb</button>
      </div>
      <p style="margin:8px 0 4px;font-weight:600">Keterangan *</p>
      <input id="peng_ket" placeholder="misal: Paket Zoom, bayar PLN, gaji lembur">
      <div style="display:flex;gap:10px;margin-top:14px">
        <button type="button" style="flex:1;background:var(--success)" onclick="simpanPengeluaran()">💾 Simpan</button>
        <button type="button" style="flex:1" onclick="showStep(2)">⬅ Kembali</button>
        <button type="button" style="flex:1;background:#64748b" onclick="tutupPengeluaran()">Batal</button>
      </div>
    </div>
  </div>
</div>

'''

pat_modal = re.compile(r'<div id="modalPengeluaran"[\s\S]*?(?=<div id="modalTanya")')
assert pat_modal.search(k), "modal lama tidak ketemu"
k = pat_modal.sub(lambda m: NEW_MODAL, k, count=1)

NEW_JS = '''const KATEGORI=[
{t:"1. Beban Gaji & Kesejahteraan Karyawan",s:["Gaji & Upah","Bonus & THR","Kesejahteraan Karyawan","Pesangon & Kompensasi"]},
{t:"2. Beban Utilitas & Fasilitas",s:["Sewa Gedung/Kantor","Listrik & Air","Komunikasi & Internet","Kebersihan & Keamanan"]},
{t:"3. Beban Perlengkapan & Peralatan Kantor",s:["Alat Tulis Kantor (ATK)","Konsumsi & Dapur Kantor","Perlengkapan Habis Pakai","Sewa Peralatan"]},
{t:"4. Beban Pemeliharaan & Perbaikan",s:["Pemeliharaan Gedung","Pemeliharaan Kendaraan Operasional","Pemeliharaan Peralatan & Perangkat IT"]},
{t:"5. Beban Transportasi & Perjalanan Dinas & ONGKIR",s:["Bahan Bakar & Tol","Perjalanan Dinas","Ekspedisi & Pengiriman"]},
{t:"6. Beban Pemasaran & Penjualan",s:["Iklan & Promosi Digital","Media Cetak & Event","Komisi & Jamuan Klien"]},
{t:"7. Beban Profesional & Perizinan",s:["Jasa Profesional","Perizinan & Retribusi","Lisensi Software"]}
];
let pengSub="";
function openPengeluaran(){renderKat();showStep(1);}
function renderKat(){
const el=document.getElementById('katList');el.innerHTML='';
KATEGORI.forEach(function(k,i){
const b=document.createElement('button');b.type='button';b.textContent=k.t;
b.style.cssText='display:block;width:100%;margin:6px 0;padding:12px;border:1px solid #cbd5e1;border-radius:8px;background:#f8fafc;text-align:left;font-weight:600';
b.onclick=function(){openSub(i)};el.appendChild(b);});
}
function openSub(i){
const k=KATEGORI[i];
document.getElementById('katJudul').textContent=k.t;
const el=document.getElementById('subList');el.innerHTML='';
k.s.forEach(function(s2){
const b=document.createElement('button');b.type='button';b.textContent=s2;
b.style.cssText='display:block;width:100%;margin:6px 0;padding:12px;border:1px solid #cbd5e1;border-radius:8px;background:#f8fafc;text-align:left';
b.onclick=function(){openForm(s2)};el.appendChild(b);});
showStep(2);
}
function openForm(sub){
pengSub=sub;
document.getElementById('subJudul').textContent=sub;
document.getElementById('peng_nominal').value='';
document.getElementById('peng_ket').value='';
showStep(3);
}
function showStep(n){
document.getElementById('peng_step1').style.display=n===1?'block':'none';
document.getElementById('peng_step2').style.display=n===2?'block':'none';
document.getElementById('peng_step3').style.display=n===3?'block':'none';
document.getElementById('modalPengeluaran').style.display='block';
}
function tutupPengeluaran(){document.getElementById('modalPengeluaran').style.display='none';}
function simpanPengeluaran(){
const j=parseFloat(document.getElementById('peng_nominal').value||0);
const k=document.getElementById('peng_ket').value.trim();
if(j<=0){alert('⚠️ Nominal wajib diisi!');return;}
if(!k){alert('⚠️ Keterangan wajib diisi!');return;}
fetch('/pengeluaran/cepat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jumlah:j,keterangan:pengSub+' = '+k})}).then(r=>r.json()).then(d=>{
if(d.ok){alert('✅ Tercatat: '+pengSub+' = '+k+' (Rp '+j.toLocaleString('id-ID')+')');tutupPengeluaran();}
else{alert('Gagal menyimpan.');}
});
}
'''

pat_js = re.compile(r'function openPengeluaran\(\)[\s\S]*?(?=function tanyaTutup)')
assert pat_js.search(k), "js lama tidak ketemu"
k = pat_js.sub(lambda m: NEW_JS, k, count=1)
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("popup kategori ok")
