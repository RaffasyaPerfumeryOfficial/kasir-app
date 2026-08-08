import io
p = "app/models.py"
s = io.open(p, encoding="utf-8").read()
# Cari semua posisi "class RiwayatTutup"
positions = []
start = 0
while True:
    idx = s.find("class RiwayatTutup", start)
    if idx == -1:
        break
    positions.append(idx)
    start = idx + 1
print(f"Ditemukan {len(positions)} kali 'class RiwayatTutup'")
if len(positions) > 1:
    # Hapus dari posisi kedua sampai akhir file (atau sampai class berikutnya)
    # Cari akhir blok class kedua (baris kosong setelahnya atau class lain)
    second_pos = positions[1]
    # Cari "\n\n" atau "\nclass " setelah posisi kedua
    end_idx = s.find("\n\nclass ", second_pos)
    if end_idx == -1:
        end_idx = s.find("\nclass ", second_pos + 1)
    if end_idx == -1:
        end_idx = len(s)
    # Hapus dari second_pos sampai end_idx
    s_new = s[:second_pos] + s[end_idx:]
    io.open(p, "w", encoding="utf-8").write(s_new)
    print("✅ Duplikat dihapus")
else:
    print("ℹ️ Tidak ada duplikat")
