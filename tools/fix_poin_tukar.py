from pathlib import Path

p = Path("app/main.py")
s = p.read_text(encoding="utf-8")

old = """        if bibit_total > 0 and poin == 0:
            earn = int(bibit_total * 0.05)
            ag.poin = (ag.poin or 0) + earn
            db.add(models.PoinLog(anggota_id=ag.id, trx_id=t.id, poin=earn))
"""

new = """        if bibit_total > 0 and not poin:
            earn = int(bibit_total * 0.05)
            ag.poin = (ag.poin or 0) + earn
            db.add(models.PoinLog(anggota_id=ag.id, trx_id=t.id, poin=earn))
"""

if old not in s:
    raise Exception("Bagian earn poin tidak ditemukan")

s = s.replace(old,new,1)

p.write_text(s,encoding="utf-8")

print("OK aturan poin diperbaiki")
