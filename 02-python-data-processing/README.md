# ETL Pipeline: CSV ke PostgreSQL

## Gambaran Umum

Proyek ini mengimplementasikan ETL (*Extract, Transform, Load*) pipeline menggunakan Python untuk memproses data pesanan e-commerce dari file CSV ke database PostgreSQL.

Pipeline menggunakan Pandas untuk transformasi dan validasi data, SQLAlchemy untuk interaksi dengan database, serta pytest untuk pengujian otomatis.

Proyek ini mendemonstrasikan praktik dasar Data Engineering, meliputi validasi data, penegakan schema, transactional loading, logging, konfigurasi berbasis environment variables, dan automated testing.

## Arsitektur Pipeline

```text
CSV Source
    |
    v
Extract
- Membaca file CSV
- Memvalidasi header dan struktur kolom
    |
    v
Transform
- Normalisasi kolom teks
- Validasi tanggal dan nilai numerik
- Menolak data tidak valid dan order_id duplikat
- Mengurutkan data
    |
    v
Load
- Memvalidasi schema dan constraint PostgreSQL
- Mengganti data target dalam satu transaksi
- Memverifikasi jumlah baris yang dimuat
    |
    v
PostgreSQL
```

## Teknologi yang Digunakan

- **Python 3.10** - bahasa pemrograman untuk implementasi ETL.
- **Pandas** - membaca, mentransformasi, dan memvalidasi data tabular.
- **PostgreSQL** - database relasional sebagai target penyimpanan.
- **SQLAlchemy** - koneksi dan interaksi dengan PostgreSQL.
- **psycopg2** - PostgreSQL driver untuk Python.
- **python-dotenv** - memuat konfigurasi dari file `.env`.
- **pytest** - menjalankan unit test dan integration test.

## Struktur Proyek

```text
02-python-data-processing/
├── data/
│   └── raw/
│       └── orders.csv
├── tests/
│   ├── test_load_to_db.py
│   └── test_load_integration.py
├── .env.example
├── .gitignore
├── load_to_db.py
├── requirements.txt
└── README.md
```

## Dataset

Proyek menggunakan dataset contoh pesanan e-commerce yang disimpan di `data/raw/orders.csv`.

| Kolom | Deskripsi |
|---|---|
| `order_id` | ID unik pesanan |
| `order_date` | Tanggal pesanan dengan format `YYYY-MM-DD` |
| `customer_id` | ID pelanggan |
| `product` | Nama produk |
| `category` | Kategori produk |
| `quantity` | Jumlah unit yang dipesan |
| `unit_price` | Harga per unit |

Dataset berisi 20 baris data dan digunakan untuk demonstrasi serta pembelajaran. Dataset ini tidak dimaksudkan untuk merepresentasikan workload produksi.

## Data Quality dan Validasi

Sebelum data dimuat ke PostgreSQL, pipeline menerapkan aturan validasi berikut:

- CSV harus memiliki kolom yang sesuai dengan schema yang diharapkan, tanpa nama kolom duplikat atau kolom tambahan yang tidak dikenal.
- Kolom teks wajib tidak boleh kosong atau hanya berisi whitespace.
- `order_date` harus menggunakan format `YYYY-MM-DD` dan merupakan tanggal kalender yang valid.
- Kolom integer harus berisi nilai integer valid dan berada dalam rentang yang didukung tipe data database.
- `order_id` harus positif dan unik.
- `quantity` harus lebih besar dari nol.
- `unit_price` tidak boleh negatif.

Database juga menerapkan constraint untuk menjaga integritas data, termasuk primary key dan `CHECK` constraints.

## Strategi Loading

Pipeline menggunakan strategi **transactional full refresh**. Setiap eksekusi yang berhasil mengganti seluruh isi tabel target dengan data dari CSV.

Tahap loading:

1. Memvalidasi data hasil transformasi.
2. Memastikan schema dan constraint tabel target sesuai.
3. Menghapus data lama menggunakan `DELETE`.
4. Memasukkan data baru menggunakan `INSERT`.
5. Memverifikasi jumlah baris setelah proses loading.
6. Melakukan `COMMIT` hanya jika seluruh proses berhasil.

