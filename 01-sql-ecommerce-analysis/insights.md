# Insights — E-Commerce SQL Analysis

## Ringkasan

- **Definisi:** *valid revenue* = revenue dari order berstatus `COMPLETE` dan `CLOSED`, dalam **USD** (tidak ada kolom mata uang; satuan disimpulkan dari format harga, tanpa konversi).
- **Cakupan data:** 68.883 order, 2013-07-25 s.d. 2014-07-24 (365 hari, tidak ada order pada 2014-03-09). Bulan pertama (2013-07) dan terakhir (2014-07) parsial.
- **Total valid revenue: 15.012.982,48 USD**, konsisten di Query 01, 05, 06, 07, 08, dan 09.
- **Revenue sangat terkonsentrasi:** 7 dari 33 kategori menghasilkan 82,64% revenue, dan 9 produk menghasilkan ±94,6%.
- **Revenue bulanan relatif datar** (1,17 s.d. 1,38 juta USD per bulan penuh). Naik-turunnya lebih dipengaruhi jumlah order daripada nilai per order.
- **Pelanggan berulang (2x ke atas) = 69% pelanggan tetapi ±87% revenue.**
- **Kualitas data:** 5.189 order valid (±17%) tidak punya item, sehingga hitungan order, AOV, dan segmentasi pelanggan memakai definisi "order valid yang punya item".


## 1. Revenue per Category
**Query:** `01_revenue_per_category.sql` (dikelompokkan per `category_id`)

**Insight:**
- Kategori **Fishing** adalah penyumbang revenue terbesar: 3.022.248,88 USD (20,13% dari total).
- **33 dari 58 kategori** punya penjualan valid; 25 kategori tidak punya penjualan valid (sebagian bisa jadi kategori tanpa produk sama sekali; belum dipisahkan).
- Ada dua kategori bernama "Electronics" (ID 13 di departemen 3 dan ID 37 di departemen 6). Keduanya entitas berbeda (112.141,70 dan 49.014,70 USD), sehingga pengelompokan harus per `category_id`, bukan per nama.

**Rekomendasi Bisnis:**
- Pisahkan 25 kategori tanpa penjualan valid menjadi (a) kategori tanpa produk, kandidat dirapikan, dan (b) kategori berproduk tetapi tidak laku, kandidat promosi atau evaluasi.
- Rapikan kategori "Electronics" ganda (misalnya nama menyertakan departemen) agar laporan tidak membingungkan.


## 2. Top 10 Produk Terlaris
**Query:** `02_top_products.sql` (dikelompokkan per `product_id`)

**Insight:**
- Terlaris menurut unit: **Perfect Fitness Perfect Rip Deck** (ID 365), 32.165 unit dengan revenue 1.929.578,35 USD.
- **Peringkat unit tidak sama dengan peringkat revenue.** Produk ID 1004 (Field & Stream Sportsman 16 Gun Fire Safe) hanya ke-7 menurut unit (7.556), tetapi revenue-nya terbesar: 3.022.248,88 USD (±20% total), karena harga ±399,98 USD per unit.
- **Penjualan terkonsentrasi di 9 produk.** Sembilan produk teratas menyumbang 14.195.057,75 USD (±94,6% dari total valid revenue). Produk ke-10 hanya 476 unit (±14.275 USD).

**Rekomendasi Bisnis:**
- Jaga ketersediaan stok 9 produk utama, terutama ID 365 dan 1004, karena kekosongan stok berdampak langsung ke revenue.
- Tentukan "produk unggulan" dengan dua ukuran sekaligus (unit dan revenue), bukan salah satu saja.
- Sebelum merancang bundle, lakukan dulu analisis produk yang sering dibeli bersama (belum dikerjakan).


## 3. Customer Analysis
**Query:** `03_customer_analysis.sql` (dikelompokkan per `customer_id`)

**Insight:**
- Pelanggan dengan order valid terbanyak: **Mary Smith (customer_id 9337)**, 10 order, 6.585,33 USD. Pelanggan berikutnya punya 9 order (enam orang) dan 8 order (tiga orang di daftar).
- Ada dua pelanggan bernama "Mary Smith" (ID 9337 dan 4116). Pengelompokan per nama akan menyatukan mereka.
- Sepuluh pelanggan teratas ini hanya menyumbang 51.858,64 USD (±0,35% dari total valid revenue). Revenue tidak ditopang pelanggan individual.
- Jumlah order = order valid yang punya minimal 1 item. Banyak seri di daftar (beberapa pelanggan punya jumlah order sama), sehingga daftar top 10 bergantung pada pemisah seri (revenue, lalu ID).

