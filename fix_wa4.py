import io
m = io.open("app/main.py", encoding="utf-8").read()
if "def buat_teks_struk" not in m:
    m += '''

def rp0(x):
    return "Rp " + format(int(round(x)), ",").replace(",", ".")

def buat_teks_struk(db, t):
    L = []
    L.append("MEKAR SARI")
    L.append("Refill Perfumery")
    L.append("Jl. Mekar Sari No.5, Bekasi Jaya,")
    L.append("Kec. Bekasi Tim., Kota Bks, Jawa Barat 17112")
    L.append("HP: 0821-1897-1096")
    L.append("-----------------------------------------")
    L.append("No   : " + (t.kode_trx or ("TRX-" + str(t.id))))
    L.append("Waktu: " + t.dibuat.strftime("%d/%m/%Y %H:%M"))
    L.append("-----------------------------------------")
    for it in json.loads(t.items):
        L.append(it["nama"])
        L.append("  " + str(it["jumlah"]) + " x " + format(int(it.get("harga") or 0), ",").replace(",", ".") + " = " + format(int((it.get("harga") or 0) * it["jumlah"]), ",").replace(",", "."))
    L.append("-----------------------------------------")
    L.append("TOTAL  : " + rp0(t.total or 0))
    if t.total_diskon:
        L.append("Diskon : " + rp0(t.total_diskon))
    if t.poin_dipakai:
        L.append("POIN   : " + rp0(t.poin_dipakai))
    L.append("Bayar  : " + rp0(t.bayar or 0))
    L.append("Kembali: " + rp0(t.kembalian or 0))
    L.append("Metode : " + (t.metode or "TUNAI"))
    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    if pl:
        ag = db.get(models.Anggota, pl.anggota_id)
        if ag:
            L.append("-----------------------------------------")
            L.append("Anggota: " + ag.nama + " (" + ag.nomor_member + ")")
            L.append("Poin tambah: +" + format(int(pl.poin), ",").replace(",", "."))
            L.append("Poin total : " + format(int(ag.poin or 0), ",").replace(",", "."))
    L.append("-----------------------------------------")
    L.append("Terima kasih")
    L.append("Parfum Anda, cerita Anda.")
    return "\\n".join(L)
'''
    io.open("app/main.py", "w", encoding="utf-8").write(m)
    print("buat_teks_struk ditambahkan")
else:
    print("sudah ada")