Operasi penghapusan dan pemasukan data dilakukan dalam satu transaksi database. Jika proses loading gagal, transaksi akan mengalami `ROLLBACK`, sehingga data sebelumnya tetap terjaga.

Strategi ini sesuai untuk demonstrasi batch ETL berukuran kecil. Untuk kebutuhan yang lebih besar atau lebih kompleks, pendekatan seperti incremental loading dan upsert dapat dipertimbangkan.

## Persyaratan

Sebelum menjalankan proyek, siapkan:

- Python 3.10
- PostgreSQL
- Git

## Instalasi dan Konfigurasi

Seluruh perintah berikut dijalankan dari direktori `02-python-data-processing` menggunakan PowerShell.

### 1. Membuat dan mengaktifkan virtual environment

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Menginstal dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Menyiapkan konfigurasi database

Salin template konfigurasi:

```powershell
Copy-Item .env.example .env
```

Sesuaikan isi `.env` dengan konfigurasi PostgreSQL lokal:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecommerce_etl
DB_USER=postgres
DB_PASSWORD=password_postgresql_lokal
```

Ganti nilai `DB_PASSWORD` dengan password PostgreSQL lokal milikmu.

### 4. Membuat database

Pastikan database yang disebutkan pada `DB_NAME` sudah tersedia di PostgreSQL.

Jika database belum ada, buat menggunakan `psql`:

```sql
CREATE DATABASE ecommerce_etl;
```

Jalankan perintah tersebut hanya jika database belum tersedia.

## Menjalankan ETL Pipeline

Dari direktori proyek, jalankan:

```powershell
python load_to_db.py
```

Pipeline akan mencatat status proses Extract, Transform, Load, dan penyelesaian pipeline melalui logging.

Jika terjadi kegagalan, error akan dicatat dan program keluar dengan status non-zero.

Nama tabel target adalah `orders`.

**Perhatian:** setiap eksekusi yang berhasil akan mengganti seluruh data dalam tabel `orders` dengan isi CSV saat itu. Gunakan database development khusus ketika melakukan eksperimen.

## Pengujian

### Menjalankan unit test

```powershell
python -m pytest -v tests/test_load_to_db.py
```

Unit test mencakup validasi transformasi, format tanggal, nilai numerik, duplikasi ID pesanan, kolom wajib, dan nilai teks kosong.

### Menjalankan PostgreSQL integration test

Integration test menguji apakah data lama tetap terjaga ketika proses insert sengaja dibuat gagal. Tes ini membutuhkan koneksi PostgreSQL yang benar dan database `ecommerce_etl` dengan tabel `orders` yang sudah berisi data.

Aktifkan tes secara eksplisit melalui PowerShell:

```powershell
$env:RUN_DB_TESTS = "1"
python -m pytest -v tests/test_load_integration.py
Remove-Item Env:RUN_DB_TESTS
```

Jalankan integration test hanya pada database development khusus yang sesuai dengan konfigurasi di atas.

### Menjalankan seluruh test suite

```powershell
python -m pytest -v
```

Secara default, PostgreSQL integration test akan dilewati kecuali environment variable `RUN_DB_TESTS=1` ditetapkan.

## Hasil Validasi Dataset Contoh

Hasil query agregasi setelah pipeline dijalankan pada dataset yang disertakan:

| Metrik | Hasil |
|---|---:|
| Total baris | 20 |
| Order ID unik | 20 |
| Total kuantitas | 29 |
| Gross sales | 12.675.000 |

`Gross sales` dihitung menggunakan `SUM(quantity * unit_price)`. Dataset sumber tidak mencantumkan metadata mata uang, sehingga nilai tersebut ditampilkan dalam satuan harga pada dataset dan tidak diasumsikan sebagai mata uang tertentu.

## Tujuan Pembelajaran

Proyek ini dibuat sebagai bagian dari portofolio Data Engineering untuk mempraktikkan ETL menggunakan Python, validasi data, integrasi PostgreSQL, transactional loading, dan automated testing.