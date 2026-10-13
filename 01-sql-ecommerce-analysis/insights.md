# Insights — E-Commerce SQL Analysis

## 1. Revenue per Category
**Query:** `01_revenue_per_category.sql`

**Insight:**
- Kategori **Fishing** adalah penyumbang revenue terbesar.
- 32 dari 58 kategori pernah menghasilkan penjualan (COMPLETE/CLOSED).

**Rekomendasi Bisnis:**
- Fokus marketing budget ke kategori Fishing.
- Investigasi 26 kategori yang belum pernah terjual, apakah perlu dihapus atau butuh promosi.


## 2. Top 10 Produk Terlaris
**Query:** `02_top_products.sql`

**Insight:**
- Produk terlaris: **Perfect Fitness Perfect Rip Deck** (32.165 unit).

**Rekomendasi Bisnis:**
- Pastikan stok produk ini selalu tersedia.
- Cari produk serupa untuk dijual sebagai bundle.


## 3. Customer Analysis
**Query:** `03_customer_analysis.sql`

**Insight:**
- Customer paling aktif: **Jacob & Mary** (10 order).

**Rekomendasi Bisnis:**
- Berikan loyalty program untuk top 10 customer.
- Tawarkan diskon khusus untuk mempertahankan mereka.


## 4. Distribusi Order Status
**Query:** `04_order_status_distribution.sql`

**Insight:**
- **Hanya 44% order yang selesai** (COMPLETE 22.899 + CLOSED 7.556 = 30.455 dari 68.883).
- **56% order tidak selesai** — banyak yang masih pending/payment/processing.
- **4% order dibatalkan atau fraud** (CANCELED 1.428 + SUSPECTED_FRAUD 1.558 = 2.986).

**Rekomendasi Bisnis:**
- Investigasi kenapa 56% order tidak selesai, apakah masalah di payment gateway atau proses bisnis.
- Tingkatkan fraud detection untuk mengurangi SUSPECTED_FRAUD.


## 5. Revenue Harian
**Query:** `05_daily_revenue.sql`

**Insight:**
- Hari dengan revenue tertinggi: **2013-11-03**.

**Rekomendasi Bisnis:**
- Cek event apa yang terjadi di tanggal tersebut (promo? hari besar?).


## 6. Revenue Bulanan

**Query:** `06_monthly_revenue.sql`

**Insight:**
- Bulan terbaik: **2013-11** (Rp 1,38 juta).
- Data mencakup 13 bulan (2013-07 hingga 2014-07).

**Rekomendasi Bisnis:**
- Rencanakan promo serupa di periode yang sama tahun berikutnya.