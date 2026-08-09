import io

k = io.open("templates/kasir.html", encoding="utf-8").read()

a = k.find('<div id="modalBayar"')
assert a != -1, "modalBayar tidak ketemu"
b = k.find('<div id="modalPengeluaran"', a)
assert b != -1
MODAL = '''<div id="modalBayar" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:60">
  <div style="background:white;max-width:480px;margin:5vh auto;padding:20px;border-radius:12px;max-height:90vh;overflow-y:auto">
    <h3>Pembayaran</h3>
    <p style="margin:6px 0">Total: <strong>Rp <span id="total2">0</span></strong></p>
    <p style="margin:8px 0 4px">+ Anggota (member):</p>
    <select id="anggota_sel" style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px" onchange="onAnggota()"></select>
    <p id="poin_info" style="color:var(--muted);font-size:13px;margin:6px 0"></p>
    <div id="box_poin" style="display:none;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:10px;margin:8px 0">
      <label style="font-weight:700"><input type="checkbox" id="pakai_poin" onchange="onPoinCheck()"> 💚 Gunakan POIN</label>
      <input id="bayar_poin" type="text" inputmode="numeric" value="0" style="margin-top:6px" oninput="fmtInput(this);updateBayar()">
      <p style="color:var(--muted);font-size:12px;margin:4px 0 0">Poin terpotong otomatis dari member (maks = poin tersedia).</p>
    </div>
    <p style="margin:12px 0 6px;font-weight:700">Metode Pembayaran:</p>
    <div style="display:flex;gap:14px;flex-wrap:wrap">
      <label><input type="radio" name="met" value="TUNAI" checked onchange="switchMet()"> TUNAI</label>
      <label><input type="radio" name="met" value="NON" onchange="switchMet()"> NON-TUNAI</label>
      <label><input type="radio" name="met" value="SPLIT" onchange="switchMet()"> SPLIT</label>
    </div>
    <div id="box_tunai" style="margin-top:10px">
      <p style="font-weight:600;margin:4px 0">Tunai:</p>
      <input id="bayar_tunai" type="text" inputmode="numeric" value="0" oninput="fmtInput(this);updateBayar()">
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0">
        <button type="button" onclick="tambahNominal('bayar_tunai',10000)">10rb</button>
        <button type="button" onclick="tambahNominal('bayar_tunai',20000)">20rb</button>
        <button type="button" onclick="tambahNominal('bayar_tunai',50000)">50rb</button>
        <button type="button" onclick="tambahNominal('bayar_tunai',100000)">100rb</button>
        <button type="button" onclick="uangPas()">Uang Pas</button>
      </div>
      <p>Kembalian: <strong id="kembalian">Rp 0</strong></p>
    </div>
    <div id="box_non" style="display:none;margin-top:10px">
      <p style="font-weight:600;margin:4px 0">Channel:</p>
      <select id="metode_sel" style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px" onchange="updateBayar()">
        <option>QRIS GOPAY</option>
        <option>QRIS SPAY</option>
        <option>QRIS DANA</option>
        <option>QRIS BCA</option>
        <option>QRIS BRI</option>
        <option>EDC BRI</option>
      </select>
      <p>Sisa non-tunai: <strong id="sisa">Rp 0</strong></p>
    </div>
    <div style="display:flex;gap:10px;margin-top:14px">
      <button style="flex:1" onclick="bayar()">Konfirmasi</button>
      <button style="flex:1;background:#64748b" onclick="document.getElementById('modalBayar').style.display='none'">Batal</button>
    </div>
  </div>
</div>

'''
k = k[:a] + MODAL + k[b:]

