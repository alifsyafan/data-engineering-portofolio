# Audit Log — E-Commerce SQL Analysis

Catatan proses audit: apa yang diperiksa, apa yang ditemukan, apa dampaknya,
apa yang diperbaiki, dan bukti validasinya. Kesimpulan bisnis ada di `insights.md`;
file ini mencatat **bagaimana** angka-angka itu dapat dipercaya.


## 0. Konteks

| Item | Nilai |
|---|---|
| Database | PostgreSQL, 6 tabel: `orders`, `order_items`, `products`, `categories`, `departments`, `customers` |
| Jumlah baris | orders 68.883; order_items 172.198; products 1.345; categories 58; departments 6; customers 12.435 |
| Rentang tanggal | 2013-07-25 s.d. 2014-07-24 (365 hari kalender) |
| Definisi valid revenue | Jumlah `order_item_subtotal` dari order berstatus `COMPLETE` atau `CLOSED` |
| Satuan | USD (disimpulkan dari format harga; tidak ada kolom mata uang; tidak ada konversi) |
| Status order | 9 nilai, seluruhnya huruf besar, tanpa variasi penulisan |

Distribusi status: COMPLETE 22.899; PENDING_PAYMENT 15.030; PROCESSING 8.275; PENDING 7.610; CLOSED 7.556; ON_HOLD 3.798; SUSPECTED_FRAUD 1.558; CANCELED 1.428; PAYMENT_REVIEW 729 (total 68.883).


## 1. Audit per query

### Query 01 — Revenue per kategori
- **Masalah:** dikelompokkan per `category_name`.
- **Dampak:** dua kategori bernama "Electronics" (ID 13 di departemen 3, ID 37 di departemen 6) akan menyatu menjadi satu baris bernilai 161.156,40 (112.141,70 + 49.014,70).
- **Perbaikan:** `GROUP BY c.category_id, c.category_name`.
- **Bukti:** hasil menampilkan 33 kategori dan dua "Electronics" terpisah.
- **Temuan:** hanya 33 dari 58 kategori punya penjualan valid. Angka "32" di versi lama berasal dari bug pengelompokan per nama.

### Query 02 — Top 10 produk terlaris
- **Masalah:** dikelompokkan per `product_name`; `LIMIT 10` tanpa pemisah seri.
- **Dampak:** produk bernama sama bisa menyatu; baris yang imbang bisa berganti antar eksekusi.
- **Perbaikan:** `GROUP BY p.product_id, p.product_name`; `ORDER BY total_quantity DESC, p.product_id`; ditambah kolom `total_revenue_usd`.
- **Temuan:** produk ID 365 terlaris menurut unit (32.165). Produk ID 1004 hanya ke-7 menurut unit (7.556) tetapi ke-1 menurut revenue (3.022.248,88 USD). Sembilan produk teratas menyumbang 14.195.057,75 USD (±94,6% total).

### Query 03 — Analisis pelanggan
- **Masalah:** `||` rentan `NULL`; `COUNT` tanpa `DISTINCT`; tidak ada revenue.
- **Dampak:** nama bisa hilang; jumlah order membengkak karena satu order punya banyak item (fan-out).
- **Perbaikan:** `CONCAT`; `COUNT(DISTINCT o.order_id)`; JOIN ke `order_items`; tambah `SUM(order_item_subtotal)`.
- **Bukti fan-out** (tanpa vs dengan `DISTINCT`): 33 vs 10, 28 vs 9, 28 vs 8, 28 vs 7, 28 vs 9. Rasio 3,1 sampai 4,0. Kelima sampel dipilih dari baris terbanyak, jadi bukan rata-rata seluruh pelanggan.
- **Temuan:** dua pelanggan bernama "Mary Smith" (ID 9337 dan 4116). Pelanggan dengan order terbanyak adalah ID 9337 (10 order, 6.585,33 USD). Sepuluh pelanggan teratas hanya ±0,35% dari valid revenue.
- **Definisi:** order = order valid yang punya minimal 1 item.

