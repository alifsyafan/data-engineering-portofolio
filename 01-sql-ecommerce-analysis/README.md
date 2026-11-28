# E-Commerce Sales & Customer Analysis

Analisis data penjualan e-commerce perlengkapan olahraga (25 Jul 2013 – 24 Jul 2014) dengan **PostgreSQL, Python, dan Looker Studio**. Proyek ini menjawab empat pertanyaan bisnis dan, sama pentingnya, **membuktikan bahwa angkanya dapat dipercaya**: setiap angka utama dihitung minimal dua kali lewat jalur berbeda, dan setiap masalah data dicatat.

- **Dashboard:** [Buka di Looker Studio]https://datastudio.google.com/s/jMmLj3FNX8k · [Versi PDF](docs/dashboard.pdf)
- **Insight dan rekomendasi bisnis:** [insights.md](insights.md)
- **Catatan audit dan validasi:** [audit_log.md](audit_log.md)

## Masalah bisnis

Tim bisnis ingin menjawab empat pertanyaan:

1. Dari mana revenue datang (kategori, produk, departemen, waktu)?
2. Berapa banyak order yang benar-benar menjadi revenue?
3. Pelanggan seperti apa yang paling bernilai?
4. Seberapa dapat dipercaya angka-angka itu?

**Definisi kunci:** valid revenue = jumlah `order_item_subtotal` dari order berstatus `COMPLETE` atau `CLOSED`. Seluruh nilai uang dalam **USD**.

## Data

Sumber dataset: Materi pelatihan praktik Data Engineering di Udemy

| Tabel | Deskripsi | Jumlah Baris |
|---|---|---|
| `departments` | Departemen | 6 |
| `categories` | Kategori produk | 58 |
| `products` | Produk | 1.345 |
| `customers` | Pelanggan | 12.435 |
| `orders` | Order | 68.883 |
| `order_items` | Detail item per order | 172.198 |

**Relasi:** `departments → categories → products`, `customers → orders → order_items`, dan `products → order_items`.

## Pendekatan

```
PostgreSQL (6 tabel)
   │  1. Audit dan perbaiki 9 query SQL                    → queries/
   ▼
Python (pandas, SQLAlchemy)
   │  2. Investigasi 3 kasus bisnis + uji hipotesis        → notebooks/
   │  3. Bangun 3 data mart (CSV)                          → data/processed/
   ▼
Google Sheets → Looker Studio
      4. Dashboard 2 halaman                               → docs/
```

| Tahap | Apa yang dikerjakan | Hasil utama |
|---|---|---|
| 1. Audit query SQL | Memeriksa filter, pengelompokan, JOIN, dan urutan hasil pada 6 query pertama. Menambah 3 query lanjutan (Pareto, pertumbuhan MoM, segmentasi pelanggan) | Menemukan pengelompokan per nama yang menyatukan entitas berbeda dan JOIN yang menyaring order tanpa item |
| 2. Investigasi di Python | Audit order tanpa item, uji hipotesis `SUSPECTED_FRAUD` dan order tertunda. Distribusi nilai order | Tiga hipotesis tidak didukung data, 11.452 order tanpa item tersebar merata |
| 3. Data mart | Tiga tabel agregasi dengan granularitas jelas dan kamus data | Bebas penghitungan ganda saat difilter, total cocok sampai sen |
| 4. Dashboard | Dua halaman, empat KPI, grafik tren, kategori, departemen, status, segmen pelanggan | Seluruh angka dashboard cocok dengan SQL dan Python |

## Temuan utama

| Pertanyaan | Temuan |
|---|---|
| Total valid revenue | **15.012.982,48 USD** dari 25.266 order valid yang punya item. Rata-rata nilai order (AOV) 594,20 USD, median 559,94 USD |
| Dari mana revenue datang | **7 dari 33 kategori (21%) menghasilkan 82,64%** revenue, Fishing sendirian 20,13%. Sembilan produk ≈ 94,6%. Satu departemen (Fan Shop) 49,62% |
| Bagaimana tren | Revenue bulanan datar di kisaran **1,17 s.d. 1,38 juta USD** (11 bulan penuh), puncak November 2013. AOV stabil, jadi naik-turunnya ditentukan jumlah order |
| Berapa order yang menjadi revenue | Hanya **44,2%** order (30.455 dari 68.883) berstatus valid. Sebanyak 51,5% masih berjalan (nilai nominal ±17,85 juta USD, lebih besar dari valid revenue) dan 4,3% batal atau diduga fraud |
| Pelanggan bernilai | Pelanggan Repeat dan Loyal = **69,05% pelanggan tetapi 86,74% revenue**. Nilai per order sama di semua tingkat (±593 s.d. 595 USD), jadi perbedaannya ada pada **frekuensi belanja** |
| Apakah status order bisa dijelaskan | Dalam variabel yang diuji (nilai order, bulan, hari, pelanggan), status **tidak menunjukkan keterkaitan**. Hipotesis "fraud bernilai lebih besar" dan "order tertunda menumpuk di bulan tertentu" tidak didukung |
| Kualitas data | **11.452 order (16,63%) tidak punya item**, tersebar merata antar status dan bulan. Penyebab tidak dapat ditentukan dari database |

Pembacaan angka yang paling sering membingungkan: *Valid Orders* di dashboard (25.266) lebih kecil dari order berstatus valid (30.455) karena 5.189 order valid tidak punya item, dan *Valid Order Share* 43,99% memakai penyebut 57.431 order yang punya item (Query 04 memakai 68.883 order dan menghasilkan 44,21%). Rinciannya ada di [audit_log.md](audit_log.md).

## Rekomendasi

