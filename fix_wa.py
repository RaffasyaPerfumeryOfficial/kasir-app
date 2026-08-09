import io, re

t1 = io.open("templates/struk.html", encoding="utf-8").read()
pat1 = re.compile(r'<script>\s*function kirimWAStruk\(\)\{[\s\S]*?</script>')
new1 = '''<script>
var WA_URL='';
fetch(location.pathname+'/wa').then(r=>r.json()).then(d=>{WA_URL=d.url+encodeURIComponent(d.text);}).catch(function(){alert('Gagal memuat data WA');});
function kirimWAStruk(){
if(!WA_URL){alert('Sedang memuat... klik lagi 1 detik lagi');return;}
window.open(WA_URL,'_blank');
}
</script>'''
t1, c1 = pat1.subn(new1, t1, count=1)
assert c1 == 1, "script wa struk tidak ketemu"
io.open("templates/struk.html", "w", encoding="utf-8").write(t1)

t2 = io.open("templates/struk_print.html", encoding="utf-8").read()
pat2 = re.compile(r'<script>\s*function kirimWAStruk\(\)\{[\s\S]*?</script>')
new2 = '''<script>
var WA_URL='';
fetch(location.pathname.replace('/print','')+'/wa').then(r=>r.json()).then(d=>{WA_URL=d.url+encodeURIComponent(d.text);}).catch(function(){alert('Gagal memuat data WA');});
function kirimWAStruk(){
if(!WA_URL){alert('Sedang memuat... klik lagi 1 detik lagi');return;}
window.open(WA_URL,'_blank');
}
</script>'''
t2, c2 = pat2.subn(new2, t2, count=1)
assert c2 == 1, "script wa print tidak ketemu"
io.open("templates/struk_print.html", "w", encoding="utf-8").write(t2)
print("tombol WA diperbaiki (struk + print)")
