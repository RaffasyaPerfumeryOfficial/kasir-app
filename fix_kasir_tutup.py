import io
k = io.open("templates/kasir.html", encoding="utf-8").read()

# Tambah tombol Tutup Kasir di topbar (sebelah + Pengeluaran)
old_topbar = '''<button type="button" style="margin-left:auto;background:var(--danger)" onclick="openPengeluaran()">+ Pengeluaran</button>'''
new_topbar = '''<button type="button" style="margin-left:auto;background:var(--danger)" onclick="openPengeluaran()">+ Pengeluaran</button>
  <button type="button" style="background:#0f766e" onclick="tanyaTutup()">Tutup Kasir</button>'''
if old_topbar in k and "tanyaTutup" not in k:
    k = k.replace(old_topbar, new_topbar)

# Tambah modal tanya + modal ringkasan (sebelum <script>)
modal_html = """
<div id="modalTanya" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:70">
  <div style="background:white;max-width:380px;margin:15vh auto;padding:24px;border-radius:12px;text-align:center">
    <h3>Apakah Anda sudah ingin Tutup Kasir?</h3>
    <div style="display:flex;gap:10px;margin-top:18px">
      <button style="flex:1;background:var(--success)" onclick="tutupTanya(true)">Ya</button>
      <button style="flex:1;background:#64748b" onclick="tutupTanya(false)">Tidak</button>
    </div>
  </div>
</div>

<div id="modalTutup" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:70">
  <div style="background:white;max-width:480px;margin:5vh auto;padding:20px;border-radius:12px">
    <pre id="ringkasanPre" style="white-space:pre-wrap;font-size:13px"></pre>
    <div style="display:flex;gap:10px;margin-top:14px">
      <button style="flex:1;background:#25D366" onclick="kirimWA()">Kirim via WhatsApp</button>
      <button style="flex:1;background:#64748b" onclick="selesaiTutup()">Selesai</button>
    </div>
  </div>
</div>
"""
if "modalTanya" not in k:
    k = k.replace("<script>", modal_html + "\n<script>")

# Tambah fungsi JS (sebelum filter();)
js_funcs = """
function tanyaTutup(){document.getElementById('modalTanya').style.display='block';}
function tutupTanya(ya){
document.getElementById('modalTanya').style.display='none';
if(!ya)return;
fetch('/tutup/preview').then(r=>r.json()).then(d=>{
fetch('/tutup/simpan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).then(()=>{
window.__ringkasan=d.text;
document.getElementById('ringkasanPre').textContent=d.text;
document.getElementById('modalTutup').style.display='block';
});
});
}
function kirimWA(){window.open('https://wa.me/?text='+encodeURIComponent(window.__ringkasan),'_blank');}
function selesaiTutup(){document.getElementById('modalTutup').style.display='none';}
"""
if "tanyaTutup" not in k:
    k = k.replace("filter();", js_funcs + "\nfilter();")

io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("✅ Tombol & popup Tutup Kasir ditambahkan ke halaman Kasir")
