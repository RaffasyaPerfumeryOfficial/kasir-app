import io
k = io.open("templates/kasir.html", encoding="utf-8").read()

# 1) helper aman
old = "function fmtInput(el){el.value=el.value.replace(/[^\\d]/g,'');if(el.value==='')return;el.value=fmtRp(parseInt(el.value));}"
assert old in k
k = k.replace(old, old + "\nfunction setTxt(id,v){var e=document.getElementById(id);if(e)e.textContent=v;}", 1)

# 2) render aman (tidak crash walau elemen hilang)
k = k.replace("document.getElementById('total').textContent=fmtRp(T);", "setTxt('total',fmtRp(T));", 1)
k = k.replace("document.getElementById('total2').textContent=fmtRp(T);", "setTxt('total2',fmtRp(T));", 1)
k = k.replace("document.getElementById('total3').textContent=fmtRp(T);", "setTxt('total3',fmtRp(T));", 1)

# 3) sukses = langsung ke struk (sebelum apa pun)
old2 = "if(d.ok){cart=[];T=0;document.getElementById('diskon_all').value='0';render();document.getElementById('modalBayar').style.display='none';window.location.href='/struk/'+d.id;}"
new2 = "if(d.ok){document.getElementById('modalBayar').style.display='none';window.location.href='/struk/'+d.id;}"
assert old2 in k
k = k.replace(old2, new2, 1)
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("redirect struk aman ok")
