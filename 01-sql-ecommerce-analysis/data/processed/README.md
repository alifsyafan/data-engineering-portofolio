# Data Mart untuk Looker Studio

Dibuat oleh `notebooks/01_eda_and_mart_prep.ipynb` dari 6 tabel PostgreSQL.
Satuan uang: USD (diasumsikan dari format harga; tidak ada konversi).
Definisi valid revenue: order berstatus `COMPLETE` atau `CLOSED`.

## 1. `mart_daily_sales.csv`

**Granularitas:** satu baris = satu tanggal × satu status × satu kategori.
**Populasi:** hanya order yang punya item. 11.452 order tanpa item (16,63%) tidak ada di file ini, sehingga jumlah order di sini tidak sama dengan Query 04 (68.883 order).
**Jumlah baris:** 35.126 (mart_daily_sales), 10.844 (mart_customer_segments), dan 3.203 (mart_daily_orders).

| Kolom | Tipe | Arti |
|---|---|---|
| `order_date` | tanggal | Tanggal order (`yyyy-mm-dd`) |
| `month_status` | teks | `FULL` atau `PARTIAL`. Bulan parsial: 2013-07 (7 hari) dan 2014-07 (24 hari) |
| `order_status` | teks | Status asli (9 nilai) |
| `status_group` | teks | `1. Valid`, `2. Berjalan`, `3. Batal/Fraud` |
| `is_valid_revenue` | boolean | `True` jika status `COMPLETE` atau `CLOSED` |
| `department_name` | teks | Nama departemen |
| `category_id` | angka (ID) | Kunci kategori. Perlakukan sebagai teks/dimensi, bukan angka yang dijumlahkan |
| `category_name` | teks | Nama kategori. **Tidak unik**: "Electronics" dipakai ID 13 dan 37 |
| `category_label` | teks | Nama kategori yang unik. **Pakai ini sebagai dimensi di dashboard** |
| `unique_orders` | angka | Jumlah order unik dalam baris tersebut |
| `total_units` | angka | Jumlah unit terjual |
| `revenue_usd` | angka | Jumlah `order_item_subtotal` |

### Aturan penjumlahan

- `revenue_usd` dan `total_units` **aditif**: aman dijumlahkan lintas dimensi mana pun.
- **`unique_orders` TIDAK boleh dijumlahkan lintas kategori.** Satu order yang memuat produk dari dua kategori dihitung 1 di masing-masing kategori. Pada order valid, `SUM(unique_orders)`
  = 66.103, padahal jumlah order valid sebenarnya 25.266 (menggembung ±2,6 kali).
  Aman hanya jika grafik dirinci per kategori atau difilter ke satu kategori.
  Tidak aman untuk total keseluruhan, per bulan tanpa rincian kategori, per departemen, atau per status.
- Untuk total order dan AOV, pakai `mart_daily_orders.csv`.
- Rasio dan rata-rata tidak disimpan. Hitung di dashboard sebagai rasio dua penjumlahan.

## 2. `mart_customer_segments.csv`

**Granularitas:** satu baris = satu pelanggan.
**Populasi:** pelanggan yang punya minimal satu order valid dengan item (10.844 dari 12.435 pelanggan).
**Jumlah baris:** 35.126 (mart_daily_sales), 10.844 (mart_customer_segments), dan 3.203 (mart_daily_orders).

| Kolom | Tipe | Arti |
|---|---|---|
| `customer_id` | angka (ID) | ID pelanggan. Perlakukan sebagai teks/dimensi. Tanpa nama atau data pribadi |
| `retention_tier` | teks | `1. One-time Buyer (1x)`, `2. Repeat Buyer (2-3x)`, `3. Loyal Buyer (4x+)` |
| `order_count` | angka | Jumlah order valid yang punya item |
| `total_revenue_usd` | angka | Total valid revenue pelanggan |
| `first_order_date`, `last_order_date` | tanggal | Tanggal order valid pertama dan terakhir |

Catatan: segmentasi frekuensi pembelian dalam ±1 tahun, bukan retensi kohort. Pelanggan yang baru
bergabung di akhir periode punya waktu lebih sedikit untuk membeli ulang.

## 3. `mart_daily_orders.csv`

**Granularitas:** satu baris = satu tanggal × satu status.
`total_orders` menghitung semua order (68.883 total, termasuk yang tanpa item);
`orders_with_items` adalah penyebut AOV.
AOV = `SUM(revenue_usd) / SUM(orders_with_items)` pada order valid ≈ 594,20 USD.

## Keterbatasan

- Tidak ada order pada 2014-03-09, sehingga grafik harian akan punya satu celah.
- Tidak ada rincian per produk, per jam, atau per pelanggan di `mart_daily_sales`.
- Satu tahun data: pola musiman tidak dapat disimpulkan.
- Nilai order adalah nilai nominal, bukan revenue terealisasi.

## Cara membuat ulang

Jalankan notebook dari awal (Restart kernel and run all). Kredensial database dibaca dari `.env`.