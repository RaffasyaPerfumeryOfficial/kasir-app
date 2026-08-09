import io, re

# ---------- 1) Model Anggota & PoinLog ----------
m = io.open("app/models.py", encoding="utf-8").read()
if "class Anggota" not in m:
    m += '''

class Anggota(Base):
    __tablename__ = "anggota"
    id = Column(Integer, primary_key=True)
    nama = Column(String)
    no_hp = Column(String)
    nomor_member = Column(String)
    poin = Column(Float, default=0)
    dibuat = Column(DateTime, default=datetime.now)

class PoinLog(Base):
    __tablename__ = "poin_log"
    id = Column(Integer, primary_key=True)
    anggota_id = Column(Integer)
    trx_id = Column(Integer)
    poin = Column(Float, default=0)
    dibuat = Column(DateTime, default=datetime.now)
'''
    io.open("app/models.py", "w", encoding="utf-8").write(m)
print("model anggota ok")

from app import models
from app.db import Base, engine
Base.metadata.create_all(bind=engine)

# ---------- 2) main.py: filter rp, route anggota, wa struk, transaksi baru ----------
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

if "filters[\"rp\"]" not in s:
    s += '''

def _rp_filter(v):
    try:
        return format(int(round(float(v))), ",").replace(",", ".")
    except Exception:
        return "0"
templates.env.filters["rp"] = _rp_filter
'''

if "/anggota" not in s:
    s += '''

@app.get("/anggota")
def anggota_page(request: Request, db: Session = Depends(get_db)):
    list_a = db.query(models.Anggota).order_by(models.Anggota.id.desc()).all()
    return templates.TemplateResponse(request, "anggota.html", {"anggota_list": list_a})

@app.post("/anggota/simpan")
def anggota_simpan(nama: str = Form(...), no_hp: str = Form(...), db: Session = Depends(get_db)):
    import random as _rnd, string as _str
    nom = "MS-" + "".join(_rnd.choices(_str.ascii_uppercase + _str.digits, k=6))
    db.add(models.Anggota(nama=nama.strip(), no_hp=no_hp.strip(), nomor_member=nom, poin=0))
    db.commit()
    return RedirectResponse("/anggota", status_code=303)

@app.get("/anggota/list")
def anggota_list(db: Session = Depends(get_db)):
    return [{"id": a.id, "label": a.nama + " | " + a.nomor_member} for a in db.query(models.Anggota).all()]


def rp0(x):
    return "Rp " + format(int(round(x)), ",").replace(",", ".")

def buat_teks_struk(db, t):
    L = []
    L.append("MEKAR SARI")
    L.append("Refill Perfumery")
    L.append("-----------------------------------------")
    L.append("No   : " + (t.kode_trx or ("TRX-" + str(t.id))))
    L.append("Waktu: " + t.dibuat.strftime("%d/%m/%Y %H:%M"))
    L.append("-----------------------------------------")
    for it in json.loads(t.items):
        L.append(it["nama"])
        L.append("  " + str(it["jumlah"]) + " x " + format(int(it.get("harga") or 0), ",").replace(",", ".") + " = " + format(int((it.get("harga") or 0) * it["jumlah"]), ",").replace(",", "."))
    L.append("-----------------------------------------")
    L.append("TOTAL  : " + rp0(t.total or 0))
    if t.total_diskon:
        L.append("Diskon : " + rp0(t.total_diskon))
    L.append("Bayar  : " + rp0(t.bayar or 0))
    L.append("Kembali: " + rp0(t.kembalian or 0))
    L.append("Metode : " + (t.metode or "TUNAI"))
    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    if pl:
        ag = db.get(models.Anggota, pl.anggota_id)
        if ag:
            L.append("-----------------------------------------")
            L.append("Anggota: " + ag.nama + " (" + ag.nomor_member + ")")
            L.append("Poin tambah: +" + format(int(pl.poin), ",").replace(",", "."))
            L.append("Poin total : " + format(int(ag.poin or 0), ",").replace(",", "."))
    L.append("-----------------------------------------")
    L.append("Terima kasih")
    L.append("Parfum Anda, cerita Anda.")
    return "\\n".join(L)

@app.get("/struk/{trx_id}/wa")
def struk_wa(trx_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Transaksi, trx_id)
    if not t:
        raise HTTPException(404, "tidak ditemukan")
    text = buat_teks_struk(db, t)
    hp = ""
    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    if pl:
        ag = db.get(models.Anggota, pl.anggota_id)
        if ag:
            hp = ag.no_hp or ""
    digits = "".join(ch for ch in hp if ch.isdigit())
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    url = ("https://wa.me/" + digits + "?text=" if digits else "https://wa.me/?text=")
    return {"text": text, "url": url}
'''

