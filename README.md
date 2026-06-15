# JVLYN Ticketing Mailer API (Cron System)

API ini dibangun menggunakan FastAPI dan Python untuk menangani pembuatan tiket secara otomatis menggunakan sistem antrean (Cron Job). Arsitektur ini dirancang untuk berjalan secara efisien pada **Vercel Hobby (Gratis)** dan memberikan pengalaman pengguna yang profesional dengan mengirimkan satu email untuk semua tiket dalam satu pesanan.

## Arsitektur Sistem

1.  **PHP Hostinger (Frontend/Backend)**:
    *   Menyimpan data pesanan ke tabel `orders`.
    *   Menyimpan data tiket ke tabel `jvlyn_tickets` dengan `ticket_status = 'pending_delivery'`.
    *   **Tidak perlu** memanggil API Vercel secara langsung.
2.  **Vercel Cron Job**:
    *   Berjalan setiap 2 menit (dikonfigurasi via `vercel.json`).
    *   Memanggil endpoint `/api/cron/process-tickets`.
3.  **FastAPI (Vercel)**:
    *   Mengambil maksimal 2 pesanan yang memiliki tiket `pending_delivery`.
    *   Membuat gambar tiket (Pillow + QR Code) di folder `/tmp`.
    *   Mengirimkan **satu email** berisi semua tiket pesanan tersebut sebagai lampiran.
    *   Mengupdate status tiket menjadi `sent` dan mencatat penggunaan mailbox.

## Setup & Instalasi

1.  **Clone repositori**
2.  **Install dependensi**: `pip install -r requirements.txt`
3.  **Konfigurasi Environment**:
    *   Salin `.env.example` menjadi `.env`.
    *   Isi kredensial database MySQL Hostinger.
    *   Isi kredensial SMTP Hostinger.
    *   `API_KEY`: Gunakan sebagai token rahasia (untuk otentikasi cron).
4.  **Inisialisasi Database**: Jalankan `init_db.sql` di MySQL Hostinger.
5.  **Aset**: Letakkan template tiket di `assets/ticket_template.jpg`. Font otomatis diunduh saat build (Roboto Condensed).

## Endpoint Cron

**URL**: `/api/cron/process-tickets`
*   **Otentikasi**: Memerlukan header `X-Vercel-Cron` (otomatis dari Vercel) atau `X-API-KEY`.

## Keunggulan Strategi B (Cron)
*   **Anti-Timeout**: Memproses dalam batch kecil (2 pesanan per run) agar selesai < 10 detik.
*   **User Friendly**: Pembeli menerima 1 email meskipun membeli banyak tiket.
*   **Reliable**: Jika email gagal dikirim, status tetap `pending_delivery` dan akan dicoba lagi pada jadwal cron berikutnya.

## Deployment
Deploy ke Vercel seperti biasa. Pastikan variabel lingkungan (Environment Variables) sudah diatur di dashboard Vercel.
