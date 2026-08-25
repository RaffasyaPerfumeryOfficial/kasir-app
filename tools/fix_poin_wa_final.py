from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = '''    L.append("Metode : " + metode)

    L.append("")
    L.append("")
    L.append("TERIMA KASIH")'''

new = '''    L.append("Metode : " + metode)

    pl = db.query(models.PoinLog).filter_by(trx_id=t.id).first()
    if pl:
        ag = db.get(models.Anggota, pl.anggota_id)
        if ag:
            L.append("")
            L.append("Anggota : " + ag.nama + " (" + ag.nomor_member + ")")
            if pl.poin < 0:
                L.append("Poin dipakai : " + rp0(abs(pl.poin)))
            elif pl.poin > 0:
                L.append("Poin tambah : +" + format(int(pl.poin), ",").replace(",", "."))
            L.append("Total poin : " + format(int(ag.poin or 0), ",").replace(",", "."))

    L.append("")
    L.append("")
    L.append("TERIMA KASIH")'''

if old not in s:
    raise Exception("Bagian metode WA tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK poin WhatsApp dirapikan")
