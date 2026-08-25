from pathlib import Path

p = Path("templates/labarugi.html")
s = p.read_text(encoding="utf-8")

old = '''  <div class="card" style="border-left:4px solid var(--success)"><h3 style="color:var(--muted);font-size:13px">LABA BERSIH</h3><p style="font-size:22px;font-weight:800;color:var(--success)">Rp {{ "%0.0f"|format(tot.net - tot.hpp - tot.op + tot.pmsk) }}</p></div>'''

new = '''  <div class="card"><h3 style="color:var(--muted);font-size:13px">LABA KOTOR</h3><p style="font-size:22px;font-weight:800">Rp {{ "%0.0f"|format(tot.net - tot.hpp) }}</p></div>
  <div class="card" style="border-left:4px solid var(--success)"><h3 style="color:var(--muted);font-size:13px">LABA BERSIH</h3><p style="font-size:22px;font-weight:800;color:var(--success)">Rp {{ "%0.0f"|format(tot.net - tot.hpp - tot.op + tot.pmsk) }}</p></div>
  <div class="card"><h3 style="color:var(--muted);font-size:13px">MARGIN LABA</h3><p style="font-size:22px;font-weight:800">{{ "%0.1f"|format(((tot.net - tot.hpp - tot.op + tot.pmsk) / tot.net * 100) if tot.net else 0) }}%</p></div>
  <div class="card"><h3 style="color:var(--muted);font-size:13px">RATA-RATA TRX</h3><p style="font-size:22px;font-weight:800">Rp {{ "%0.0f"|format((tot.net / tot.trx) if tot.trx else 0) }}</p></div>'''

if old not in s:
    raise Exception("blok laba bersih tidak ditemukan")

s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")

print("OK dashboard laba detail")
