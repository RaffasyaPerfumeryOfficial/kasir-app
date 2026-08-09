import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()

pat = re.compile(r'@app\.get\("/struk/\{trx_id\}"\)[\s\S]*?(?=\n@app\.)')
if pat.search(s):
    s = pat.sub(lambda m: "", s, count=1)
    print("route struk lama dihapus")
else:
    print("route struk lama tidak ditemukan (lanjut)")

if "def struk_page(" not in s:
    s += '''

@app.get("/struk/{trx_id}")
def struk_page(trx_id: int, request: Request, db: Session = Depends(get_db)):
    t = db.get(models.Transaksi, trx_id)
    if not t:
        raise HTTPException(404, "Struk tidak ditemukan")
    raw = json.loads(t.items)
    for it in raw:
        if not it.get("harga"):
            pr = db.query(models.Produk).filter_by(nama=it["nama"]).first()
            it["harga"] = pr.harga if pr else 0
    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    ag = db.get(models.Anggota, pl.anggota_id) if pl else None
    return templates.TemplateResponse(request, "struk.html", {"t": t, "items": raw, "ag": ag, "pl": pl})
'''
    io.open(p, "w", encoding="utf-8").write(s)
print("route struk baru ok")

T = '''{% extends "base.html" %}
{% block title %}Struk{% endblock %}
{% block content %}
<div class="card" style="max-width:440px;margin:20px auto;padding:20px">
  <div style="text-align:center">
    <h3 style="margin:0">MEKAR SARI</h3>
    <div style="color:var(--muted)">Refill Perfumery</div>
  </div>
  <hr style="border-top:1px dashed #94a3b8">
  <table style="width:100%;font-size:14px">
    <tr><td>No</td><td style="text-align:right">{{ t.kode_trx or ('TRX-' ~ t.id) }}</td></tr>
    <tr><td>Waktu</td><td style="text-align:right">{{ t.dibuat.strftime('%d/%m/%Y %H:%M') }}</td></tr>
    <tr><td>Metode</td><td style="text-align:right">{{ t.metode or 'TUNAI' }}</td></tr>
  </table>
  <hr style="border-top:1px dashed #94a3b8">
  {% for it in items %}
  <div style="font-size:14px">{{ it.nama }}</div>
  <div style="display:flex;justify-content:space-between;font-size:14px">
    <span>&nbsp;&nbsp;{{ it.jumlah }} x {{ "%0.0f"|format(it.harga or 0) }}</span>
    <span>{{ "%0.0f"|format((it.harga or 0) * it.jumlah) }}</span>
  </div>
  {% endfor %}
  <hr style="border-top:1px dashed #94a3b8">
  <table style="width:100%;font-size:14px">
    <tr><td><strong>TOTAL</strong></td><td style="text-align:right"><strong>Rp {{ "%0.0f"|format(t.total or 0) }}</strong></td></tr>
    {% if t.total_diskon %}<tr><td>Diskon</td><td style="text-align:right">{{ "%0.0f"|format(t.total_diskon) }}</td></tr>{% endif %}
    <tr><td>Bayar</td><td style="text-align:right">{{ "%0.0f"|format(t.bayar or 0) }}</td></tr>
    <tr><td>Kembali</td><td style="text-align:right">{{ "%0.0f"|format(t.kembalian or 0) }}</td></tr>
  </table>
  {% if ag %}
  <hr style="border-top:1px dashed #94a3b8">
  <table style="width:100%;font-size:14px">
    <tr><td>Anggota</td><td style="text-align:right">{{ ag.nama }} ({{ ag.nomor_member }})</td></tr>
    <tr><td>Poin tambah</td><td style="text-align:right">+{{ "%0.0f"|format(pl.poin or 0) }}</td></tr>
    <tr><td>Poin total</td><td style="text-align:right">{{ "%0.0f"|format(ag.poin or 0) }}</td></tr>
  </table>
  {% endif %}
  <hr style="border-top:1px dashed #94a3b8">
  <div style="text-align:center;color:var(--muted)">Terima kasih 🙏<br>Parfum Anda, cerita Anda.</div>
</div>
<p style="text-align:center;display:flex;gap:8px;justify-content:center">
  <button type="button" onclick="location.href=location.href+'/print'">🖨️ Cetak 80mm</button>
  <button type="button" style="background:#25D366" onclick="kirimWAStruk()">📱 Kirim via WhatsApp</button>
  <button type="button" style="background:#64748b" onclick="location.href='/kasir'">⬅ Kasir</button>
</p>
<script>
function kirimWAStruk(){
fetch(location.pathname+'/wa').then(r=>r.json()).then(d=>{window.open(d.url+encodeURIComponent(d.text),'_blank');});
}
</script>
{% endblock %}
'''
io.open("templates/struk.html", "w", encoding="utf-8").write(T)
print("template struk baru ok")
