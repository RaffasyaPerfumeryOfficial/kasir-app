from pathlib import Path

p = Path("templates/struk.html")
s = p.read_text(encoding="utf-8")

old = '''var WA_URL="{{ wa_url|safe }}";
function kirimWAStruk(){window.open(WA_URL,'_blank');}
'''

new = '''var WA_URL="{{ wa_url|safe }}";

function kirimWAStruk(){

    var pesan = encodeURIComponent({{ teks|safe }});

    var app = "whatsapp://send?text=" + pesan;

    window.location.href = app;

    setTimeout(function(){
        window.open(WA_URL,'_blank');
    },1500);
}
'''

if old not in s:
    raise Exception("script WA lama tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK patch whatsapp app")
