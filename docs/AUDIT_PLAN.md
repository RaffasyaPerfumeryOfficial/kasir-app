# Audit Awal dan Rencana Pengembangan — Kasir App

Tanggal audit: 2026-10-29  
Branch kerja: `work/supabase-multicabang-audit`  
Branch produksi yang dilindungi: `main`

## Tujuan

Mengembangkan aplikasi secara bertahap tanpa mengubah branch `main`, menghapus data, atau menimpa database yang ada. Semua migrasi database harus diuji pada salinan terlebih dahulu.

## Temuan awal dari kode

1. Aplikasi memakai Python, FastAPI, SQLAlchemy, Jinja2, dan HTML.
2. `app/db.py` menunjuk ke SQLite lokal dengan URL `sqlite:///./kasir.db`. Database ini bergantung pada lokasi kerja aplikasi dan tidak otomatis terlindungi jika komputer/folder rusak.
3. `app/models.py` memuat tabel produk, transaksi, pengeluaran, tutup kasir, sesi, stok masuk, rekap, anggota, poin, dan pemasukan.
4. Model produk dan transaksi yang diperiksa belum menunjukkan relasi cabang. Penerapan multi-cabang perlu dirancang dengan inventaris per cabang serta transaksi yang menyimpan identitas cabang.
5. `backup_db.py` pada branch `main` kosong. Riwayat commit menyebut fitur backup/restore di masa lalu, sehingga implementasi aktual perlu dilacak pada file lain sebelum menulis ulang.
6. `app/main.py` memiliki kredensial login yang ditulis langsung di kode (`USERS`) dan sesi disimpan di database. Ini perlu dipindahkan ke konfigurasi environment dan cookie sesi diperketat sebelum aplikasi diakses publik.
7. `jalan.bat` menjalankan ngrok dan Uvicorn serta melakukan `git pull` saat aplikasi dimulai ulang. Alur deployment ini harus ditinjau agar perubahan kode tidak otomatis masuk ke mesin kasir tanpa pengujian.
8. `.gitignore` mengabaikan file `*.db`, tetapi tidak menggantikan backup di luar komputer. Berkas database lokal yang tidak terlacak di Git tidak bisa dipulihkan dari repository saja.

## Rencana kerja bertahap

### Tahap 0 — Pengamanan dan baseline
- Jangan melakukan commit ke `main`.
- Pertahankan branch kerja terpisah ini.
- Catat versi kode dan jalankan audit tanpa menyentuh database produksi.
- Periksa apakah ada file database, backup, dan data lokal yang masih tersedia; jangan menimpa atau menjalankan restore otomatis.

### Tahap 1 — Backup dan pemulihan
- Implementasikan backup SQLite yang konsisten (gunakan SQLite backup API atau mekanisme aman ketika aplikasi berhenti/terkunci).
- Simpan backup di lokasi terpisah dari folder aplikasi dan sediakan salinan kedua di penyimpanan cloud yang aksesnya dibatasi.
- Gunakan nama berstempel waktu, log hasil backup, dan retensi yang ditetapkan.
- Uji pemulihan ke file database uji yang berbeda; jangan restore langsung ke database aktif.
- Jangan menganggap backup berhasil sampai uji restore berhasil.

### Tahap 2 — Supabase/PostgreSQL untuk uji coba
- Buat proyek Supabase terpisah untuk pengembangan; jangan menggunakan database produksi pada uji pertama.
- Simpan URL dan password database dalam environment variables lokal yang tidak di-commit.
- Sesuaikan konfigurasi koneksi SQLAlchemy secara kompatibel dengan PostgreSQL.
- Buat skema dan migrasi yang eksplisit. Jangan menjalankan migrasi otomatis yang menghapus/menimpa tabel.
- Uji produk, transaksi, perhitungan stok, laporan omzet, dan riwayat pada data contoh.

### Tahap 3 — Multi-cabang
- Tambahkan tabel cabang dan pemetaan pengguna ke cabang.
- Rancang stok per cabang, serta transaksi, pengeluaran, dan penutupan kasir yang terikat ke cabang.
- Tetapkan apakah katalog/harga produk dibagi bersama atau dapat berbeda antar cabang.
- Batasi akses berdasarkan cabang di sisi server, bukan hanya menyembunyikan pilihan cabang di antarmuka.
- Buat uji agar cabang A tidak dapat melihat/mengubah stok atau transaksi cabang B tanpa izin.

### Tahap 4 — Keamanan dan operasional
- Pindahkan kredensial dari source code ke environment variables; ganti kredensial yang pernah digunakan jika aplikasi pernah terekspos.
- Tambahkan atribut cookie sesi yang sesuai (HttpOnly, SameSite, dan Secure saat HTTPS), validasi sesi, serta proteksi aksi yang mengubah data.
- Tinjau penggunaan ngrok dan hindari `git pull` otomatis sebagai mekanisme deployment produksi.
- Hapus executable besar dari alur pengembangan hanya setelah memastikan tidak dibutuhkan, dan jangan menghapusnya tanpa persetujuan.

### Tahap 5 — Pengujian dan rilis
- Jalankan tes regresi untuk transaksi, void, stok, tutup kasir, ekspor, dan laporan.
- Uji skenario koneksi internet terputus dan kegagalan database.
- Buat pull request dari branch kerja ke `main` hanya setelah perubahan ditinjau dan tes lulus.
- Jangan merge atau deploy otomatis tanpa persetujuan pemilik aplikasi.

## Kriteria penerimaan

- Branch `main` tidak diubah oleh pekerjaan audit ini.
- Data produksi tidak dihapus, ditimpa, atau dimigrasikan tanpa backup terverifikasi dan persetujuan.
- Backup dapat dipulihkan ke database uji.
- Data transaksi dan stok terisolasi per cabang.
- Rahasia tidak disimpan dalam repository.
- Hasil tes dan langkah rollback terdokumentasi.

## Batas audit ini

Ini adalah audit awal berdasarkan file dan metadata repository yang berhasil diperiksa. Belum ada koneksi ke database lokal pengguna, belum ada pengujian runtime, dan belum ada verifikasi backup yang tersedia di komputer pengguna. Temuan terkait file lain perlu dikonfirmasi sebelum perubahan implementasi.
