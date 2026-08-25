from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

old = '''<tr>
      <td>Tunai</td>
      <td class="r">{{ (t.p_tunai or 0)|rpx }}</td>
    </tr>'''

new = '''<tr>
      <td>Tunai</td>
      <td class="r">{{ (t.p_tunai or 0)|rpx }}</td>
    </tr>
    {% if t.p_nontunai %}
    <tr>
      <td>Non-Tunai</td>
      <td class="r">{{ (t.p_nontunai or 0)|rpx }}</td>
    </tr>
    {% endif %}'''

if old not in s:
    raise Exception("Blok Tunai tidak ditemukan")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("OK non-tunai ditambahkan")
