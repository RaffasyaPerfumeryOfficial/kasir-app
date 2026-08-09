import io, re
from app import models
from app.db import Base, engine
from sqlalchemy import inspect as sa_inspect, text
Base.metadata.create_all(bind=engine)
cols = [c["name"] for c in sa_inspect(engine).get_columns(models.Transaksi.__tablename__)]
if "poin_dipakai" not in cols:
    with engine.begin() as c:
        c.execute(text("ALTER TABLE " + models.Transaksi.__tablename__ + " ADD COLUMN poin_dipakai FLOAT DEFAULT 0"))
print("kolom poin ok")

s = io.open("app/main.py", encoding="utf-8").read()
m1 = re.search(r'@app\.post\("/transaksi"\)', s)
assert m1, "route transaksi tidak ketemu"
start = m1.start()
m2 = re.search(r'\n@app\.', s[start + 10:])
end = start + 10 + m2.start() if m2 else len(s)
NEW_ROUTE = '''@app.post("/transaksi")
def buat_transaksi(payload: dict = Body(...), db: Session = Depends(get_db)):
    import random, string
    from datetime import datetime
    items_in = payload.get("items", [])
    if not items_in:
        return JSONResponse({"ok": False, "detail": "Keranjang kosong"}, status_code=400)
    rows = []
    total = 0.0
    bibit_total = 0.0
    for it in items_in:
        p = db.get(models.Produk, int(it["produk_id"]))
        if not p:
            return JSONResponse({"ok": False, "detail": "Produk tidak ditemukan"}, status_code=400)
        qty = int(it["jumlah"])
        if getattr(p, "stok", None) is not None and p.stok < qty:
            return JSONResponse({"ok": False, "detail": "Stok kurang: " + p.nama}, status_code=400)
    for it in items_in:
        p = db.get(models.Produk, int(it["produk_id"]))
        qty = int(it["jumlah"])
        dsc = float(it.get("diskon") or 0)
        sub = (p.harga or 0) * qty - dsc
        total += sub
        if (p.kategori or "").upper() == "BIBIT":
            bibit_total += sub
        rows.append({"nama": p.nama, "jumlah": qty, "harga": p.harga, "diskon": dsc})
        if getattr(p, "stok", None) is not None:
            p.stok -= qty
    dt = float(payload.get("diskon_total") or 0)
    total -= dt
    poin = int(payload.get("poin_dipakai") or 0)
    ag_id = payload.get("anggota_id") or ""
    ag = db.get(models.Anggota, int(ag_id)) if ag_id else None
    if poin > 0:
        if not ag:
            return JSONResponse({"ok": False, "detail": "Pilih anggota dulu untuk pakai poin"}, status_code=400)
        if (ag.poin or 0) < poin:
            return JSONResponse({"ok": False, "detail": "Poin tidak cukup"}, status_code=400)
    t = models.Transaksi()
    t.items = json.dumps(rows)
    t.total = total
    t.total_diskon = dt + sum(r["diskon"] for r in rows)
    t.metode = payload.get("metode") or "TUNAI"
    t.bayar = float(payload.get("tunai") or 0)
    t.kembalian = float(payload.get("kembalian") or 0)
    t.poin_dipakai = poin
    t.kode_trx = "RP-MKRS/" + datetime.now().strftime("%m%d%y") + "/" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    db.add(t)
    db.flush()
    if ag:
        if poin > 0:
            ag.poin = (ag.poin or 0) - poin
        if bibit_total > 0:
            earn = int(bibit_total * 0.05)
            ag.poin = (ag.poin or 0) + earn
            db.add(models.PoinLog(anggota_id=ag.id, trx_id=t.id, poin=earn))
    db.commit()
    return {"ok": True, "id": t.id}


'''
s = s[:start] + NEW_ROUTE + s[end:]
io.open("app/main.py", "w", encoding="utf-8").write(s)
print("route transaksi ok")

k = io.open("templates/kasir.html", encoding="utf-8").read()
a = k.find('<div id="modal"')
if a == -1:
    a = k.find('<div id="modalBayar"')
assert a != -1, "modal bayar tidak ketemu"
b = k.find('<div id="modalPengeluaran"', a)
assert b != -1, "batas modal tidak ketemu"
MODAL = '''<div id="modalBayar" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:60">
  <div style="background:white;max-width:480px;margin:5vh auto;padding:20px;border-radius:12px;max-height:90vh;overflow-y:auto">
    <h3>Pembayaran</h3>
    <p style="margin:6px 0">Total: <strong>Rp <span id="total2">0</span></strong></p>
    <p style="margin:8px 0 4px">+ Anggota (member):</p>
    <select id="anggota_sel" style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px" onchange="onAnggota()"></select>
    <p id="poin_info" style="color:var(--muted);font-size:13px;margin:6px 0"></p>
    <p style="margin:10px 0 4px;font-weight:700">1) POIN (terlebih dahulu)</p>
    <input id="bayar_poin" type="text" inputmode="numeric" value="0" disabled oninput="fmtInput(this);updateBayar()">
    <p style="margin:10px 0 4px;font-weight:700">2) TUNAI</p>
    <input id="bayar_tunai" type="text" inputmode="numeric" value="0" oninput="fmtInput(this);updateBayar()">
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0">
      <button type="button" onclick="tambahNominal('bayar_tunai',10000)">10rb</button>
      <button type="button" onclick="tambahNominal('bayar_tunai',20000)">20rb</button>
      <button type="button" onclick="tambahNominal('bayar_tunai',50000)">50rb</button>
      <button type="button" onclick="tambahNominal('bayar_tunai',100000)">100rb</button>
      <button type="button" onclick="uangPas()">Uang Pas</button>
    </div>
    <p>Kembalian: <strong id="kembalian">Rp 0</strong></p>
    <p style="margin:10px 0 4px;font-weight:700">3) NON-TUNAI (otomatis sisa)</p>
    <select id="metode_sel" style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px" onchange="updateBayar()">
      <option>QRIS GOPAY</option>
      <option>QRIS SPAY</option>
      <option>QRIS DANA</option>
      <option>QRIS BCA</option>
      <option>QRIS BRI</option>
      <option>EDC BRI</option>
    </select>
    <p>Sisa non-tunai: <strong id="sisa">Rp 0</strong></p>
    <div style="display:flex;gap:10px;margin-top:14px">
      <button style="flex:1" onclick="bayar()">Konfirmasi</button>
      <button style="flex:1;background:#64748b" onclick="document.getElementById('modalBayar').style.display='none'">Batal</button>
    </div>
  </div>
</div>

'''
k = k[:a] + MODAL + k[b:]