**Rekomendasi Bisnis:**
- Arahkan program loyalitas ke **segmen** (lihat Bagian 9), bukan hanya 10 pelanggan teratas yang dampaknya kecil terhadap total revenue.
- Sebelum menawarkan insentif retensi, periksa tanggal order terakhir tiap pelanggan teratas apakah masih aktif (belum dianalisis).


## 4. Distribusi Order Status
**Query:** `04_order_status_distribution.sql` (persentase dinamis dengan window function)

**Insight:**
- **44,2% order masuk valid revenue:** `COMPLETE` 22.899 (33,24%) + `CLOSED` 7.556 (10,97%) = 30.455 dari 68.883 order.
- **55,8% order tidak masuk valid revenue**, terdiri dari:
  - 51,5% masih berjalan: `PENDING_PAYMENT` 15.030 (21,82%), `PROCESSING` 8.275 (12,01%), `PENDING` 7.610 (11,05%), `ON_HOLD` 3.798 (5,51%), `PAYMENT_REVIEW` 729 (1,06%), total 35.442 order;
  - 4,3% batal atau diduga fraud: `CANCELED` 1.428 + `SUSPECTED_FRAUD` 1.558 = 2.986 order.
- `PENDING_PAYMENT` adalah status non-valid terbesar.
- Data berupa satu potret tanpa riwayat perubahan status, sehingga tidak diketahui apakah order yang berjalan akhirnya selesai.

**Rekomendasi Bisnis:**
- Tinjau 15.030 order `PENDING_PAYMENT`: sudah berapa lama tertahan dan di tahap apa (dugaan masalah pembayaran masih harus dibuktikan).
- Tinjau penanganan 1.558 order `SUSPECTED_FRAUD` (2,26%) dan estimasi nilainya.
- Analisis lanjutan: hitung revenue per status untuk mengetahui potensi revenue yang masih tertahan.


## 5. Revenue Harian
**Query:** `05_daily_revenue.sql` (`order_date::date`)

**Insight:**
- Revenue harian tertinggi: **2013-11-03** (69.977,41 USD), ±1,7 kali rata-rata harian (±41.244 USD per hari aktif). Terendah: 2013-12-16 (10.255,68 USD).
- Fluktuasi harian lebar (kira-kira 10 ribu sampai 70 ribu USD), sehingga satu hari puncak belum cukup untuk menyimpulkan penyebabnya.
- Data hanya memuat 364 hari. Tidak ada order sama sekali pada 2014-03-09; penyebabnya tidak dapat ditentukan dari database.

**Rekomendasi Bisnis:**
- Cocokkan hari puncak dengan kalender promo atau event jika datanya tersedia (tidak ada di database ini).
- Analisis lanjutan: pola per hari dalam minggu untuk melihat ritme mingguan.


## 6. Revenue Bulanan
**Query:** `06_monthly_revenue.sql`

**Insight:**
- Bulan penuh terbaik: **2013-11**, 1.379.935,33 USD.
- Data mencakup 13 bulan (2013-07 s.d. 2014-07), tetapi **hanya 11 bulan penuh** (2013-08 s.d. 2014-06). 2013-07 (7 hari) dan 2014-07 (24 hari) parsial dan tidak bisa dibandingkan langsung dengan bulan lain.

**Rekomendasi Bisnis:**
- Satu tahun data tidak cukup untuk menyatakan pola musiman. Pantau November tahun berikutnya untuk menguji apakah lonjakan 2013-11 berulang sebelum merencanakan promo berdasarkan itu.


## 7. Kontribusi Kategori dan Pareto
**Query:** `07_category_pareto.sql`

**Insight:**
- **7 dari 33 kategori (21,2%) menyumbang 82,64% valid revenue.** Tiga teratas (Fishing, Cleats, Camping & Hiking) = 45,02%; delapan teratas = 91,02%; 25 kategori sisanya berbagi 8,98%.
- Revenue Fishing, Camping & Hiking, Women's Apparel, Men's Footwear, dan Indoor/Outdoor Games masing-masing identik sampai sen dengan revenue satu produk di Query 02. Konsentrasi ini terjadi di level produk, bukan hanya kategori.
- `total_orders` per kategori tidak boleh dijumlahkan: totalnya 66.103 versus 25.266 order, karena satu order bisa memuat beberapa kategori (±2,6 kategori per order).

**Rekomendasi Bisnis:**
- Prioritaskan pengelolaan stok, harga, dan kualitas data pada 7 kategori inti.
- Pantau risiko konsentrasi: gangguan pada beberapa produk berdampak besar pada total revenue.