pat_trx = re.compile(r'@app\.post\("/transaksi"\)[\s\S]*?(?=\n@app\.)')
assert pat_trx.search(s), "route transaksi lama tidak ketemu"
new_trx = '''@app.post("/transaksi")
async def buat_transaksi(request: Request, db: Session = Depends(get_db)):
    import random as _rnd, string as _str
    d = await request.json()
    items_in = d.get("items", [])
    diskon_total = float(d.get("diskon_total") or 0)
    anggota_id = d.get("anggota_id") or ""
    rows = []
    total = 0.0
    bibit_total = 0.0
    for it in items_in:
        pr = db.get(models.Produk, int(it["produk_id"]))
        if not pr:
            continue
        qty = int(it["jumlah"])
        dsc = float(it.get("diskon") or 0)
        sub = (pr.harga or 0) * qty - dsc
        total += sub
        rows.append({"nama": pr.nama, "jumlah": qty, "harga": pr.harga, "diskon": dsc})
        if (pr.kategori or "").upper() == "BIBIT":
            bibit_total += sub
        pr.stok = (pr.stok or 0) - qty
    total = max(0, total - diskon_total)
    metode = d.get("metode", "TUNAI")
    tunai = float(d.get("tunai") or 0)
    channel = d.get("channel") or ""
    if metode == "TUNAI":
        p_tunai, p_non = total, 0.0
        bayar = tunai if tunai > 0 else total
        kembalian = bayar - total
        label = "TUNAI"
    elif metode == "NON":
        p_tunai, p_non = 0.0, total
        bayar = total
        kembalian = 0
        label = "NON-TUNAI (" + channel + ")"
    else:
        p_tunai = min(tunai, total)
        p_non = total - p_tunai
        bayar = total
        kembalian = 0
        label = "SPLIT (TUNAI+" + channel + ")"
    now = datetime.now()
    kode = "RP-MKRS/" + now.strftime("%d%m%y") + "/" + "".join(_rnd.choices(_str.ascii_uppercase + _str.digits, k=5))
    trx = models.Transaksi(
        kode_trx=kode,
        items=json.dumps(rows),
        total=total,
        total_diskon=diskon_total + sum(float(it.get("diskon") or 0) for it in items_in),
        bayar=bayar,
        kembalian=kembalian,
        metode=label,
        p_tunai=p_tunai,
        p_nontunai=p_non,
    )
    db.add(trx)
    db.commit()
    db.refresh(trx)
    poin = 0.0
    if anggota_id:
        poin = round(0.05 * bibit_total)
        ag = db.get(models.Anggota, int(anggota_id))
        if ag:
            ag.poin = (ag.poin or 0) + poin
            db.add(models.PoinLog(anggota_id=ag.id, trx_id=trx.id, poin=poin))
            db.commit()
    return {"ok": True, "id": trx.id, "kembalian": kembalian, "poin": poin}


'''
s = pat_trx.sub(lambda mm: new_trx, s, count=1)
io.open(p, "w", encoding="utf-8").write(s)
print("main.py ok")

# ---------- 3) base.html: pemisah ribuan otomatis + menu Anggota ----------
b = io.open("templates/base.html", encoding="utf-8").read()
if "rpWalker" not in b:
    b = b.replace("</body>", '''
<script>
function rpWalker(){
function fmt(s){return s.replace(/\\d{4,}/g,function(m2){return m2.replace(/\\B(?=(\\d{3})+(?!\\d))/g,'.')})}
var walk=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,null,false);
var nodes=[];
while(walk.nextNode())nodes.push(walk.currentNode);
nodes.forEach(function(n){
var tag=n.parentNode?n.parentNode.tagName:'';
if(tag==='SCRIPT'||tag==='STYLE'||tag==='INPUT'||tag==='OPTION'||tag==='SELECT'||tag==='TEXTAREA')return;
var t=n.nodeValue;
if(/\\d{4,}/.test(t)&&t.indexOf('.')===-1){n.nodeValue=fmt(t);}
});
}
document.addEventListener('DOMContentLoaded',rpWalker);
</script>
</body>''', 1)
if 'href="/anggota"' not in b:
    b = re.sub(r'(<a[^>]*href="/logout"[^>]*>)', '<a href="/anggota">Anggota</a>\n  \\1', b, count=1)
io.open("templates/base.html", "w", encoding="utf-8").write(b)
print("base ok")

