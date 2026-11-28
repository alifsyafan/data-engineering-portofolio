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
- **Tindak lanjut:** nilai order per status dan pengujian dua hipotesis tentang status dicatat di Bagian 5.

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
- **Masalah:** `GROUP BY` per nama; kumulatif memakai frame bawaan (`RANGE`) tanpa pemisah seri.
- **Perbaikan:** `GROUP BY category_id, category_name`; `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` dengan urutan deterministik; ditambah `revenue_rank` dan `pareto_group`.
- **Bukti:** 33 baris; kumulatif akhir 100,00; total revenue 15.012.982,48.
- **Temuan:** 7 dari 33 kategori (21,2%) menyumbang 82,64%.
- **Catatan:** `total_orders` per kategori tidak boleh dijumlahkan (total 66.103 vs 25.266 order, karena satu order bisa memuat beberapa kategori).

### Query 08 — Tren bulanan, AOV, MoM
- **Masalah:** MoM dihitung juga untuk bulan parsial.
- **Dampak:** tanpa koreksi, Agustus 2013 tampak +266% dan Juli 2014 tampak −19%. Keduanya hanya efek jumlah hari.
- **Perbaikan:** bulan parsial dideteksi dari rentang tanggal data (bukan dari `active_days`, karena Maret 2014 tetap penuh walau 9 Maret kosong); MoM hanya dihitung jika bulan ini dan bulan lalu sama-sama penuh, selain itu `NULL`; ditambah `avg_daily_revenue_usd`.
- **Bukti:** `month_status` = PARTIAL hanya di 2013-07 dan 2014-07; jumlah `total_orders` = 25.266.
- **Temuan:** 10 nilai MoM dapat dihitung (−10,03% sampai +17,77%); AOV stabil (581,94 sampai 603,76 USD).

### Query 09 — Segmentasi retensi pelanggan
- **Masalah:** kolom jumlah order dan rata-rata revenue per pelanggan belum ada; definisi tidak tertulis.
- **Perbaikan:** `COUNT(*)` menggantikan `COUNT(kolom)`; ditambah `total_orders` dan `avg_revenue_per_customer_usd`; catatan definisi di header.
- **Bukti:** jumlah order 25.266; revenue 15.012.982,48; populasi 10.844 pelanggan.
- **Temuan:** Repeat + Loyal = 69,05% pelanggan dan 86,74% revenue. Nilai per order hampir sama di semua tingkat (±593 sampai 595 USD).
- **Catatan:** ini segmentasi frekuensi pembelian dalam ±1 tahun, bukan retensi kohort.


## 2. Temuan kualitas data

