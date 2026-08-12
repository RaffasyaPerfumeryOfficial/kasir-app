import io
k = io.open("templates/kasir.html", encoding="utf-8").read()

# 1) tambah kolom Harga di header
old_h = '<tr><th>Nama</th><th>Qty</th><th>Diskon</th><th>Subtotal</th><th></th></tr>'
new_h = '<tr><th>Nama</th><th>Harga</th><th>Qty</th><th>Diskon</th><th>Subtotal</th><th></th></tr>'
assert old_h in k, "header tidak ketemu"
k = k.replace(old_h, new_h, 1)

# 2) baris keranjang: tampilkan harga + subtotal jadi input
old_row = r'''tr.innerHTML='<td>'+i.nama+'</td>'+
'<td><input type="number" min="1" value="'+i.jumlah+'" style="width:60px;margin:0" onclick="this.value=\'\'" onchange="setQty('+i.id+',this.value)"></td>'+
'<td><input type="text" inputmode="numeric" value="'+fmtRp(i.diskon||0)+'" style="width:90px;margin:0" oninput="fmtInput(this)" onchange="setDiskon('+i.id+',this.value)"></td>'+
'<td>'+fmtRp(sub)+'</td>'+
'<td><button class="btn-danger" onclick="hapus('+i.id+')">x</button></td>';'''
new_row = r'''tr.innerHTML='<td>'+i.nama+'</td>'+
'<td>'+fmtRp(i.harga)+'</td>'+
'<td><input type="number" step="0.5" min="0.5" value="'+i.jumlah+'" style="width:70px;margin:0" onclick="this.value=\'\'" onchange="setQty('+i.id+',this.value)"></td>'+
'<td><input type="text" inputmode="numeric" value="'+fmtRp(i.diskon||0)+'" style="width:90px;margin:0" oninput="fmtInput(this)" onchange="setDiskon('+i.id+',this.value)"></td>'+
'<td><input type="text" inputmode="numeric" value="'+fmtRp(sub)+'" style="width:100px;margin:0" oninput="fmtInput(this)" onchange="setSub('+i.id+',this.value)"></td>'+
'<td><button class="btn-danger" onclick="hapus('+i.id+')">x</button></td>';'''
assert old_row in k, "baris keranjang tidak ketemu"
k = k.replace(old_row, new_row, 1)

# 3) setQty desimal + pembulatan + setSub
old_setqty = """function setQty(id,v){
let it=cart.find(i=>i.id===id);
if(it){it.jumlah=Math.max(1,parseInt(v)||1);}
render();
}"""
new_setqty = """function roundQty(q){
if(!(q>0))return 0.5;
var w=Math.floor(q);var f=q-w;
if(f<0.001)return w;
if(f<=0.5)return w+0.5;
return w+1;
}
function setQty(id,v){
let it=cart.find(i=>i.id===id);
if(it){it.jumlah=roundQty(parseFloat(String(v).replace(',','.'))||1);}
render();
}
function setSub(id,v){
let it=cart.find(i=>i.id===id);
if(it&&it.harga>0){
var s=Math.max(0,parseInt(String(v).replace(/[^\\d]/g,''))||0);
it.jumlah=roundQty(s/it.harga);
}
render();
}"""
assert old_setqty in k, "setQty tidak ketemu"
k = k.replace(old_setqty, new_setqty, 1)
io.open("templates/kasir.html", "w", encoding="utf-8").write(k)
print("keranjang harga + subtotal ok")
