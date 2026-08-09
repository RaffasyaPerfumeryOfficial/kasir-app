import io
p = "templates/struk.html"
s = io.open(p, encoding="utf-8").read()

CHUNK = '''
<p style="margin-top:12px;text-align:center"><button style="background:#25D366" onclick="kirimWAStruk()">📱 Kirim via WhatsApp</button></p>
<script>
function kirimWAStruk(){
fetch(window.location.pathname+'/wa').then(r=>r.json()).then(d=>{window.open(d.url+encodeURIComponent(d.text),'_blank');});
}
</script>
{% endblock %}'''

if "kirimWAStruk" in s:
    s = s.replace(CHUNK, "{% endblock %}", 1)
    idx = s.rfind("{% endblock %}")
    WA = '''
<p style="margin-top:12px;text-align:center"><button style="background:#25D366" onclick="kirimWAStruk()">📱 Kirim via WhatsApp</button></p>
<script>
function kirimWAStruk(){
fetch(window.location.pathname+'/wa').then(r=>r.json()).then(d=>{window.open(d.url+encodeURIComponent(d.text),'_blank');});
}
</script>
'''
    s = s[:idx] + WA + s[idx:]
    io.open(p, "w", encoding="utf-8").write(s)
    print("struk.html diperbaiki")
else:
    print("tidak ada yang perlu diperbaiki")
