import io, re

# 1) filter rpx (Rp45.000 tanpa spasi)
m = io.open("app/main.py", encoding="utf-8").read()
if "def _rpx(" not in m:
    m += '''

def _rpx(x):
    try:
        x = float(x)
    except Exception:
        x = 0.0
    return "Rp" + format(int(round(x)), ",").replace(",", ".")
templates.env.filters["rpx"] = _rpx
'''
    io.open("app/main.py", "w", encoding="utf-8").write(m)
print("filter rpx ok")

# 2) route print baru (jam cetak + ulang + subtotal)
m = io.open("app/main.py", encoding="utf-8").read()
pat = re.compile(r'@app\.get\("/struk/\{trx_id\}/print"\)[\s\S]*?(?=\n@app\.|\Z)')
assert pat.search(s := m), "route print tidak ketemu"
new = '''@app.get("/struk/{trx_id}/print")
def struk_print(trx_id: int, request: Request, ulang: str = "", db: Session = Depends(get_db)):
    t = db.get(models.Transaksi, trx_id)
    if not t:
        raise HTTPException(404, "Struk tidak ditemukan")
    raw = json.loads(t.items)
    sub = 0.0
    for it in raw:
        if not it.get("harga"):
            pr = db.query(models.Produk).filter_by(nama=it["nama"]).first()
            it["harga"] = pr.harga if pr else 0
        sub += (it["harga"] or 0) * it["jumlah"] - (it.get("diskon") or 0)
    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    ag = db.get(models.Anggota, pl.anggota_id) if pl else None
    from datetime import datetime as _dt
    now = _dt.now()
    BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Des"]
    now_str = "%02d %s %d, %02d.%02d" % (now.day, BULAN[now.month - 1], now.year, now.hour, now.minute)
    return templates.TemplateResponse(request, "struk_print.html", {
        "t": t, "items": raw, "ag": ag, "pl": pl,
        "ulang": bool(ulang), "now_str": now_str, "sub": sub,
        "nontunai": "NON" in (t.metode or "").upper()})


'''
m = pat.sub(lambda x: new, m, count=1)
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("route print ok")

# 3) template 80mm gaya foto
T = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Struk</title>
<style>
@page { size: 72mm auto; margin: 0; }
* { box-sizing: border-box; }
body { width: 72mm; margin: 0 auto; font-family: 'Courier New', monospace; font-size: 12px; color: #000; padding: 4mm 2mm; }
.c { text-align: center; }
.line { border-top: 1px dashed #000; margin: 6px 0; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
td { vertical-align: top; padding: 1px 0; }
.r { text-align: right; }
@media print { .noprint { display: none; } }
</style>
</head>
<body onload="setTimeout(function(){window.print()},300)">
<div class="c">
<img src="/static/logo.png" style="width:56px;height:56px;object-fit:contain;margin:0 auto 4px;display:block">
<strong style="font-size:14px">MEKAR SARI</strong> <span style="font-size:10px">perfumery</span><br>
<span style="font-size:10px">Refill Perfumery</span><br>
<span style="font-size:9px">Jl. Mekar Sari No.5, Bekasi Jaya, Kec. Bekasi Tim.,</span><br>
<span style="font-size:9px">Kota Bks, Jawa Barat 17112</span><br>
<span style="font-size:9px">HP: 0821-1897-1096</span>
</div>
<div class="c" style="margin-top:8px">
<div style="font-size:14px;font-weight:bold">MKSR - BEKASI</div>
<div>{{ t.kode_trx or ('TRX-' ~ t.id) }}</div>
</div>
<div class="line"></div>
<table>
<tr><td style="width:32%">Pelanggan</td><td>: {% if ag %}{{ ag.nama }}{% else %}MS - UMUM{% endif %}</td></tr>
<tr><td>Transaksi</td><td>: {{ now_str }}</td></tr>
<tr><td>Karyawan</td><td>: MKSR - Admin</td></tr>
</table>
<div class="line"></div>
{% if ulang %}
<div class="c" style="font-weight:bold">Cetak Ulang</div>
<div class="line"></div>
{% endif %}
{% for it in items %}
<div>{{ it.nama }}</div>
<div style="display:flex;justify-content:space-between">
<span>&nbsp;{{ it.jumlah }} x {{ (it.harga or 0)|rpx }}</span>
<span>{{ ((it.harga or 0) * it.jumlah - (it.get('diskon') or 0))|rpx }}</span>
</div>
{% endfor %}
<div class="line"></div>
<table>
<tr><td class="r" style="width:60%">Subtotal :</td><td class="r">{{ sub|rpx }}</td></tr>
{% if t.total_diskon %}<tr><td class="r">Diskon :</td><td class="r">{{ (t.total_diskon or 0)|rpx }}</td></tr>{% endif %}
<tr><td class="r">Total :</td><td class="r">{{ (t.total or 0)|rpx }}</td></tr>
</table>
<div class="line"></div>
<div style="text-align:right;font-size:16px;font-weight:bold">Grand Total : {{ (t.total or 0)|rpx }}</div>
<div class="line"></div>
{% if nontunai %}
<table><tr><td class="r" style="width:60%">{{ t.metode }} :</td><td class="r">{{ (t.total or 0)|rpx }}</td></tr></table>
<div class="line"></div>
{% endif %}
{% if ag %}
<table>
<tr><td style="width:60%">Poin +</td><td class="r">{{ "%0.0f"|format(pl.poin or 0) }}</td></tr>
<tr><td>Total poin</td><td class="r">{{ "%0.0f"|format(ag.poin or 0) }}</td></tr>
</table>
<div class="line"></div>
{% endif %}
<div class="c" style="margin-top:8px">Terima Kasih</div>
<p class="noprint" style="text-align:center">
<button onclick="window.print()">Cetak Lagi</button>
<button style="background:#25D366" onclick="kirimWAStruk()">📱 WA</button>
<button onclick="history.back()">Kembali</button>
</p>
<script>
function kirimWAStruk(){
fetch(location.pathname.replace('/print','')+'/wa').then(r=>r.json()).then(d=>{window.open(d.url+encodeURIComponent(d.text),'_blank');});
}
</script>
</body>
</html>
'''
io.open("templates/struk_print.html", "w", encoding="utf-8").write(T)
print("template 80mm ok")

# 4) tombol cetak di struk layar: bawa tanda ulang jika dari riwayat
k = io.open("templates/struk.html", encoding="utf-8").read()
old = """onclick="location.href=location.href+'/print'\""""
new = """onclick="location.href=location.pathname+'/print'+(location.search.indexOf('src=riwayat')>=0?'?ulang=1':'')\""""
assert old in k, "tombol cetak tidak ketemu"
k = k.replace(old, new, 1)
io.open("templates/struk.html", "w", encoding="utf-8").write(k)
print("tombol cetak ok")

# 5) link Struk di Riwayat bawa tanda
r = io.open("templates/riwayat_hari.html", encoding="utf-8").read()
oldr = '<a href="/struk/{{ r.t.id }}">Struk</a>'
newr = '<a href="/struk/{{ r.t.id }}?src=riwayat">Struk</a>'
assert oldr in r, "link struk riwayat tidak ketemu"
r = r.replace(oldr, newr, 1)
io.open("templates/riwayat_hari.html", "w", encoding="utf-8").write(r)
print("link riwayat ok")
