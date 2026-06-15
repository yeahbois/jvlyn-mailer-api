# JVLYN Ticketing Mailer API (Sistem Antrean Asinkron)

API ini dibangun menggunakan FastAPI dan Python untuk menangani pembuatan tiket secara otomatis dan pengiriman email massal menggunakan sistem antrean (Cron Job). Arsitektur ini dioptimalkan untuk **Vercel Hobby (Gratis)**.

## Alur Kerja Sistem

### 1. Sisi Website & Backend PHP (Hostinger)
Saat ada peserta yang mengisi formulir pendaftaran:
*   **Langkah A**: PHP memvalidasi input dan melakukan `INSERT` ke tabel `orders`.
*   **Langkah B**: PHP mengambil ID pesanan (`LAST_INSERT_ID()`) dan melakukan `INSERT` ke tabel `jvlyn_tickets` untuk setiap tiket yang dibeli. Kolom `ticket_status` akan berisi nilai default `'pending_delivery'`.
*   **Langkah C**: PHP langsung menampilkan pesan sukses ke user. Proses ini instan (< 0.1 detik).

### 2. Sisi Integrasi Database
Data tiket mengantre di MySQL Hostinger dengan status `pending_delivery`.

### 3. Sisi API Python FastAPI (Vercel Cron Job)
Setiap 1-2 menit sekali, Vercel Cron memicu endpoint `/api/cron/process-tickets`.
*   **Ambil Antrean**: Python mengambil maksimal 2 pesanan (`LIMIT 2`) yang memiliki tiket `pending_delivery`.
*   **Rotasi Mailbox**: Python memilih mailbox yang kuotanya masih tersedia (< 100 email/hari) dari tabel `mailbox_counters`.
*   **Manipulasi Gambar**:
    *   Membaca template `assets/ticket_template.jpg`.
    *   Membuat QR Code berdasarkan `ticket_id`.
    *   Menempelkan QR, Nama, ID Tiket, dan Tipe Tiket menggunakan **Pillow** (dengan font Roboto Bold).
    *   Menyimpan gambar sementara di folder `/tmp/`.
*   **Kirim Email**: Python mengirimkan **satu email** berisi semua tiket pesanan tersebut sebagai lampiran (multi-attachments).
*   **Update Status**: Setelah sukses, `ticket_status` diubah menjadi `'sent'` dan counter mailbox ditambah (+1).

---

## Persiapan & Instalasi

### 1. Database MySQL (Hostinger)
Jalankan perintah SQL di file `init_db.sql` untuk membuat tabel:
*   `orders`: Menyimpan data utama pemesan.
*   `jvlyn_tickets`: Menyimpan data tiap tiket dan status pengirimannya.
*   `mailbox_counters`: Mengelola kuota 10 mailbox.

### 2. Aset Gambar & Font
*   Letakkan template tiket di `assets/ticket_template.jpg`.
*   Font `Roboto-Bold.ttf` sudah disertakan di folder `assets/`.

### 3. Konfigurasi Environment (.env)
Buat file `.env` (berdasarkan `.env.example`) dan isi:
*   `DB_*`: Kredensial database MySQL Hostinger (pastikan remote access diizinkan).
*   `MAIL_*`: Kredensial SMTP Hostinger.
*   `API_KEY`: Token rahasia untuk keamanan endpoint cron.

### 4. Deployment di Vercel
*   Pastikan variabel lingkungan sudah diatur di Dashboard Vercel.
*   `vercel.json` sudah dikonfigurasi untuk menjalankan cron job secara otomatis.

---

## Keunggulan
*   **Cepat & Ringan**: Backend PHP tidak terbebani proses berat.
*   **Profesional**: User menerima semua tiket dalam satu email yang rapi.
*   **Gratis & Stabil**: Berjalan sempurna di Vercel Tier Gratis tanpa terkena limit timeout.