a = k.find('function openBayar(')
assert a != -1, "openBayar tidak ketemu"
cands = [k.find(x) for x in ['function openPengeluaran', 'const KATEGORI', 'function tanyaTutup'] if k.find(x) > a]
b = min(cands) if cands else len(k)
JS = '''let anggotaData=null;
function getMet(){var r=document.querySelector('input[name="met"]:checked');return r?r.value:'TUNAI';}
function switchMet(){
var m=getMet();
document.getElementById('box_tunai').style.display=(m==='NON')?'none':'block';
document.getElementById('box_non').style.display=(m==='TUNAI')?'none':'block';
updateBayar();
}
function onPoinCheck(){
if(document.getElementById('pakai_poin').checked&&anggotaData){
document.getElementById('bayar_poin').value=fmtRp(Math.min(Math.floor(anggotaData.poin||0),T));
}
updateBayar();
}
function openBayar(){
if(cart.length===0){alert('Keranjang kosong');return;}
setTxt('total2',fmtRp(T));
document.getElementById('bayar_poin').value='0';
document.getElementById('bayar_tunai').value='0';
document.getElementById('pakai_poin').checked=false;
document.getElementById('box_poin').style.display='none';
document.getElementById('poin_info').textContent='';
document.querySelector('input[name="met"][value="TUNAI"]').checked=true;
switchMet();
anggotaData=null;
fetch('/anggota/list').then(r=>r.json()).then(d=>{
var s2=document.getElementById('anggota_sel');s2.innerHTML='<option value="">-- Tanpa Anggota --</option>';
d.forEach(function(a2){var o=document.createElement('option');o.value=a2.id;o.textContent=a2.label;s2.appendChild(o);});
});
document.getElementById('modalBayar').style.display='block';
updateBayar();
}
function onAnggota(){
var id=document.getElementById('anggota_sel').value;
if(!id){anggotaData=null;document.getElementById('box_poin').style.display='none';document.getElementById('poin_info').textContent='';}
else{fetch('/anggota/list').then(r=>r.json()).then(d=>{
anggotaData=d.find(function(x){return String(x.id)===String(id);});
document.getElementById('box_poin').style.display='block';
document.getElementById('poin_info').textContent='Poin tersedia: '+fmtRp(anggotaData?anggotaData.poin:0);
onPoinCheck();
updateBayar();});}
updateBayar();
}
function hitungBayar(){
var poin=0;
if(anggotaData&&document.getElementById('pakai_poin').checked){
poin=Math.min(numVal('bayar_poin'),Math.floor(anggotaData.poin||0),T);
}
var sisaP=T-poin;
var m=getMet();
var tunai=0,non=0,kemb=0;
if(m==='NON'){non=sisaP;}
else{tunai=numVal('bayar_tunai');
if(tunai>=sisaP){kemb=tunai-sisaP;}else if(m==='SPLIT'){non=sisaP-tunai;}}
return {poin:poin,sisaP:sisaP,tunai:tunai,non:non,kemb:kemb,met:m};
}
function updateBayar(){
var h=hitungBayar();
setTxt('kembalian',fmtRp(h.kemb));
setTxt('sisa',fmtRp(h.non));
}
function updateKembalian(){updateBayar();}
function updateSplit(){}
function uangPas(){var h=hitungBayar();document.getElementById('bayar_tunai').value=fmtRp(h.sisaP);updateBayar();}
function tambahNominal(idEl,v){var el=document.getElementById(idEl);el.value=fmtRp((parseInt(el.value.replace(/[^\\d]/g,''))||0)+v);updateBayar();}
function bayar(){
if(cart.length===0){alert('Keranjang kosong');return;}
var h=hitungBayar();
if(h.met==='TUNAI'&&h.tunai<h.sisaP){alert('Tunai kurang! Kurang '+fmtRp(h.sisaP-h.tunai));return;}
if(h.poin>0&&!anggotaData){alert('Pilih anggota dulu');return;}
var ch=document.getElementById('metode_sel').value;
var metode;
if(h.non>0&&h.tunai>0)metode='TUNAI + NON-TUNAI ('+ch+')';
else if(h.non>0)metode='NON-TUNAI ('+ch+')';
else metode='TUNAI';
if(h.poin>0)metode='POIN + '+metode;
var dt=numVal('diskon_all');
var payload={items:cart.map(function(i){return {produk_id:i.id,jumlah:i.jumlah,diskon:i.diskon||0};}),diskon_total:dt,anggota_id:(document.getElementById('anggota_sel').value||''),poin_dipakai:h.poin,tunai:h.tunai,kembalian:h.kemb,metode:metode};
fetch('/transaksi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(d=>{
if(d.ok){document.getElementById('modalBayar').style.display='none';window.location.href='/struk/'+d.id;}
else{alert(d.detail||'Gagal');}
});
}
'''
k = k[:a] + JS + k[b:]
OLD_TN = "function tambahNominal(idEl,v){\nvar el=document.getElementById(idEl);\nel.value=fmtRp((parseInt(el.value.replace(/[^\\d]/g,''))||0)+v);\nupdateKembalian();updateSplit();\n}"
while k.count("function tambahNominal") > 1:
    idx = k.find(OLD_TN)
    if idx == -1:
        break
    k = k[:idx] + k[idx + len(OLD_TN):]
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("popup pembayaran rapih ok")
