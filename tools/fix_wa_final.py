from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

start = s.find("<script>")
end = s.find("</script>", start)

if start == -1:
    raise Exception("script tidak ditemukan")

new = '''<script>
var WA_URL="{{ wa_url|safe }}";

function kirimWAStruk(){

    var pesan = {{ teks|safe }};

    var url = "https://wa.me/?text=" + encodeURIComponent(pesan);

    window.open(url, "_blank");

}
</script>'''

s = s[:start] + new + s[end+9:]

p.write_text(s, encoding="utf-8")

print("OK WA pakai whatsapp web")
