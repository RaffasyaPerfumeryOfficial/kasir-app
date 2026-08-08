import io
p = "templates/labarugi.html"
s = io.open(p, encoding="utf-8").read()

# Tambah tombol download di topbar atau setelah judul
download_btn = """
<div style="margin:15px 0">
  <form method="get" action="/laporan/laba_rugi/excel" style="display:inline">
    <input type="date" name="start_date" id="excel_start" style="padding:8px;border:1px solid #cbd5e1;border-radius:6px">
    <span> sampai </span>
    <input type="date" name="end_date" id="excel_end" style="padding:8px;border:1px solid #cbd5e1;border-radius:6px">
    <button type="submit" style="background:#16a34a;color:white;padding:8px 16px;border:0;border-radius:6px;cursor:pointer">📥 Download Excel</button>
  </form>
  <button type="button" onclick="setExcelPeriode(30)" style="margin-left:8px;padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer">30 Hari</button>
  <button type="button" onclick="setExcelPeriode(7)" style="padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer">7 Hari</button>
  <button type="button" onclick="setExcelPeriode(0)" style="padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer">Hari Ini</button>
</div>
<script>
function setExcelPeriode(hari){
  const now = new Date();
  const end = now.toISOString().split('T')[0];
  let start;
  if(hari === 0){
    start = end;
  } else {
    const d = new Date();
    d.setDate(d.getDate() - hari + 1);
    start = d.toISOString().split('T')[0];
  }
  document.getElementById('excel_start').value = start;
  document.getElementById('excel_end').value = end;
}
// Set default 30 hari saat load
window.addEventListener('load', function(){ setExcelPeriode(30); });
</script>
"""

if "Download Excel" not in s:
    # Cari posisi setelah <h2> atau topbar
    idx = s.find("</div>", s.find("topbar"))
    if idx == -1:
        idx = s.find("{% block content %}") + len("{% block content %}")
    s = s[:idx] + "\n" + download_btn + s[idx:]
    io.open(p, "w", encoding="utf-8").write(s)
    print("✅ Tombol Download Excel ditambahkan")
else:
    print("ℹ️ Tombol sudah ada, skip")
