from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

s = s.replace(
'''    L.append("--------------------------------")

    L.append("No : " + (t.kode_trx or ("TRX-" + str(t.id))))
    L.append("Waktu : " + t.dibuat.strftime("%d/%m/%Y %H:%M"))

    L.append("--------------------------------")
    L.append("DETAIL PEMBELIAN")
    L.append("")
''',
'''    L.append("")

    L.append("No : " + (t.kode_trx or ("TRX-" + str(t.id))))
    L.append("Waktu : " + t.dibuat.strftime("%d/%m/%Y %H:%M"))

    L.append("")
    L.append("Detail Pembelian")
    L.append("")
'''
)

s = s.replace(
'''        L.append(
            str(it["jumlah"]) +
            " x " +
            rp0(it.get("harga") or 0)
            +
            " = " +
            rp0((it.get("harga") or 0) * it["jumlah"])
        )
        L.append("")
    
    L.append("--------------------------------")
    L.append("TOTAL   : " + rp0(t.total or 0))
    L.append("BAYAR   : " + rp0(t.bayar or 0))
    L.append("KEMBALI : " + rp0(t.kembalian or 0))
    L.append("")
    L.append("Metode : " + (t.metode or "TUNAI"))

    L.append("--------------------------------")
    L.append("")
    L.append("TERIMA KASIH ??")
    L.append("")
    L.append("Simpan struk ini sebagai")
    L.append("bukti pembayaran yang sah.")
''',
'''        L.append(
            str(it["jumlah"]) +
            " x " +
            rp0(it.get("harga") or 0)
            +
            " = " +
            rp0((it.get("harga") or 0) * it["jumlah"])
        )
        L.append("")

    L.append("Total : " + rp0(t.total or 0))
    L.append("Bayar : " + rp0(t.bayar or 0))
    L.append("Kembali : " + rp0(t.kembalian or 0))
    L.append("")
    L.append("Metode : " + (t.metode or "TUNAI"))

    L.append("")
    L.append("Terima Kasih ??")
    L.append("")
    L.append("Simpan struk ini sebagai")
    L.append("bukti pembayaran yang sah.")
    L.append("")
    L.append("Refill Perfumery")
'''
)

p.write_text(s,encoding="utf-8")
print("OK format WA lebih natural")