| # | Aksi | Dasar data | Metrik keberhasilan |
|---|---|---|---|
| 1 | Tuntaskan order `PENDING_PAYMENT` | 15.030 order (21,82%), nominal ±7,58 juta USD (±50% dari valid revenue), proporsi sama di semua bulan | Payment Completion Rate; jumlah dan nilai order pending lebih dari 30 hari; Valid Order Share (43,99% saat ini) |
| 2 | Dorong pelanggan Repeat menjadi Loyal | 5.664 pelanggan Repeat; pelanggan Loyal bernilai ±4,5 kali pelanggan sekali beli | % pelanggan dengan ≥4 order (16,82% saat ini); revenue per pelanggan |
| 3 | Kelola risiko konsentrasi | 9 produk ≈ 94,6% revenue; 7 kategori = 82,64% | Hari kehabisan stok pada 9 produk utama |
| 4 | Perbaiki kelengkapan data order | 16,63% order tanpa item | % order tanpa item; tersedianya riwayat status |

Aksi 1 dan 2 adalah hipotesis yang perlu diuji, bukan kepastian (lihat keterbatasan).

## Dashboard

- **Halaman 1, Sales & Category Overview:** Valid Revenue, Valid Orders, AOV, Valid Order Share; tren valid revenue bulanan (bulan parsial diberi catatan); Top 10 kategori; kontribusi per departemen.
- **Halaman 2, Order Status & Customer Retention:** distribusi status order beserta nilai nominalnya; segmentasi pelanggan (% pelanggan vs % revenue per tingkat); ringkasan insight dan keterbatasan.

Dashboard membaca tiga data mart, bukan tabel mentah. Alasannya: kecepatan, tidak ada penghitungan ganda (*fan-out*) saat orang memfilter, dan tidak ada data pribadi pelanggan. Kamus data dan aturan penjumlahan ada di [data/processed/README.md](data/processed/README.md).

## Keterbatasan

- **Satu tahun data dan satu potret status order, tanpa riwayat perubahan status.** Penyebab 55,8% order non-valid dan pola musiman tidak dapat disimpulkan.
- **11.452 order tanpa item.** Metrik berbasis order (Valid Orders, AOV, segmentasi pelanggan) memakai definisi "order yang punya item".
- **Pola tanpa keterkaitan antar variabel tidak lazim untuk data operasional nyata**, sehingga ada kemungkinan data bersifat latihan atau sintetis. Ini dugaan yang belum dikonfirmasi, dan karena itu rekomendasi diperlakukan sebagai hipotesis.
- **Nilai order adalah nilai nominal**, bukan revenue yang sudah terealisasi.
- **Segmentasi pelanggan adalah frekuensi pembelian dalam ±1 tahun**, bukan analisis kohort; pelanggan baru di akhir periode punya waktu lebih sedikit untuk membeli ulang.
- **Konsentrasi ada di level produk:** revenue lima kategori teratas identik sampai sen dengan satu produk. Pemetaan produk ke kategori belum diperiksa langsung.
- **Dua bulan parsial** (2013-07 dan 2014-07) dan **satu hari tanpa order** (2014-03-09).

## Struktur repositori

```
01-sql-ecommerce-analysis/
├── queries/                  
├── notebooks/
│   └── 01_eda_and_mart_prep.ipynb
├── data/
│   └── processed/            
├── docs/                     
├── insights.md               
├── audit_log.md              
├── requirements.txt
├── .env.example
└── README.md
```

| # | Pertanyaan | File Query |
|---|---|---|
| 1 | Kategori mana yang menghasilkan revenue terbesar? | [01_revenue_per_category.sql](queries/01_revenue_per_category.sql) |
| 2 | Produk apa saja yang paling banyak terjual? | [02_top_products.sql](queries/02_top_products.sql) |
| 3 | Pelanggan mana yang paling sering order? | [03_customer_analysis.sql](queries/03_customer_analysis.sql) |
| 4 | Bagaimana distribusi status order? | [04_order_status_distribution.sql](queries/04_order_status_distribution.sql) |
| 5 | Bagaimana tren revenue harian? | [05_daily_revenue.sql](queries/05_daily_revenue.sql) |
| 6 | Bagaimana revenue bulanan? | [06_monthly_revenue.sql](queries/06_monthly_revenue.sql) |
| 7 | Berapa kategori yang menopang ±80% revenue? | [07_category_pareto.sql](queries/07_category_pareto.sql) |
| 8 | Bagaimana tren bulanan, AOV, dan pertumbuhan MoM? | [08_monthly_mom_growth.sql](queries/08_monthly_mom_growth.sql) |
| 9 | Bagaimana segmentasi pelanggan berdasarkan frekuensi? | [09_customer_retention_tier.sql](queries/09_customer_retention_tier.sql) |

## Cara menjalankan

1. **Database:** siapkan PostgreSQL dengan dataset 6 tabel di atas.
2. **Query SQL:** jalankan file di `queries/` dengan pgAdmin Query Tool atau `psql`.
3. **Notebook:**
   ```
   python -m venv .venv
   pip install -r requirements.txt
   ```
   Salin `.env.example` menjadi `.env`, isi kredensial database, lalu jalankan `notebooks/01_eda_and_mart_prep.ipynb` dari awal (Restart kernel and run all). Notebook menghasilkan tiga CSV di `data/processed/`.
4. **Dashboard:** impor tiga CSV ke Google Sheets (locale **United States**, satu tab per file), lalu hubungkan ke Looker Studio.

## Tools

PostgreSQL 18 · pgAdmin 4 · Python (pandas, SQLAlchemy, psycopg2, seaborn) · Jupyter · Google Sheets · Looker Studio · Antigravity IDE · Git