| ID | Temuan | Bukti | Dampak | Status |
|---|---|---|---|---|
| DQ-1 | 5.189 order valid (17,0% dari 30.455) tidak punya item di `order_items`. Di seluruh data, 11.452 dari 68.883 order (16,63%) tanpa item, tersebar merata di semua status. | 30.455 order valid vs 25.266 order valid yang punya item | Revenue tidak terpengaruh. Jumlah order, AOV (±594 vs ±493 USD), dan segmentasi pelanggan terpengaruh | Terverifikasi; penyebab tidak dapat ditentukan dari database |
| DQ-2 | Dari 12.435 pelanggan, 11.405 punya order valid dan 10.844 punya order valid dengan item | Query pembanding dan hasil Q09 | 1.030 pelanggan tanpa order valid; 561 lagi hilang karena DQ-1 | Terverifikasi |
| DQ-3 | Tidak ada order pada 2014-03-09 | Query pada rentang 2014-03-08 s.d. 2014-03-10 | Celah satu hari di data harian | Terverifikasi; penyebab tidak diketahui |
| DQ-4 | Bulan pertama (2013-07, 7 hari) dan terakhir (2014-07, 24 hari) parsial | `MIN`/`MAX` tanggal dan `active_days` | Tidak dapat dibandingkan langsung dengan bulan penuh | Terverifikasi; ditangani di Q08 |
| DQ-5 | Nama kembar: dua kategori "Electronics", dua pelanggan "Mary Smith" | ID berbeda (kategori 13 dan 37; pelanggan 9337 dan 4116) | Pengelompokan per nama menggabungkan entitas berbeda | Terverifikasi; ditangani dengan `GROUP BY` ID |
| DQ-6 | Revenue lima kategori identik sampai sen dengan revenue satu produk (Fishing = produk 1004; Camping & Hiking = 957; Women's Apparel = 502; Indoor/Outdoor Games = 1014; Men's Footwear = 403) | Perbandingan hasil Q01 dan Q02 | Konsentrasi revenue ada di level produk | Terverifikasi dari angka; pemetaan produk-kategori belum diperiksa langsung |
| DQ-7 | Tidak ada kolom mata uang | Format harga (dua desimal, banyak akhiran .99) | Satuan diasumsikan USD | Asumsi; tidak ada konversi |
| DQ-8 | Order tanpa item tidak terkait status maupun bulan: orphan rate 15,93% s.d. 17,18% antar status dan 15,58% s.d. 17,19% antar bulan (keseluruhan 16,63%) | Notebook Kasus 1 (`orphan_by_status`, `orphan_by_month`); orphan `COMPLETE` + `CLOSED` = 3.934 + 1.255 = 5.189, cocok dengan SQL; jumlah orphan sama lewat `merge` dan `isin()` (11.452); item tanpa order induk = 0, jadi kekosongan hanya terjadi pada satu arah | Ketiadaan item tidak dapat dijelaskan oleh variabel apa pun di database. Hitungan order, AOV, dan segmentasi pelanggan hanya mencakup 57.431 order yang punya item | Terverifikasi; penyebab tidak dapat ditentukan dari database |
| DQ-9 | Dalam variabel yang diuji (nilai order, bulan, pelanggan), status order tidak menunjukkan keterkaitan | Notebook Kasus 2: median nilai order 529,97 s.d. 579,95 antar status; proporsi status per bulan stabil (selisih maksimum ±1,5 poin persentase); order 2013-07 masih 23,03% `PENDING_PAYMENT`; pelanggan dengan order fraud sesuai perkiraan acak | Tidak ada variabel di database yang menjelaskan 56% order tidak selesai atau tanda fraud | Terverifikasi (pola); dugaan bahwa data bersifat latihan belum dikonfirmasi |


## 3. Validasi silang

| Angka | Nilai | Sumber yang cocok |
|---|---|---|
| Total valid revenue | 15.012.982,48 USD | Q01, Q05, Q06, Q07, Q08, Q09, total langsung, dan pandas (Hari 3, Kasus 2 dan 3) |
| Order valid | 30.455 | Hitungan langsung dari `orders` dan pandas |
| Order valid yang punya item | 25.266 | Jumlah `total_orders` Q08, Q09, dan pandas (Kasus 3) |
| Total order | 68.883 | Q04 dan pandas |
| Order tanpa item | 11.452 (16,63%) | Jumlah orphan per status dan per bulan (Kasus 1); selisih `total_orders` − `orders_with_items` (Kasus 2) |
| Order dengan item | 57.431 | `orders_with_items` per status (Kasus 2); sama dengan 68.883 − 11.452 |
| Baris hasil left merge `orders` × `order_items` | 183.650 | 172.198 item + 11.452 order tanpa item (Kasus 1) |
| Item tanpa order induk | 0 | Pemeriksaan arah sebaliknya dengan `isin()` (Kasus 1) |
| Total nilai order semua status | 34.322.619,93 USD | Jumlah `total_revenue` per status (Kasus 2) dan total `order_item_subtotal` di `order_items` (identik); bagian `COMPLETE` + `CLOSED` = 15.012.982,48, sama dengan Q01 s.d. Q09 |
| Rata-rata nilai order valid (AOV) | 594,20 USD | Kasus 3 dan 15.012.982,48 ÷ 25.266 |
| Kategori dengan penjualan valid | 33 | Q01 dan Q07 |
| KPI dashboard Halaman 1 | 15.012.982,48 USD; 25.266 order; AOV 594,20; Valid Order Share 43,99% | Query SQL langsung (revenue, order, AOV), Python (Kasus 3), dan `mart_daily_orders.csv` |
| Status order di dashboard Halaman 2 | 68.883 order; nilai order 34.322.619,93 USD | Query 04, Kasus 2, dan `mart_daily_orders.csv` |

