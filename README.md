# JVLYN Ticketing Mailer API

API ini dibangun menggunakan FastAPI dan Python untuk menangani pembuatan tiket (image manipulation), QR Code, dan pengiriman email otomatis dengan sistem rotasi mailbox untuk menghindari limit harian.

## Arsitektur
1. **PHP Backend (Hostinger)** mengirim data pesanan ke API ini di Vercel.
2. **FastAPI (Vercel)** menerima data, memvalidasi API Key, dan merespons cepat (`queued`).
3. **Background Tasks** memproses pembuatan gambar tiket, mengupdate database MySQL, dan mengirim email.

## Setup & Instalasi

1. **Clone repositori**
2. **Install dependensi**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Konfigurasi Environment**:
   Salin `.env.example` menjadi `.env` dan isi dengan kredensial yang sesuai:
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
2. **Testing Script**: Gunakan `test_api.py` untuk menguji endpoint secara cepat.
3. **Unit Test**: Jalankan `python3 test_logic.py` untuk memverifikasi logika background processing tanpa memerlukan koneksi database/SMTP asli.
4. **Temporary Files**: Folder `temp_tickets` digunakan sementara untuk menyimpan gambar tiket sebelum dikirim, dan akan dihapus otomatis setelah email terkirim.

## Deployment di Vercel
Pastikan file `main.py` dapat diakses oleh Vercel. Anda mungkin perlu menambahkan file `vercel.json` jika diperlukan konfigurasi khusus.
