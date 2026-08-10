import io
m = io.open("app/main.py", encoding="utf-8").read()
i = m.find('return ("Omzet sinkron " + label')
assert i != -1, "blok omzet ai tidak ketemu"
j = m.find('\n', i)
new_block = '''            peng_list = [p for p in db.query(models.Pengeluaran).all() if p.dibuat and p.dibuat.date() == target]
            tot_peng = sum(p.jumlah or 0 for p in peng_list)
            tunai_bersih = tun - tot_peng
            out = ("Omzet sinkron " + label + " (" + target.strftime("%d/%m/%Y") + "):\\nomzet : " + rp(tot) + "\\nTUNAI : " + rp(tun) + "\\nNON-TUNAI : " + rp(non))
            if tot_peng > 0:
                out += "\\nPengeluaran : " + rp(tot_peng) + "\\nRINCIAN PENGELUARAN:"
                for p in peng_list:
                    out += "\\n- " + (p.keterangan or "Pengeluaran").upper() + " " + rp(p.jumlah or 0)
                out += "\\nTUNAI setelah pengeluaran : " + rp(tunai_bersih)
                out += "\\nNON-TUNAI tidak dipotong : " + rp(non)
            else:
                out += "\\nPengeluaran : tidak ada\\nTUNAI setelah pengeluaran : " + rp(tunai_bersih)
            out += "\\n\\n(Sinkron dengan Dashboard, Riwayat & Laporan)"
            return out'''
m = m[:i] + new_block + m[j:]
io.open("app/main.py", "w", encoding="utf-8").write(m)
print("ai omzet + pengeluaran ok")