**Koreksi proses:** angka acuan awal untuk jumlah order Q08 dan Q09 adalah 30.455,
tetapi `JOIN` ke `order_items` menyaring order tanpa item sehingga yang benar adalah 25.266.
Selisih ini yang membuka DQ-1. Angka acuan harus berasal dari populasi yang sama
dengan query yang divalidasi.


## 4. Validasi pipeline Python

- Koneksi PostgreSQL ke pandas memakai SQLAlchemy dengan kredensial dari `.env`.
- Enam tabel termuat dengan jumlah baris sesuai `COUNT(*)` di PostgreSQL (orders 68.883; order_items 172.198; products 1.345; categories 58; departments 6; customers 12.435).
- `order_date` terbaca sebagai `datetime64`, sehingga tidak perlu konversi tanggal.
- Reproduksi di pandas (`merge` inner): 30.455 order valid; 25.266 order valid yang punya item; 15.012.982,48 USD. Semuanya sama dengan hasil SQL.
- Agregasi `order_items` menjadi satu baris per order dilakukan **sebelum** `merge` ke `orders` (mencegah fan-out), dengan `validate="one_to_one"`. Hasilnya 68.883 baris, dan jumlah order tanpa nilai (NaN) = 11.452, sama dengan jumlah orphan di Kasus 1.
- Left merge `orders` × `order_items` menghasilkan 183.650 baris = 172.198 item + 11.452 order tanpa item. Artinya setiap item cocok dengan tepat satu order, dan setiap orphan muncul tepat satu kali.
- Orphan dihitung dengan dua cara, yaitu `merge` (kolom `order_item_id` kosong) dan `isin()`. Hasilnya sama: 11.452.
- Integritas relasi arah sebaliknya: item tanpa order induk = 0.
- Total nilai order semua status di pandas (34.322.619,93 USD) sama dengan total `order_item_subtotal` di `order_items` (34.322.619,93 USD).


## 5. Investigasi Python

Notebook: `notebooks/01_eda_and_mart_prep.ipynb`. Semua angka berasal dari sel kode di notebook.

### 5.1 Hipotesis yang diuji

| Hipotesis | Dianggap salah jika | Hasil | Status |
|---|---|---|---|
| H1: order `SUSPECTED_FRAUD` bernilai lebih besar daripada order valid | Median dan p95 fraud tidak lebih tinggi | Median fraud 549,95 vs 559,94 (`COMPLETE`) dan 559,93 (`CLOSED`); p95 sama (±1.200); maksimum fraud 1.979,83 lebih kecil dari `COMPLETE` (3.449,91) | **Tidak didukung** |
| H2: order belum selesai menumpuk di bulan tertentu, terutama bulan terbaru | Proporsi status sama tiap bulan; bulan lama tetap punya porsi pending yang sama | Proporsi stabil; 2013-07 masih 23,03% `PENDING_PAYMENT` (rata-rata 21,82%); selisih terbesar dari rata-rata keseluruhan ±1,5 poin persentase dan tidak searah | **Tidak didukung** |
| H3: fraud mengelompok pada pelanggan tertentu | Jumlah pelanggan berulang fraud jauh di atas perkiraan acak | Aktual 1.470 / 83 / 4 pelanggan (≥1 / ≥2 / ≥3 order fraud) vs perkiraan acak 1.464,4 / 89,8 / 3,7 (model binomial memakai jumlah order tiap pelanggan; dihitung di notebook) | **Tidak ada bukti** |
| H4: order `PENDING` mengelompok pada pelanggan tertentu | Jumlah pelanggan berulang pending jauh di atas perkiraan acak | Aktual 5.681 / 1.554 / 310 / 58 / 6 pelanggan (≥1 sampai ≥5 order pending) vs perkiraan acak 5.692,5 / 1.564,3 / 302,4 / 44,8 / 5,4. Hanya ≥4 yang agak di atas (58 vs 44,8, ±2 simpangan baku), wajar terjadi kebetulan dari delapan perbandingan | **Tidak ada bukti** |
| H5: status `PENDING` atau `SUSPECTED_FRAUD` terkait hari dalam minggu | Proporsi per hari jauh dari proporsi keseluruhan | `PENDING` 10,70% s.d. 11,37% (keseluruhan 11,05%); `SUSPECTED_FRAUD` 2,13% s.d. 2,40% (keseluruhan 2,26%), di dalam kisaran fluktuasi acak | **Tidak ada bukti** |