### Query 04 — Distribusi status order
- **Masalah:** persentase belum ada.
- **Perbaikan:** `COUNT(...) * 100.0 / SUM(COUNT(...)) OVER ()` (dinamis, tanpa angka 68883 yang ditulis manual).
- **Bukti:** total 68.883; jumlah persentase 99,99 (selisih pembulatan).
- **Temuan:** 44,2% order valid; 51,5% masih berjalan; 4,3% batal atau diduga fraud.

### Query 05 — Revenue harian
- **Masalah:** alias belum berlabel USD; risiko pengelompokan per timestamp.
- **Perbaikan:** `order_date::date`; alias `daily_revenue_usd`.
- **Bukti:** `MIN(order_date)` = 2013-07-25, `MAX(order_date)` = 2014-07-24, sama untuk semua order maupun order valid.
- **Temuan:** hanya 364 hari yang punya revenue. Tidak ada order sama sekali pada 2014-03-09 (diverifikasi dengan query; penyebab tidak diketahui).

### Query 06 — Revenue bulanan
- **Masalah:** alias belum USD; kelengkapan bulan tidak dicek.
- **Perbaikan:** alias `monthly_revenue_usd`; tambah `active_days`.
- **Temuan:** 2013-07 hanya 7 hari dan 2014-07 hanya 24 hari (parsial). Sebelas bulan lainnya penuh.

### Query 07 — Kontribusi kategori dan Pareto
- **Masalah (versi tugas):** `GROUP BY` per nama; kumulatif memakai frame bawaan (`RANGE`) tanpa pemisah seri.
- **Perbaikan:** `GROUP BY category_id, category_name`; `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` dengan urutan deterministik; ditambah `revenue_rank` dan `pareto_group`.
- **Bukti:** 33 baris; kumulatif akhir 100,00; total revenue 15.012.982,48.
- **Temuan:** 7 dari 33 kategori (21,2%) menyumbang 82,64%.
- **Catatan:** `total_orders` per kategori tidak boleh dijumlahkan (total 66.103 vs 25.266 order, karena satu order bisa memuat beberapa kategori).

### Query 08 — Tren bulanan, AOV, MoM
- **Masalah (versi tugas):** MoM dihitung juga untuk bulan parsial.
- **Dampak:** tanpa koreksi, Agustus 2013 tampak +266% dan Juli 2014 tampak −19%. Keduanya hanya efek jumlah hari.
- **Perbaikan:** bulan parsial dideteksi dari rentang tanggal data (bukan dari `active_days`, karena Maret 2014 tetap penuh walau 9 Maret kosong); MoM hanya dihitung jika bulan ini dan bulan lalu sama-sama penuh, selain itu `NULL`; ditambah `avg_daily_revenue_usd`.
- **Bukti:** `month_status` = PARTIAL hanya di 2013-07 dan 2014-07; jumlah `total_orders` = 25.266.
- **Temuan:** 10 nilai MoM dapat dihitung (−10,03% sampai +17,77%); AOV stabil (581,94 sampai 603,76 USD).

### Query 09 — Segmentasi retensi pelanggan
- **Masalah (versi tugas):** kolom jumlah order dan rata-rata revenue per pelanggan belum ada; definisi tidak tertulis.
- **Perbaikan:** `COUNT(*)` menggantikan `COUNT(kolom)`; ditambah `total_orders` dan `avg_revenue_per_customer_usd`; catatan definisi di header.
- **Bukti:** jumlah order 25.266; revenue 15.012.982,48; populasi 10.844 pelanggan.
- **Temuan:** Repeat + Loyal = 69,05% pelanggan dan 86,74% revenue. Nilai per order hampir sama di semua tingkat (±593 sampai 595 USD).
- **Catatan:** ini segmentasi frekuensi pembelian dalam ±1 tahun, bukan retensi kohort.


## 2. Temuan kualitas data

