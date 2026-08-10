import io
k = io.open("templates/labarugi.html", encoding="utf-8").read()
if 'id="nav_lr"' in k:
    print("sudah ada")
else:
    i = k.find('<form')
    assert i != -1, "form tidak ketemu"
    NAV = '''<div class="card" id="nav_lr" style="margin:0 0 15px;text-align:center">
  <div style="display:flex;align-items:center;justify-content:center;gap:14px">
    <button type="button" onclick="geserLR(-1)" style="font-size:20px;font-weight:800;padding:4px 14px;border:1px solid #cbd5e1;border-radius:8px;background:white">&lt;</button>
    <strong id="lr_tanggal" style="font-size:18px;min-width:150px">-</strong>
    <button type="button" id="lr_next" onclick="geserLR(1)" style="font-size:20px;font-weight:800;padding:4px 14px;border:1px solid #cbd5e1;border-radius:8px;background:white">&gt;</button>
  </div>
  <div style="color:var(--muted);font-size:12px;margin-top:6px">&lt; hari sebelumnya • &gt; hari berikutnya (maksimal hari ini)</div>
</div>
'''
    k = k[:i] + NAV + k[i:]
    k = k.replace('<form', '<form style="display:none"', 1)
    JS = '''<script>
function lrParse(v){var p=v.split('-');return new Date(+p[0],+p[1]-1,+p[2]);}
function lrFmt(d){var m=('0'+(d.getMonth()+1)).slice(-2);var dd=('0'+d.getDate()).slice(-2);return d.getFullYear()+'-'+m+'-'+dd;}
function lrToday(){var n=new Date();return new Date(n.getFullYear(),n.getMonth(),n.getDate());}
var lrForm=document.querySelector('form[action="/labarugi"]');
var lrStart=lrForm.querySelector('input[name="start_date"]');
var lrEnd=lrForm.querySelector('input[name="end_date"]');
function lrCur(){return lrParse(lrStart.value||lrFmt(lrToday()));}
function lrRender(){
document.getElementById('lr_tanggal').textContent=lrFmt(lrCur());
var dis=lrCur().getTime()>=lrToday().getTime();
document.getElementById('lr_next').disabled=dis;
document.getElementById('lr_next').style.opacity=dis?'0.3':'1';
}
function geserLR(n){
var d=lrCur();d.setDate(d.getDate()+n);
if(d>lrToday())d=lrToday();
lrStart.value=lrFmt(d);lrEnd.value=lrFmt(d);
lrForm.submit();
}
window.addEventListener('load',lrRender);
</script>
'''
    idx = k.rfind('{% endblock %}')
    k = k[:idx] + JS + k[idx:]
    io.open("templates/labarugi.html", "w", encoding="utf-8").write(k)
    print("navigator laba rugi ok")