### 5.2 Kasus 1: orphan orders
- **Bukti:** 11.452 dari 68.883 order (16,63%) tanpa item. Orphan rate per status 15,93% (`ON_HOLD`) s.d. 17,18% (`COMPLETE`); per bulan 15,58% (2014-07) s.d. 17,19% (2014-03).
- **Validasi:** orphan `COMPLETE` + `CLOSED` = 5.189 (sama dengan SQL); order dengan item 57.431 = 68.883 − 11.452; baris hasil merge 183.650 = 172.198 + 11.452; orphan lewat `isin()` = lewat `merge` = 11.452; item tanpa order induk = 0.
- **Dampak:** lihat DQ-1 dan DQ-8.

### 5.3 Kasus 2: nilai order per status

| Kelompok | Nilai order (USD) | Porsi |
|---|---|---|
| Valid (`COMPLETE` + `CLOSED`) | 15.012.982,48 | 43,7% |
| Berjalan (`PENDING_PAYMENT`, `PROCESSING`, `PENDING`, `ON_HOLD`, `PAYMENT_REVIEW`) | 17.846.761,78 | 52,0% |
| Batal atau diduga fraud (`CANCELED`, `SUSPECTED_FRAUD`) | 1.462.875,67 | 4,3% |
| **Total semua status** | **34.322.619,93** | 100% |

- Nilai order adalah nilai nominal, bukan revenue terealisasi. Order tanpa item tidak ikut dihitung.
- Mean nilai order antar status 582,94 s.d. 607,34; median 529,97 s.d. 579,95; p95 1.179,91 s.d. 1.209,86. Tidak ada status yang menonjol.
- `PENDING_PAYMENT` saja bernilai 7.581.671,05 USD (±50% dari valid revenue).
- Jumlah order per bulan penuh 5.308 s.d. 6.381; 2013-07 (7 hari) 1.533 order dan 2014-07 (24 hari) 4.468 order.

### 5.4 Kasus 3: distribusi nilai order valid
- Populasi 25.266 order (valid dan punya item); mean 594,20; median 559,94; simpangan baku 344,48; persentil 25 / 75 / 95 = 299,99 / 829,96 / 1.199,92; minimum 9,99; maksimum 3.449,91.
- Skewness 0,53 (miring ke kanan moderat). 58 order (0,23%) melewati batas outlier IQR (1.624,91). Sepuluh persen order terbesar menyumbang 20,97% revenue.
- **Validasi:** jumlah order, total revenue, dan mean cocok dengan SQL; tidak ada order bernilai ≤ 0.

### 5.5 Catatan metode
- Perbandingan orphan memakai **rate di dalam tiap kelompok**, bukan hitungan mentah, karena status yang besar otomatis punya orphan lebih banyak.
- Selisih antar bulan dan status dibaca terhadap kisaran fluktuasi acak untuk ukuran kelompoknya. Perkiraan kasar: ±1 poin persentase untuk status besar pada satu bulan penuh.
- Hipotesis yang tidak didukung tetap dicatat; itu hasil sah, bukan kegagalan.


## 6. Keterbatasan dan tindak lanjut

- Pisahkan 25 kategori tanpa penjualan valid: tanpa produk sama sekali vs berproduk tetapi tidak laku.
- Periksa pemetaan produk ke kategori untuk 9 produk teratas (nama produk tampak tidak selalu sesuai namanya kategori).
- Periksa apakah nama produk terpotong 45 karakter di sumber data.
- Hitung revenue per status untuk melihat potensi revenue yang tertahan (selesai, lihat Bagian 5.3).
- Analisis retensi kohort sungguhan (Q09 baru segmentasi frekuensi).
- Minta data riwayat perubahan status order dari sumber data (di luar database ini) untuk menguji penyebab 56% order tidak selesai.
- Konfirmasi dari sumber data apakah data ini data latihan atau sintetis (dugaan dari pola tanpa keterkaitan pada DQ-9).
- Buat data mart tingkat produk jika dashboard perlu menampilkan top produk (dashboard saat ini tidak punya rincian per produk).
- Data hanya mencakup satu tahun dan satu potret status order, sehingga pola musiman dan perubahan status tidak dapat disimpulkan.