a = k.find('function openBayar(')
assert a != -1, "js openBayar tidak ketemu"
cands = [k.find(x) for x in ['function openPengeluaran', 'const KATEGORI', 'function tanyaTutup'] if k.find(x) > a]
b = min(cands) if cands else len(k)
JS = '''let anggotaData=null;
function openBayar(){
if(cart.length===0){alert('Keranjang kosong');return;}
document.getElementById('total2').textContent=fmtRp(T);
document.getElementById('bayar_poin').value='0';
document.getElementById('bayar_tunai').value='0';
document.getElementById('kembalian').textContent='Rp 0';
document.getElementById('sisa').textContent='Rp 0';
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
if(!id){anggotaData=null;document.getElementById('bayar_poin').disabled=true;document.getElementById('bayar_poin').value='0';document.getElementById('poin_info').textContent='';}
else{fetch('/anggota/list').then(r=>r.json()).then(d=>{
anggotaData=d.find(function(x){return String(x.id)===String(id);});
document.getElementById('bayar_poin').disabled=false;
document.getElementById('poin_info').textContent='Poin tersedia: '+fmtRp(anggotaData?anggotaData.poin:0);
updateBayar();});}
updateBayar();
}
function hitungBayar(){
var poin=Math.min(numVal('bayar_poin'), anggotaData?Math.floor(anggotaData.poin):0, T);
var sisaP=T-poin;
var tunai=numVal('bayar_tunai');
var kemb=0,non=0;
if(tunai>=sisaP){kemb=tunai-sisaP;}else{non=sisaP-tunai;}
return {poin:poin,sisaP:sisaP,tunai:tunai,kemb:kemb,non:non};
}
function updateBayar(){
var h=hitungBayar();
document.getElementById('kembalian').textContent=fmtRp(h.kemb);
document.getElementById('sisa').textContent=fmtRp(h.non);
}
function updateKembalian(){updateBayar();}
function updateSplit(){}
function uangPas(){var h=hitungBayar();document.getElementById('bayar_tunai').value=fmtRp(h.sisaP);updateBayar();}
function tambahNominal(idEl,v){
var el=document.getElementById(idEl);
el.value=fmtRp((parseInt(el.value.replace(/[^\\d]/g,''))||0)+v);
updateBayar();
}
function bayar(){
if(cart.length===0){alert('Keranjang kosong');return;}
var h=hitungBayar();
if(h.poin>0&&!anggotaData){alert('Pilih anggota dulu untuk pakai poin');return;}
var met=document.getElementById('metode_sel').value;
var metode;
if(h.non>0&&h.tunai>0)metode='TUNAI + NON-TUNAI ('+met+')';
else if(h.non>0)metode='NON-TUNAI ('+met+')';
else metode='TUNAI';
if(h.poin>0)metode='POIN + '+metode;
var dt=numVal('diskon_all');
var payload={items:cart.map(function(i){return {produk_id:i.id,jumlah:i.jumlah,diskon:i.diskon||0};}),diskon_total:dt,anggota_id:(document.getElementById('anggota_sel').value||''),poin_dipakai:h.poin,tunai:h.tunai,kembalian:h.kemb,metode:metode};
fetch('/transaksi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(d=>{
if(d.ok){cart=[];T=0;document.getElementById('diskon_all').value='0';render();document.getElementById('modalBayar').style.display='none';window.location='/struk/'+d.id;}
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
print("popup 3 bagian ok")

t1 = io.open("templates/struk.html", encoding="utf-8").read()
if "poin_dipakai" not in t1:
    t1 = t1.replace('<tr><td>Bayar</td>', '{% if t.poin_dipakai %}<tr><td>POIN dipakai</td><td style="text-align:right">-{{ "%0.0f"|format(t.poin_dipakai) }}</td></tr>{% endif %}\n    <tr><td>Bayar</td>', 1)
    io.open("templates/struk.html", "w", encoding="utf-8").write(t1)
t2 = io.open("templates/struk_print.html", encoding="utf-8").read()
if "poin_dipakai" not in t2:
    t2 = t2.replace('{% if nontunai %}', '{% if t.poin_dipakai %}\n<table><tr><td class="r" style="width:60%">POIN :</td><td class="r">{{ (t.poin_dipakai or 0)|rpx }}</td></tr></table>\n<div class="line"></div>\n{% endif %}\n{% if nontunai %}', 1)
    io.open("templates/struk_print.html", "w", encoding="utf-8").write(t2)
print("struk poin ok")
