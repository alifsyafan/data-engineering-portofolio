# E-Commerce SQL Analysis
Analisis data sales e-commerce menggunakan PostgreSQL untuk menjawab 6 pertanyaan bisnis.

## Dataset
Dataset terdiri dari 6 tabel yang saling berelasi:

| Tabel | Deskripsi | Jumlah Baris |
|---|---|---|
| `departments` | Departemen | 6 |
| `categories` | Kategori produk | 58 |
| `products` | Produk | 1.345 |
| `customers` | Customer | 124.535 |
| `orders` | Order | 68.883 |
| `order_items` | Detail item per order | 172.198 |

**Relasi:**
- `departments → categories → products`
- `customers → orders → order_items`
- `products → order_items`

## Pertanyaan Bisnis & Query
| # | Pertanyaan | File Query |
|---|---|---|
| 1 | Kategori mana yang menghasilkan revenue terbesar? | [01_revenue_per_category.sql](queries/01_revenue_per_category.sql) |
| 2 | Produk apa saja yang paling banyak terjual? | [02_top_products.sql](queries/02_top_products.sql) |
| 3 | Customer mana yang paling sering order? | [03_customer_analysis.sql](queries/03_customer_analysis.sql) |
| 4 | Bagaimana distribusi status order? | [04_order_status_distribution.sql](queries/04_order_status_distribution.sql) |
| 5 | Bagaimana tren revenue harian? | [05_daily_revenue.sql](queries/05_daily_revenue.sql) |
| 6 | Bagaimana pertumbuhan revenue bulanan? | [06_monthly_revenue.sql](queries/06_monthly_revenue.sql) |

## Insight
- **Revenue per category:** Fishing adalah kategori dengan revenue tertinggi (Rp 3,02 juta).
- **Top produk:** Perfect Fitness Perfect Rip Deck adalah produk terlaris (32.165 unit).
- **Customer:** Jacob & Mary adalah customer paling aktif (10 order).
- **Order status:** Hanya 44% order yang selesai (COMPLETE + CLOSED). 56% lainnya masih pending/processing.
- **Revenue harian:** Hari dengan revenue tertinggi adalah 2013-11-03.
- **Revenue bulanan:** Bulan terbaik adalah 2013-11 (Rp 1,38 juta).

## Tools
- PostgreSQL 16
- pgAdmin 4
- VS Code

## Cara Menjalankan
1. Setup database PostgreSQL dengan dataset e-commerce (6 tabel).
2. Jalankan setiap file `.sql` di folder `queries/` menggunakan pgAdmin Query Tool atau `psql`.

## Author
Muhammad Alif Syafan