# ---------- 4) kasir.html: format ribuan + anggota ----------
k = io.open("templates/kasir.html", encoding="utf-8").read()
R = [
("let cart=[];\nlet T=0;", "let cart=[];\nlet T=0;\nfunction fmtRp(n){n=Math.round(n||0);return n.toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g,'.');}\nfunction numVal(id){return parseInt((document.getElementById(id).value||'').replace(/[^\\d]/g,''))||0;}\nfunction fmtInput(el){el.value=el.value.replace(/[^\\d]/g,'');if(el.value==='')return;el.value=fmtRp(parseInt(el.value));}"),
("let dt=parseFloat(document.getElementById('diskon_all').value||0)||0;", "let dt=numVal('diskon_all');"),
("const dt=parseFloat(document.getElementById('diskon_all').value||0)||0;", "const dt=numVal('diskon_all');"),
('<input id="diskon_all" type="number" value="0" onclick="this.value=\'\'" oninput="render()">', '<input id="diskon_all" type="text" inputmode="numeric" value="0" oninput="fmtInput(this);render()">'),
("if(it){it.diskon=Math.max(0,parseFloat(v)||0);}", "if(it){it.diskon=Math.max(0,parseInt(String(v).replace(/[^\\d]/g,''))||0);}"),
("'<td><input type=\"number\" min=\"0\" value=\"'+(i.diskon||0)+'\" style=\"width:80px;margin:0\" onclick=\"this.value=\'\'\" onchange=\"setDiskon('+i.id+',this.value)\"></td>'+", "'<td><input type=\"text\" inputmode=\"numeric\" value=\"'+fmtRp(i.diskon||0)+'\" style=\"width:90px;margin:0\" oninput=\"fmtInput(this)\" onchange=\"setDiskon('+i.id+',this.value)\"></td>'+"),
("'<td>'+sub+'</td>'+", "'<td>'+fmtRp(sub)+'</td>'+"),
("document.getElementById('total').textContent=T;", "document.getElementById('total').textContent=fmtRp(T);"),
("document.getElementById('total2').textContent=T;", "document.getElementById('total2').textContent=fmtRp(T);"),
("document.getElementById('total3').textContent=T;", "document.getElementById('total3').textContent=fmtRp(T);"),
("const b=parseFloat(document.getElementById('bayar').value||0);\ndocument.getElementById('kembalian').textContent=b-T;", "const b=numVal('bayar');\ndocument.getElementById('kembalian').textContent=fmtRp(b-T);"),
("const s=parseFloat(document.getElementById('split_tunai').value||0);\ndocument.getElementById('sisa').textContent=Math.max(0,T-s);", "const s=numVal('split_tunai');\ndocument.getElementById('sisa').textContent=fmtRp(Math.max(0,T-s));"),
('<input id="bayar" type="number" onclick="this.value=\'\';updateKembalian()" oninput="updateKembalian()" placeholder="0">', '<input id="bayar" type="text" inputmode="numeric" oninput="fmtInput(this);updateKembalian()" placeholder="0">'),
('<input id="split_tunai" type="number" onclick="this.value=\'\';updateSplit()" oninput="updateSplit()" placeholder="0">', '<input id="split_tunai" type="text" inputmode="numeric" oninput="fmtInput(this);updateSplit()" placeholder="0">'),
("function uangPas(){document.getElementById('bayar').value=T;updateKembalian();}", "function uangPas(){document.getElementById('bayar').value=fmtRp(T);updateKembalian();}"),
("function tambahNominal(idEl,v){\nconst el=document.getElementById(idEl);\nel.value=(parseFloat(el.value)||0)+v;\nupdateKembalian();updateSplit();\n}", "function tambahNominal(idEl,v){\nconst el=document.getElementById(idEl);\nel.value=fmtRp((parseInt(el.value.replace(/[^\\d]/g,''))||0)+v);\nupdateKembalian();updateSplit();\n}"),
("const b=parseFloat(document.getElementById('bayar').value||0);\nif(b<T)", "const b=numVal('bayar');\nif(b<T)"),
("const s=parseFloat(document.getElementById('split_tunai').value||0);\nif(s<=0||s>=T)", "const s=numVal('split_tunai');\nif(s<=0||s>=T)"),
("const payload={items:cart.map(i=>({produk_id:i.id,jumlah:i.jumlah,diskon:i.diskon||0})),diskon_total:dt};", "const payload={items:cart.map(i=>({produk_id:i.id,jumlah:i.jumlah,diskon:i.diskon||0})),diskon_total:dt,anggota_id:(document.getElementById('anggota_sel').value||'')};"),
('<p style="margin:10px 0">Total: <strong>Rp <span id="total2">0</span></strong></p>', '<p style="margin:10px 0">Total: <strong>Rp <span id="total2">0</span></strong></p>\n    <p style="margin:10px 0 6px">+ Anggota (poin 5% belanja BIBIT):</p>\n    <select id="anggota_sel" style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;margin-bottom:8px"><option value="">-- Tanpa Anggota --</option></select>'),
("function openBayar(){\nif(cart.length===0){alert('Keranjang kosong');return;}", "function openBayar(){\nif(cart.length===0){alert('Keranjang kosong');return;}\nfetch('/anggota/list').then(r=>r.json()).then(d=>{\nvar s2=document.getElementById('anggota_sel');s2.innerHTML='<option value=\"\">-- Tanpa Anggota --</option>';\nd.forEach(function(a){var o=document.createElement('option');o.value=a.id;o.textContent=a.label;s2.appendChild(o);});\n});"),
("const j=parseFloat(document.getElementById('peng_nominal').value||0);", "const j=numVal('peng_nominal');"),
('<input id="peng_nominal" type="number" placeholder="0" onclick="this.value=\'\'">', '<input id="peng_nominal" type="text" inputmode="numeric" placeholder="0" oninput="fmtInput(this)">'),
('<td>{{ "%0.0f"|format(p.harga) }}</td>', '<td>{{ p.harga|rp }}</td>'),
]
for old, new in R:
    assert old in k, "tidak ketemu: " + old[:60]
    k = k.replace(old, new, 1)
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("kasir ok")

