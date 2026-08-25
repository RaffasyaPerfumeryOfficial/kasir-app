from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

old = """    {% if t.poin_dipakai %}
    <tr>
      <td>POIN dipakai</td>
      <td style="text-align:right">-{{ "%0.0f"|format(t.poin_dipakai) }}</td>
    </tr>
    <tr>
      <td><strong>TOTAL BAYAR</strong></td>
      <td style="text-align:right">
        <strong>Rp {{ "%0.0f"|format((t.total or 0) - (t.poin_dipakai or 0)) }}</strong>
      </td>
    </tr>
    {% else %}
    <tr><td>Bayar</td><td style="text-align:right">{{ "%0.0f"|format(t.bayar or 0) }}</td></tr>
    <tr><td>Kembali</td><td style="text-align:right">{{ "%0.0f"|format(t.kembalian or 0) }}</td></tr>
    {% endif %}
"""

new = """    <tr>
      <td><strong>PEMBAYARAN</strong></td>
      <td></td>
    </tr>

    {% if t.poin_dipakai %}
    <tr>
      <td>Poin</td>
      <td style="text-align:right">-{{ "%0.0f"|format(t.poin_dipakai) }}</td>
    </tr>
    {% endif %}

    {% if t.bayar %}
    <tr>
      <td>Tunai</td>
      <td style="text-align:right">{{ "%0.0f"|format(t.bayar) }}</td>
    </tr>
    {% endif %}

    {% if t.p_nontunai %}
    <tr>
      <td>QRIS</td>
      <td style="text-align:right">{{ "%0.0f"|format(t.p_nontunai) }}</td>
    </tr>
    {% endif %}

    <tr>
      <td><strong>TOTAL BAYAR</strong></td>
      <td style="text-align:right">
        <strong>Rp {{ "%0.0f"|format((t.total or 0) - (t.poin_dipakai or 0)) }}</strong>
      </td>
    </tr>

    {% if not t.poin_dipakai and not t.p_nontunai %}
    <tr>
      <td>Kembali</td>
      <td style="text-align:right">{{ "%0.0f"|format(t.kembalian or 0) }}</td>
    </tr>
    {% endif %}
"""

if old not in s:
    raise Exception("Blok pembayaran struk.html tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("OK pembayaran struk.html dirapikan")
