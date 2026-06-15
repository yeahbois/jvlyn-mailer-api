# JVLYN Ticketing Mailer API

API ini dibangun menggunakan FastAPI dan Python untuk menangani pembuatan tiket (image manipulation), QR Code, dan pengiriman email otomatis dengan sistem rotasi mailbox untuk menghindari limit harian.

## Arsitektur & Strategi "One Request, One Ticket"

Untuk mendukung **Vercel Hobby (Gratis)**, API ini menggunakan strategi pemrosesan sinkron. Hal ini dikarenakan Vercel Tier Gratis akan membekukan eksekusi segera setelah respons dikirim.

**Rekomendasi Implementasi di Backend PHP (Hostinger):**
Jangan mengirimkan seluruh data tiket dalam satu request jika jumlahnya banyak. Disarankan agar PHP melakukan looping dan memanggil API ini untuk **setiap tiket secara individual** (atau dalam kelompok kecil maksimal 2-3 tiket) agar tetap berada di bawah batas timeout 10 detik Vercel.

Contoh Alur:
1. User beli 3 tiket.
2. PHP simpan ke DB.
3. PHP memanggil API Vercel 3x berturut-turut (1 tiket per panggilan).
4. Vercel memproses 1 tiket, kirim email, lalu kirim balasan `success`.

## Setup & Instalasi

1. **Clone repositori**
2. **Install dependensi**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Konfigurasi Environment**:
   Salin `.env.example` menjadi `.env` dan isi dengan kredensial yang sesuai.
   - `API_KEY`: Token rahasia untuk autentikasi.
   - `DB_*`: Kredensial database MySQL.
   - `MAIL_*`: Kredensial SMTP Hostinger.

4. **Inisialisasi Database**:
   Jalankan query di file `init_db.sql` pada database MySQL Anda untuk membuat tabel `mailbox_counters` dan `jvlyn_tickets`.

5. **Aset**:
   Pastikan file `assets/ticket_template.jpg` tersedia sebagai template tiket.

## Penggunaan API

### Generate Tiket & Email
**Endpoint**: `POST /api/tickets/generate`
**Header**: `X-API-KEY: <your_api_key>`

**Body (JSON)**:
```json
{
  "order_id": 12345,
  "buyer_name": "NAMA PEMBELI",
  "notelp": "08123456789",
  "buyer_email": "email@pembeli.com",
  "tickets": [
    {
      "ticket_id": "JVLYNVIP001",
      "ticket_type": "VIP",
      "referral_code": "PROMO"
    }
  ]
}
```

## Cara Debugging

1. **Log Server**: Jika dijalankan secara lokal, periksa output terminal uvicorn.
2. **Unit Test**: Jalankan `python3 test_logic.py` (jika tersedia) untuk memverifikasi logika.
3. **Temporary Files**: API menggunakan `/tmp` untuk penyimpanan sementara gambar agar kompatibel dengan filesystem read-only Vercel.

## Deployment di Vercel
Pastikan file `main.py` dan `vercel.json` sudah benar. Endpoint akan otomatis terpetakan sebagai serverless function.