## 7. Format entri baru

Setiap temuan baru dicatat dengan: **ID, temuan, bukti (query atau angka), dampak, tindakan, status**
(Terverifikasi / Dugaan / Terbuka). Tuliskan penyebab hanya jika sudah terbukti.


## 8. Data mart untuk Looker Studio

| Mart | Granularitas | Baris | Populasi |
|---|---|---|---|
| `mart_daily_sales` | tanggal × status × kategori | 35.126 | Order yang punya item |
| `mart_customer_segments` | pelanggan | 10.844 | Pelanggan dengan order valid yang punya item |
| `mart_daily_orders` | tanggal × status | 3.203 | Semua order |

**Validasi:** tidak ada nilai kosong dan tidak ada duplikat grain; 364 hari unik; total revenue semua status 34.322.619,93 USD; total valid revenue 15.012.982,48 USD (sama dengan Q01, Q05, Q06, Q07, Q08, Q09); total unit 375.758 sama dengan `order_items`; `SUM(unique_orders)` order valid 66.103 vs 25.266 order sebenarnya (menggembung ±2,6 kali); `mart_customer_segments`: 10.844 pelanggan, 25.266 order, 15.012.982,48 USD, tiga tingkat sama dengan Q09 (3.356 / 5.664 / 1.824 pelanggan).

**Validasi file CSV (dibaca ulang dari `data/processed/`):** `mart_daily_sales.csv` 35.126 baris × 12 kolom (3,37 MB): total revenue 34.322.619,93 dan valid revenue 15.012.982,48, bulan `PARTIAL` hanya 2013-07 dan 2014-07; `mart_customer_segments.csv` 10.844 baris × 6 kolom (0,65 MB): total 15.012.982,48; `mart_daily_orders.csv` 3.203 baris × 9 kolom (0,20 MB): 68.883 total order, 57.431 order dengan item, 25.266 order valid dengan item, valid revenue 15.012.982,48, AOV 594,20. Setelah dibaca ulang, `order_date` terbaca sebagai teks dan `category_id` sebagai angka, sehingga tipenya diatur ulang di Looker Studio.

**Keputusan desain:**
- `GROUP BY` memakai ID. Kolom `category_label` dibuat unik karena dua kategori "Electronics"
  (ID 13 dan 37) akan menyatu di grafik berdasarkan `category_name`.
- `unique_orders` tidak aditif lintas kategori: `SUM` order valid = 66.103 vs 25.266 order sebenarnya. Ditangani dengan dokumentasi dan `mart_daily_orders` untuk total order dan AOV.
- Order tanpa item (11.452) tidak ada di `mart_daily_sales`.
- Bulan parsial ditandai di `month_status`.
- Mart pelanggan hanya memuat ID, tanpa data pribadi.


## 9. Dashboard Looker Studio

**Sumber data:** Google Sheets `Ecommerce_BI_Data_Marts` (3 tab dari 3 CSV mart), locale United States.

**Koreksi terhadap instruksi awal:**
- Metric order memakai `orders_with_items`. `total_orders` akan memberi 30.455 order valid dan AOV 492,96 karena ikut menghitung order tanpa item.
- Dimension kategori memakai `category_label` karena `category_name` menyatukan dua "Electronics" (bar ke-10 menjadi 161.156,40, bukan 112.141,70).
- Rentang tanggal default diset Custom (2013-07-25 s.d. 2014-07-24).
- Filter valid memakai `status_group = "1. Valid"` dan dibuat per sumber data.

