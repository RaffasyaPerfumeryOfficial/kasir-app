import io, re
p = "app/main.py"
s = io.open(p, encoding="utf-8").read()
m = re.search(r"def jawab_ai2\([^)]*\):", s)
assert m, "fungsi jawab_ai2 tidak ditemukan sama sekali"
if "jawab_fitur(q, db)" not in s:
    s = s[:m.end()] + "\n    _fit = jawab_fitur(q, db)\n    if _fit:\n        return _fit" + s[m.end():]
    io.open(p, "w", encoding="utf-8").write(s)
print("hook ok")

a = io.open("templates/ai.html", encoding="utf-8").read()
if "kirimBriefing" not in a:
    btn = '''
<div style="margin:10px 0"><button style="background:#0ea5e9;color:#fff;border:0;padding:10px 16px;border-radius:999px;font-weight:600" onclick="kirimBriefing()">🌅 Briefing Pagi</button></div>
<script>
function kirimBriefing(){
var i=document.querySelector('input[placeholder*="Tulis"]');
if(i){i.value='briefing pagi';}
var b=[].slice.call(document.querySelectorAll('button')).find(function(x){return x.textContent.trim()==='Kirim';});
if(b)b.click();
}
</script>
'''
    idx = a.rfind("{% endblock %}")
    a = a[:idx] + btn + a[idx:]
    io.open("templates/ai.html", "w", encoding="utf-8").write(a)
print("tombol briefing ok")

k = io.open("templates/struk.html", encoding="utf-8").read()
if "Cetak 80mm" not in k:
    pb = '''
<p style="margin-top:12px;text-align:center"><button onclick="window.location.href=window.location.href+'/print'">🖨️ Cetak 80mm</button></p>
'''
    idx = k.rfind("{% endblock %}")
    k = k[:idx] + pb + k[idx:]
    io.open("templates/struk.html", "w", encoding="utf-8").write(k)
print("tombol cetak ok")
