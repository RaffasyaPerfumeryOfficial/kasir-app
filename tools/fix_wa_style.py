from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

start = s.index("def buat_teks_struk(db, t):")

end = s.index("\n\n", start)

baru = '''def buat_teks_struk(db, t):
    L = []

    L.append("?? *MEKAR SARI*")
    L.append("*Refill Perfumery*")
    L.append("Jl. Mekar Sari No.5, Bekasi Jaya")
    L.append("Kota Bekasi")
    L.append("")

    L.append("No : " + (t.kode_trx or ("TRX-" + str(t.id))))
    L.append("Waktu : " + t.dibuat.strftime("%d/%m/%Y %H:%M"))
    L.append("")

    L.append("*Detail Pembelian*")
    L.append("")

    for it in json.loads(t.items):
        L.append(it["nama"])
        L.append(
            str(it["jumlah"]) +
            " x " +
            rp0(it.get("harga") or 0) +
            " = " +
            rp0((it.get("harga") or 0) * it["jumlah"])
        )
        L.append("")

    L.append("*TOTAL : " + rp0(t.total or 0) + "*")
    L.append("Bayar : " + rp0(t.bayar or 0))
    L.append("Kembali : " + rp0(t.kembalian or 0))
    L.append("")
    L.append("Metode : " + (t.metode or "TUNAI"))

    L.append("")
    L.append("?? *TERIMA KASIH*")
    L.append("")
    L.append("Simpan struk ini sebagai")
    L.append("bukti pembayaran yang sah.")

    return "\\n".join(L)
'''

s = s[:start] + baru + s[end:]

p.write_text(s, encoding="utf-8")

print("OK WA format baru")
