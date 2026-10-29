# Audit Awal dan Rencana Pengembangan — Kasir App

Tanggal audit: 2026-10-29  
Branch kerja: `work/supabase-multicabang-audit`  
Branch produksi yang dilindungi: `main`

## Tujuan

Mengembangkan aplikasi bertahap tanpa mengubah branch `main`, menghapus data, atau menimpa database yang ada. Migrasi database harus diuji pada salinan terlebih dahulu.

## Temuan awal dari kode

1. Aplikasi memakai Python, FastAPI, SQLAlchemy, Jinja2, dan HTML.
2. `app/db.py` menunjuk ke SQLite lokal: `sqlite:///./kasir.db`. Database bergantung pada lokasi kerja aplikasi dan tidak otomatis terlindungi jika komputer atau folder rusak.
3. `app/models.py` memuat model produk, transaksi, pengeluaran, tutup kasir, sesi, stok masuk, rekap, anggota, poin, dan pemasukan.
4. Model produk dan transaksi yang diperiksa belum memiliki relasi cabang. Multi-cabang perlu dirancang dengan inventaris per cabang dan transaksi yang menyimpan identitas cabang.
5. `backup_db.py` kosong, tetapi fungsi backup/restore memang ada di `app/main.py`. Backup otomatis memakai `shutil.copy2("kasir.db", tujuan)`, membuat log lokal, dan dipanggil pada beberapa alur tertentu. Jadi, backup bukan sepenuhnya belum ada; yang belum terbukti adalah konsistensi backup, cakupan pemicu, backup di luar komputer, dan keberhasilan restore.
6. Backup berupa penyalinan file SQLite langsung ketika aplikasi mungkin sedang berjalan berisiko menghasilkan salinan yang tidak konsisten, bergantung pada konfigurasi SQLite/WAL dan aktivitas transaksi. Perlu diganti atau diverifikasi dengan SQLite backup API.
7. Endpoint `POST /restore` menerima parameter nama/path file dan menyalinnya ke `kasir.db`. Path harus dibatasi hanya ke file backup yang tervalidasi di direktori backup. Restore wajib membuat backup sebelum restore, memvalidasi file, dan diuji pada database uji—bukan langsung pada database aktif.
8. `app/main.py` memiliki kredensial login tertulis langsung di kode (`USERS`) dan cookie sesi dibuat tanpa atribut keamanan eksplisit. Pindahkan rahasia ke environment variables, ganti kredensial yang pernah terekspos, dan perketat cookie sebelum aplikasi diakses publik.
9. `jalan.bat` menjalankan ngrok dan Uvicorn serta menjalankan `git pull` dalam siklus restart. Alur ini berisiko mengambil perubahan kode tanpa proses rilis dan pengujian terkontrol.
10. `.gitignore` mengabaikan file `*.db` dan `backup/`. Ini membantu mencegah data lokal masuk Git, tetapi berarti file database/backup lokal tidak bisa dipulihkan dari repository saja jika hilang.
11. Ada skrip `insert_branch.py` dan `produk_branch.py`; keberadaannya saja tidak membuktikan multi-cabang aktif. Perlu ditinjau sebagai skrip modifikasi kode terpisah dan tidak dijalankan otomatis pada database atau kode produksi.

## Rencana kerja bertahap

### Tahap 0 — Pengamanan dan baseline
- Jangan commit ke `main`; gunakan branch kerja terpisah.
- Catat versi kode dan audit tanpa menyentuh database produksi.
- Periksa apakah file database dan backup masih ada di komputer pengguna. Jangan menjalankan restore otomatis atau menimpa file.
- Buat salinan lokal terpisah sebelum eksperimen runtime.

### Tahap 1 — Backup dan pemulihan
- Ganti penyalinan file mentah dengan mekanisme backup SQLite yang konsisten, misalnya SQLite backup API.
- Simpan backup di luar folder aplikasi dan sediakan salinan kedua di penyimpanan cloud dengan akses terbatas.
- Gunakan nama bertanggal, log hasil backup, retensi, dan penanganan kegagalan.
- Batasi restore ke file backup yang tervalidasi dalam direktori backup; tolak path arbitrer.
- Uji pemulihan ke file database uji yang berbeda. Jangan restore langsung ke database aktif.
- Jangan menganggap backup berhasil sebelum uji restore berhasil.

### Tahap 2 — Supabase/PostgreSQL untuk uji coba
- Buat proyek Supabase terpisah untuk pengembangan, bukan database produksi.
- Simpan URL dan password database di environment variables yang tidak di-commit.
- Sesuaikan konfigurasi SQLAlchemy untuk PostgreSQL dan buat migrasi skema eksplisit.
- Jangan menjalankan migrasi yang menghapus/menimpa tabel. Pertahankan SQLite asli sebagai sumber yang tidak disentuh.
- Uji produk, transaksi, stok, omzet, riwayat, tutup kasir, dan ekspor dengan data contoh terlebih dahulu.
- Migrasi data historis hanya setelah pemetaan kolom dan rekonsiliasi jumlah record disepakati.

### Tahap 3 — Multi-cabang
- Tambahkan tabel cabang dan pemetaan pengguna ke cabang.
- Rancang stok per cabang serta transaksi, pengeluaran, dan penutupan kasir yang terikat pada cabang.
- Tentukan apakah katalog dan harga produk dibagi bersama atau dapat berbeda antar cabang.
- Batasi akses cabang di sisi server, bukan hanya dengan menyembunyikan pilihan di antarmuka.
- Uji agar cabang A tidak dapat melihat atau mengubah stok/transaksi cabang B tanpa izin.

### Tahap 4 — Keamanan dan operasional
- Pindahkan kredensial dari source code ke environment variables; ganti kredensial lama jika pernah terekspos.
- Atur cookie sesi dengan HttpOnly, SameSite, dan Secure saat HTTPS; tinjau proteksi aksi yang mengubah data.
- Tinjau penggunaan ngrok dan hindari `git pull` otomatis sebagai mekanisme deployment produksi.
- Jangan menghapus executable atau skrip lama sebelum memastikan tidak dibutuhkan dan mendapat persetujuan.

### Tahap 5 — Pengujian dan rilis
- Jalankan tes regresi untuk transaksi, void, stok, tutup kasir, ekspor, dan laporan.
- Uji skenario koneksi internet terputus dan kegagalan database.
- Buat pull request dari branch kerja ke `main` hanya setelah perubahan ditinjau dan tes lulus.
- Jangan merge atau deploy tanpa persetujuan pemilik aplikasi.

## Kriteria penerimaan

- Branch `main` tidak diubah oleh pekerjaan pengembangan ini.
- Data produksi tidak dihapus, ditimpa, atau dimigrasikan tanpa backup terverifikasi dan persetujuan.
- Backup dapat dipulihkan ke database uji.
- Data transaksi dan stok terisolasi per cabang.
- Rahasia tidak disimpan dalam repository.
- Hasil tes dan langkah rollback terdokumentasi.

## Batas audit ini

Audit ini berdasarkan file dan metadata repository. Belum ada akses ke database lokal pengguna dan belum ada pengujian runtime. Kondisi backup pada komputer pengguna dan keberhasilan restore belum diverifikasi. Temuan tambahan harus dikonfirmasi sebelum implementasi.