## 8. Tren Bulanan, AOV, dan Pertumbuhan MoM
**Query:** `08_monthly_mom_growth.sql`

**Insight:**
- Sebelas bulan penuh bergerak antara 1.171.686,92 dan 1.379.935,33 USD, tanpa tren naik atau turun yang konsisten. Dari 10 nilai MoM yang dapat dihitung, 3 positif dan 7 negatif (−10,03% sampai +17,77%). Puncak: November 2013 (+17,77% dari Oktober). Agustus 2013 ke Juni 2014: −3,44%.
- **AOV stabil** (581,94 s.d. 603,76 USD, selisih ±3,7%), sedangkan jumlah order bulanan berkisar 1.954 s.d. 2.336 (±19,5%). Variasi revenue terutama berasal dari **jumlah order**, bukan nilai per order.
- MoM sengaja tidak dihitung untuk bulan parsial. Tanpa koreksi, hasilnya +266% (Agustus 2013) dan −19% (Juli 2014), yang hanya mencerminkan jumlah hari.
- Definisi: AOV = revenue ÷ order valid yang punya item (rata-rata keseluruhan ±594,20 USD). Jika penyebutnya seluruh 30.455 order valid, AOV ±493 USD.

**Rekomendasi Bisnis:**
- Karena AOV hampir tidak berubah, ukur inisiatif lewat dampaknya pada jumlah order. Menaikkan AOV memerlukan intervensi terpisah (misalnya uji bundle).
- Bandingkan antar bulan dengan rata-rata revenue per hari bila jumlah harinya berbeda.


## 9. Segmentasi Retensi Pelanggan
**Query:** `09_customer_retention_tier.sql`

**Insight (populasi: 10.844 pelanggan dengan order valid yang punya item, dari 12.435 pelanggan):**

| Tingkat | Pelanggan | % Pelanggan | % Revenue | Revenue per pelanggan (USD) |
|---|---|---|---|---|
| One-time (1x) | 3.356 | 30,95% | 13,26% | 593,25 |
| Repeat (2-3x) | 5.664 | 52,23% | 53,98% | 1.430,70 |
| Loyal (4x+) | 1.824 | 16,82% | 32,76% | 2.696,58 |

- Pelanggan Repeat dan Loyal = 69,05% pelanggan tetapi **86,74% revenue**.
- Pelanggan Loyal bernilai ±4,5 kali pelanggan sekali beli per kepala.
- Nilai per order hampir sama di semua tingkat (±593 s.d. 595 USD). Perbedaan kontribusi berasal dari **frekuensi pembelian**, bukan keranjang yang lebih besar.

**Keterbatasan:**
- Ini segmentasi frekuensi pembelian dalam periode ±1 tahun, bukan retensi kohort. Pelanggan yang baru bergabung di akhir periode punya waktu lebih sedikit untuk membeli ulang, sehingga porsi One-time bisa terlihat terlalu tinggi.
- Hasil sensitif terhadap definisi order: bila semua order valid dihitung (11.405 pelanggan), porsi Loyal naik dari 16,8% menjadi 25,1%.

**Rekomendasi Bisnis:**
- Uji kampanye pembelian ulang untuk segmen Repeat (5.664 pelanggan), karena naik tingkat ke Loyal berpotensi menaikkan nilai per pelanggan secara signifikan (hipotesis yang perlu diuji, bukan kepastian).
- Untuk pelanggan One-time, periksa dulu tanggal order pertamanya sebelum menyimpulkan mereka "tidak kembali".


## 10. Kualitas Data dan Keterbatasan

- **5.189 order valid (±17,0% dari 30.455) tidak punya item** di `order_items` dan tersebar di semua status. Revenue tidak terpengaruh (order itu tidak punya subtotal), tetapi hitungan order, AOV, dan segmentasi pelanggan terpengaruh. Penyebabnya tidak dapat ditentukan dari database.
- **Pelanggan:** dari 12.435 pelanggan, 11.405 punya order valid dan 10.844 punya order valid dengan item.
- **Rentang waktu:** 2013-07 dan 2014-07 parsial; tidak ada order pada 2014-03-09.
- **Satuan:** tidak ada kolom mata uang; harga diasumsikan USD dan tidak dikonversi.
- **Cakupan:** satu tahun data dan satu potret status order, sehingga pola musiman dan perubahan status tidak dapat disimpulkan.
- **Validasi silang:** total valid revenue 15.012.982,48 USD sama di Query 01, 05, 06, 07, 08, dan 09.