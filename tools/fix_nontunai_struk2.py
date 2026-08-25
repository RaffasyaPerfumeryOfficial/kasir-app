from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

target = '''<td>Tunai</td>'''

pos = s.find(target)

if pos == -1:
    raise Exception("Tulisan Tunai tidak ditemukan")

end = s.find("</tr>", pos)

blok = s[pos:end+5]

if "Non-Tunai" in blok or "p_nontunai" in s:
    print("Non-tunai sudah ada")
else:
    tambah = '''
    {% if t.p_nontunai %}
    <tr>
      <td>Non-Tunai</td>
      <td class="r">{{ (t.p_nontunai or 0)|rpx }}</td>
    </tr>
    {% endif %}'''

    s = s[:end+5] + tambah + s[end+5:]

    p.write_text(s, encoding="utf-8")
    print("OK non-tunai ditambahkan")
