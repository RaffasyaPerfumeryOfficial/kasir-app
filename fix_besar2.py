import io

k = io.open("templates/kasir.html", encoding="utf-8").read()
R = [
("let cart=[];\nlet T=0;", "let cart=[];\nlet T=0;\nfunction fmtRp(n){n=Math.round(n||0);return n.toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g,'.');}\nfunction numVal(id){return parseInt((document.getElementById(id).value||'').replace(/[^\\d]/g,''))||0;}\nfunction fmtInput(el){el.value=el.value.replace(/[^\\d]/g,'');if(el.value==='')return;el.value=fmtRp(parseInt(el.value));}"),
("let dt=parseFloat(document.getElementById('diskon_all').value||0)||0;", "let dt=numVal('diskon_all');"),
("const dt=parseFloat(document.getElementById('diskon_all').value||0)||0;", "const dt=numVal('diskon_all');"),
('<input id="diskon_all" type="number" value="0" onclick="this.value=\'\'" oninput="render()">', '<input id="diskon_all" type="text" inputmode="numeric" value="0" oninput="fmtInput(this);render()">'),
("if(it){it.diskon=Math.max(0,parseFloat(v)||0);}", "if(it){it.diskon=Math.max(0,parseInt(String(v).replace(/[^\\d]/g,''))||0);}"),
("'<td><input type=\"number\" min=\"0\" value=\"'+(i.diskon||0)+'\" style=\"width:80px;margin:0\" onclick=\"this.value=\\'\\'\" onchange=\"setDiskon('+i.id+',this.value)\"></td>'+", "'<td><input type=\"text\" inputmode=\"numeric\" value=\"'+fmtRp(i.diskon||0)+'\" style=\"width:90px;margin:0\" oninput=\"fmtInput(this)\" onchange=\"setDiskon('+i.id+',this.value)\"></td>'+"),
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
