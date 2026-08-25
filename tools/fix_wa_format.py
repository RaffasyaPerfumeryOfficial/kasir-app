from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

start = s.index("def buat_teks_struk(db, t):")

new_func = r'''def buat_teks_struk(db, t):
    L = []

    L.append("MEKAR SARI")
    L.append("Refill Perfumery")
    L.append("Jl. Mekar Sari No.5, Bekasi Jaya")
    L.append("Kota Bekasi")
    L.append("HP: 0821-1897-1096")
    L.append("--------------------------------")

    L.append("No : " + (t.kode_trx or ("TRX-" + str(t.id))))
    L.append("Waktu : " + t.dibuat.strftime("%d/%m/%Y %H:%M"))
    L.append("--------------------------------")

    L.append("DETAIL PEMBELIAN")

    for it in json.loads(t.items):
        L.append(it["nama"])
        L.append(
            str(it["jumlah"]) +
            " x " +
            rp0(it.get("harga") or 0) +
            " = " +
            rp0((it.get("harga") or 0) * it["jumlah"])
        )

    L.append("--------------------------------")
    L.append("TOTAL : " + rp0(t.total or 0))

    if t.poin_dipakai:
        L.append("POTONG POIN : -" + rp0(t.poin_dipakai))
        L.append("BAYAR AKHIR : " + rp0((t.total or 0) - (t.poin_dipakai or 0)))

    metode = (t.metode or "TUNAI")
    metode = metode.replace("POIN + NON-TUNAI (", "")
    metode = metode.replace(")", "")

    L.append("METODE : " + metode)

    if "TUNAI" in metode.upper():
        L.append("BAYAR : " + rp0(t.bayar or 0))
        L.append("KEMBALI : " + rp0(t.kembalian or 0))

    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    if pl:
        ag = db.get(models.Anggota, pl.anggota_id)
        if ag:
            L.append("")
            if pl.poin < 0:
                L.append("POIN DIPAKAI : " + rp0(abs(pl.poin)))
            elif pl.poin > 0:
                L.append("POIN TAMBAH : +" + format(int(pl.poin), ",").replace(",", "."))

            L.append("SISA POIN : " + format(int(ag.poin or 0), ",").replace(",", "."))

    L.append("--------------------------------")
    L.append("TERIMA KASIH")
    L.append("Simpan struk ini sebagai")
    L.append("bukti pembayaran yang sah.")

    return "\n".join(L)
'''

s = s[:start] + new_func + "\n"

p.write_text(s, encoding="utf-8")

print("OK format WhatsApp dirapikan")
