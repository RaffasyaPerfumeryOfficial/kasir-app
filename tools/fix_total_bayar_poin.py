from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

old = '''    <tr><td><strong>TOTAL</strong></td><td style="text-align:right"><strong>Rp {{ "%0.0f"|format(t.total or 0) }}</strong></td></tr>
    {% if t.total_diskon %}<tr><td>Diskon</td><td style="text-align:right">{{ "%0.0f"|format(t.total_diskon) }}</td></tr>{% endif %}
    {% if t.poin_dipakai %}<tr><td>POIN dipakai</td><td style="text-align:right">-{{ "%0.0f"|format(t.poin_dipakai) }}</td></tr>{% endif %}
    <tr><td>Bayar</td><td style="text-align:right">{{ "%0.0f"|format(t.bayar or 0) }}</td></tr>
    <tr><td>Kembali</td><td style="text-align:right">{{ "%0.0f"|format(t.kembalian or 0) }}</td></tr>'''

new = '''    <tr><td><strong>TOTAL</strong></td><td style="text-align:right"><strong>Rp {{ "%0.0f"|format(t.total or 0) }}</strong></td></tr>
    {% if t.total_diskon %}<tr><td>Diskon</td><td style="text-align:right">{{ "%0.0f"|format(t.total_diskon) }}</td></tr>{% endif %}

    {% if t.poin_dipakai %}
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
    {% endif %}'''

if old not in s:
    raise Exception("Blok total pembayaran tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK total bayar poin diperbaiki")