**Validasi dashboard:** Valid Revenue 15.012.982,48; Valid Orders 25.266; AOV 594,20; Valid Order Share 43,99% (25.266 ÷ 57.431 order yang punya item); tren 2013-07 333.465,45, 2013-08 1.221.828,90, 2013-11 1.379.935,33, 2014-07 955.590,77 (sama dengan Query 06); bar chart #1 Fishing 3.022.248,88 dan #9 Shop By Sport 568.171,81; nilai "Others" 779.715,23 = 15.012.982,48 − 14.233.267,25 (jumlah 9 kategori teratas); setelah opsi Others dimatikan bar ke-10 = Electronics 112.141,70; tabel departemen: persentase Fan Shop 49,62% / Apparel 21,40% / Golf 13,44% / Footwear 11,87% / Outdoors 2,88% / Fitness 0,78% (berjumlah 99,99%, selisih pembulatan), jumlah revenue semua departemen = 15.012.982,48.

**Keterbatasan:** dropdown departemen tidak memengaruhi scorecard (sumber data berbeda); Valid Order Share (43,99%) dihitung dari 57.431 order yang punya item, bukan dari seluruh 68.883 order (44,21%).

**Halaman 2 (Order Status & Customer Retention):**
- Distribusi status memakai `total_orders` (68.883 order, sama dengan Query 04), bukan `orders_with_items`; `unique_orders` tidak ada di `mart_daily_orders`.
- Kolom pelanggan memakai `customer_id` (diganti dari `order_customer_id` di mart).
- Kontrol tanggal dijadikan report-level. Grafik `mart_customer_segments` memakai rentang tetap (Custom 2013-07-25 s.d. 2014-07-24), karena data tingkat pelanggan memuat total seumur hidup yang tidak bisa dipotong per tanggal.
- Kolom `revenue_usd` per status diberi nama "Nilai order (USD)" karena nilai nominal, bukan revenue terealisasi.
- Porsi valid di Halaman 1 (43,99%, dari 57.431 order ber-item) berbeda dari Halaman 2 (44,21%, dari 68.883 order); keduanya konsisten dan dicatat di halaman.
- Insight "56% order tertahan" dirinci menjadi 51,5% berjalan (nominal ±17,85 juta USD) dan 4,3% batal/fraud.

**Validasi Halaman 2:** tabel status cocok dengan Query 04 dan Kasus 2 (22.899 / 15.030 / 8.275 / 7.610 / 7.556 / 3.798 / 1.558 / 1.428 / 729; total 68.883; nilai order total 34.322.619,93 USD). Segmen pelanggan cocok dengan Query 09: 3.356 / 5.664 / 1.824 pelanggan; 3.356 / 13.645 / 8.265 order; revenue 1.990.936,12 / 8.103.491,64 / 4.918.554,72; Revenue per Customer 593,25 / 1.430,70 / 2.696,58; Revenue per Order 593,25 / 593,88 / 595,11. Grafik pelanggan tidak berubah saat kontrol tanggal dipersempit (rentang tetap berhasil).

**Validasi KPI terhadap SQL dan Python:** empat KPI Halaman 1 cocok: Valid Revenue 15.012.982,48 USD, Valid Orders 25.266, AOV 594,20 (query SQL langsung dan Python), dan Valid Order Share 43,99% (25.266 ÷ 57.431; pembilang dan penyebut dari `mart_daily_orders.csv` dan Python).

**Kendala teknis yang ditemui dan penanganannya:**
- Bar chart dengan batas 10 bar menampilkan "Others" (779.715,23 = gabungan 24 kategori terkecil). Opsi Show Others dimatikan agar sesuai dengan judul Top 10.
- Nama kategori ganda ("Electronics") disatukan oleh Looker Studio bila memakai `category_name`; dimension memakai `category_label`.
- Pembulatan: Looker Studio menghilangkan nol di belakang (`$1,221,828.9`), dan persentase departemen berjumlah 99,99%. Bukan kesalahan data; nilai tepat diverifikasi lewat penjumlahan.
- Filter bersifat per sumber data: dropdown departemen tidak memengaruhi scorecard dari `mart_daily_orders`. Disengaja untuk menghindari penghitungan ganda, dan dicatat di dashboard.

**Hasil uji Halaman 2:** grafik dan tabel pelanggan tidak berubah saat kontrol tanggal dipersempit.

**Bukti visual:** `docs/dashboard.pdf`. Tautan dashboard ada di `README.md`.