| ID | Temuan | Bukti | Dampak | Status |
|---|---|---|---|---|
| DQ-1 | 5.189 order valid (17,0% dari 30.455) tidak punya item di `order_items`, tersebar di semua status | 30.455 order valid vs 25.266 order valid yang punya item | Revenue tidak terpengaruh. Jumlah order, AOV (±594 vs ±493 USD), dan segmentasi pelanggan terpengaruh | Terverifikasi; penyebab tidak dapat ditentukan dari database |
| DQ-2 | Dari 12.435 pelanggan, 11.405 punya order valid dan 10.844 punya order valid dengan item | Query pembanding dan hasil Q09 | 1.030 pelanggan tanpa order valid; 561 lagi hilang karena DQ-1 | Terverifikasi |
| DQ-3 | Tidak ada order pada 2014-03-09 | Query pada rentang 2014-03-08 s.d. 2014-03-10 | Celah satu hari di data harian | Terverifikasi; penyebab tidak diketahui |
| DQ-4 | Bulan pertama (2013-07, 7 hari) dan terakhir (2014-07, 24 hari) parsial | `MIN`/`MAX` tanggal dan `active_days` | Tidak dapat dibandingkan langsung dengan bulan penuh | Terverifikasi; ditangani di Q08 |
| DQ-5 | Nama kembar: dua kategori "Electronics", dua pelanggan "Mary Smith" | ID berbeda (kategori 13 dan 37; pelanggan 9337 dan 4116) | Pengelompokan per nama menggabungkan entitas berbeda | Terverifikasi; ditangani dengan `GROUP BY` ID |
| DQ-6 | Revenue lima kategori identik sampai sen dengan revenue satu produk (Fishing = produk 1004; Camping & Hiking = 957; Women's Apparel = 502; Indoor/Outdoor Games = 1014; Men's Footwear = 403) | Perbandingan hasil Q01 dan Q02 | Konsentrasi revenue ada di level produk | Terverifikasi dari angka; pemetaan produk-kategori belum diperiksa langsung |
| DQ-7 | Tidak ada kolom mata uang | Format harga (dua desimal, banyak akhiran .99) | Satuan diasumsikan USD | Asumsi; tidak ada konversi |


## 3. Validasi silang

| Angka | Nilai | Sumber yang cocok |
|---|---|---|
| Total valid revenue | 15.012.982,48 USD | Q01, Q05, Q06, Q07, Q08, Q09, total langsung, dan pandas (Hari 3) |
| Order valid | 30.455 | Hitungan langsung dari `orders` dan pandas |
| Order valid yang punya item | 25.266 | Jumlah `total_orders` Q08, Q09, dan pandas |
| Total order | 68.883 | Q04 dan pandas |
| Kategori dengan penjualan valid | 33 | Q01 dan Q07 |

**Koreksi proses:** angka acuan awal untuk jumlah order Q08 dan Q09 adalah 30.455,
tetapi `JOIN` ke `order_items` menyaring order tanpa item sehingga yang benar adalah 25.266.
Selisih ini yang membuka DQ-1. Angka acuan harus berasal dari populasi yang sama
dengan query yang divalidasi.


## 4. Validasi pipeline Python (Hari 3)

- Koneksi PostgreSQL ke pandas memakai SQLAlchemy dengan kredensial dari `.env` (tidak di-commit).
- Enam tabel termuat dengan jumlah baris sesuai `COUNT(*)` di PostgreSQL.
- Reproduksi di pandas (`merge` inner): 30.455 order valid; 25.266 order valid yang punya item; 15.012.982,48 USD. Semuanya sama dengan hasil SQL.


## 5. Keterbatasan dan tindak lanjut

- Pisahkan 25 kategori tanpa penjualan valid: tanpa produk sama sekali vs berproduk tetapi tidak laku.
- Periksa pemetaan produk ke kategori untuk 9 produk teratas (nama produk tampak tidak selalu sesuai namanya kategori).
- Periksa apakah nama produk terpotong 45 karakter di sumber data.
- Hitung revenue per status untuk melihat potensi revenue yang tertahan.
- Analisis retensi kohort sungguhan (Q09 baru segmentasi frekuensi).
- Data hanya mencakup satu tahun dan satu potret status order, sehingga pola musiman dan perubahan status tidak dapat disimpulkan.


## 6. Format entri baru

Setiap temuan baru dicatat dengan: **ID, temuan, bukti (query atau angka), dampak, tindakan, status**
(Terverifikasi / Dugaan / Terbuka).