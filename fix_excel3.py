import io
t = io.open("templates/riwayat.html", encoding="utf-8").read()
if "Download Excel" not in t:
    block = '''
<div class="card" style="margin:15px 0">
  <form method="get" action="/transaksi/excel" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
    <input type="date" name="start_date" id="trx_start" style="padding:8px;border:1px solid #cbd5e1;border-radius:6px">
    <span>s/d</span>
    <input type="date" name="end_date" id="trx_end" style="padding:8px;border:1px solid #cbd5e1;border-radius:6px">
    <button type="submit" style="background:#16a34a;color:white;padding:8px 16px;border:0;border-radius:6px">📥 Download Excel (per struk)</button>
    <button type="button" onclick="setTrxPeriode(30)">30 Hari</button>
    <button type="button" onclick="setTrxPeriode(7)">7 Hari</button>
    <button type="button" onclick="setTrxPeriode(0)">Hari Ini</button>
  </form>
</div>
<script>
function setTrxPeriode(hari){
const now=new Date();const end=now.toISOString().split('T')[0];let start;
if(hari===0){start=end;}else{const d=new Date();d.setDate(d.getDate()-hari+1);start=d.toISOString().split('T')[0];}
document.getElementById('trx_start').value=start;document.getElementById('trx_end').value=end;
}
window.addEventListener('load',function(){setTrxPeriode(30);});
</script>
'''
    idx = t.find("</div>", t.find("topbar"))
    if idx == -1:
        idx = t.find("{% block content %}") + len("{% block content %}")
    t = t[:idx] + "\n" + block + t[idx:]
    io.open("templates/riwayat.html", "w", encoding="utf-8").write(t)
    print("tombol transaksi ok")
else:
    print("sudah ada, skip")
