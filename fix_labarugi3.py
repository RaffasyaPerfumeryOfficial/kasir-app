import io
k = io.open("templates/labarugi.html", encoding="utf-8").read()

# 1) munculkan kembali form Tampilkan (kostum tanggal)
if '<form style="display:none"' in k:
    k = k.replace('<form style="display:none"', '<form', 1)
    print("form tampilkan muncul")

# 2) tabel Rincian per Hari (jika belum ada)
if 'Rincian per Hari' not in k:
    TABLE = '''
<div class="card" style="margin-top:15px">
  <h3 style="margin-bottom:10px">Rincian per Hari</h3>
  <table style="width:100%">
    <tr><th>Tanggal</th><th>Trx</th><th>Gross</th><th>Diskon</th><th>Pendapatan</th><th>HPP</th><th>Operasional</th><th>Laba</th></tr>
    {% for d, r in rows %}
    <tr>
      <td>{{ d.strftime("%d/%m/%Y") }}</td>
      <td>{{ r.trx }}</td>
      <td>{{ "%0.0f"|format(r.gross) }}</td>
      <td>{{ "%0.0f"|format(r.disc) }}</td>
      <td>{{ "%0.0f"|format(r.net) }}</td>
      <td>{{ "%0.0f"|format(r.hpp) }}</td>
      <td>{{ "%0.0f"|format(r.op) }}</td>
      <td>{{ "%0.0f"|format(r.net - r.hpp - r.op) }}</td>
    </tr>
    {% endfor %}
    <tr style="background:#eef2ff;font-weight:700">
      <td>TOTAL</td>
      <td>{{ tot.trx }}</td>
      <td>{{ "%0.0f"|format(tot.gross) }}</td>
      <td>{{ "%0.0f"|format(tot.disc) }}</td>
      <td>{{ "%0.0f"|format(tot.net) }}</td>
      <td>{{ "%0.0f"|format(tot.hpp) }}</td>
      <td>{{ "%0.0f"|format(tot.op) }}</td>
      <td>{{ "%0.0f"|format(tot.net - tot.hpp - tot.op) }}</td>
    </tr>
  </table>
</div>
'''
    idx = k.rfind('{% endblock %}')
    k = k[:idx] + TABLE + k[idx:]
    print("tabel rincian ok")
io.open("templates/labarugi.html", "w", encoding="utf-8").write(k)
print("labarugi kostum ok")