# ---------- 5) tombol WA di struk ----------
st = io.open("templates/struk.html", encoding="utf-8").read()
if "kirimWAStruk" not in st:
    st = st.replace("{% endblock %}", '''
<p style="margin-top:12px;text-align:center"><button style="background:#25D366" onclick="kirimWAStruk()">📱 Kirim via WhatsApp</button></p>
<script>
function kirimWAStruk(){
fetch(window.location.pathname+'/wa').then(r=>r.json()).then(d=>{window.open(d.url+encodeURIComponent(d.text),'_blank');});
}
</script>
{% endblock %}''', 1)
    io.open("templates/struk.html", "w", encoding="utf-8").write(st)
sp = io.open("templates/struk_print.html", encoding="utf-8").read()
if "kirimWAStruk" not in sp:
    sp = sp.replace('<p class="noprint"', '<p class="noprint" style="text-align:center"><button style="background:#25D366" onclick="kirimWAStruk()">📱 Kirim via WhatsApp</button></p>\n<p class="noprint"', 1)
    sp = sp.replace("</body>", "<script>function kirimWAStruk(){fetch(window.location.pathname.replace('/print','')+'/wa').then(r=>r.json()).then(d=>{window.open(d.url+encodeURIComponent(d.text),'_blank');});}</script>\n</body>", 1)
    io.open("templates/struk_print.html", "w", encoding="utf-8").write(sp)
print("struk wa ok")

# ---------- 6) halaman Anggota ----------
T = '''{% extends "base.html" %}
{% block title %}Anggota{% endblock %}
{% block content %}
<div class="topbar"><h2>Anggota / Member</h2><span class="badge">{{ anggota_list|length }} anggota</span></div>
<div class="grid">
  <div class="card">
    <div style="max-height:480px;overflow-y:auto">
      <table style="width:100%">
        <tr><th>Nama</th><th>No HP</th><th>Nomer Member</th><th style="text-align:right">Poin</th></tr>
        {% for a in anggota_list %}
        <tr>
          <td><strong>{{ a.nama }}</strong></td>
          <td>{{ a.no_hp }}</td>
          <td>{{ a.nomor_member }}</td>
          <td style="text-align:right"><strong>{{ "%0.0f"|format(a.poin or 0) }}</strong></td>
        </tr>
        {% else %}
        <tr><td colspan="4">Belum ada anggota.</td></tr>
        {% endfor %}
      </table>
    </div>
  </div>
  <div class="card">
    <h3 style="margin-bottom:12px">Tambahkan Anggota</h3>
    <form method="post" action="/anggota/simpan">
      <input name="nama" placeholder="Nama" required>
      <input name="no_hp" placeholder="No HP (misal 0853...)" required>
      <button style="width:100%">+ Tambah (nomer member otomatis)</button>
    </form>
    <p style="color:var(--muted);margin-top:10px;font-size:13px">Poin = 5% dari belanja kategori BIBIT, otomatis saat transaksi dengan memilih anggota di pembayaran.</p>
  </div>
</div>
{% endblock %}
'''
io.open("templates/anggota.html", "w", encoding="utf-8").write(T)
print("anggota ok")
