# Data Portfolio

Kumpulan portfolio data yang saya bangun selama proses belajar.

## Portfolio

| # | Portfolio | Tools | Status |
|---|---|---|---|
| 1 | [E-Commerce Sales & Customer Analysis](01-sql-ecommerce-analysis/) | SQL, PostgreSQL, Python (Pandas), Google Sheets, Looker Studio | Selesai |
| 2 | Python Data Processing | Python, Pandas, PostgreSQL | Selesai |

## E-Commerce Sales & Customer Analysis

Analisis 68.883 order e-commerce (Jul 2013 – Jul 2014) dari database PostgreSQL sampai dashboard Looker Studio.

- **Masalah bisnis:** dari mana revenue datang, berapa order yang benar-benar menjadi revenue, pelanggan mana yang paling bernilai, dan seberapa dapat dipercaya angkanya.
- **Yang saya kerjakan:** audit dan perbaikan 9 query SQL (CTE, window function), investigasi dan uji hipotesis di Python, tiga data mart, dan dashboard dua halaman.
- **Temuan utama:**
  - Valid revenue **15.012.982,48 USD**; 7 dari 33 kategori menghasilkan **82,64%**.
  - Hanya **44,2%** order berstatus valid (`COMPLETE` dan `CLOSED`).
  - Pelanggan berulang = **69,05%** pelanggan tetapi **86,74%** revenue.
  - **16,63%** order tidak punya item (11.452 order).
- **Yang membedakan:** setiap angka utama divalidasi lewat minimal dua jalur berbeda (SQL, Python, dan dashboard), dan setiap masalah data dicatat beserta dampaknya.

## Tentang Saya

Fresh Graduate Teknik Informatika yang sedang membangun karier di bidang data.

**Skills:**
- SQL (PostgreSQL): SELECT, JOIN, GROUP BY, HAVING, subquery, CTE, window function
- Python: Pandas, SQLAlchemy, Jupyter Notebook
- Visualisasi dan BI: Looker Studio, Google Sheets, seaborn
- Dokumentasi data: audit log, kamus data, insight bisnis
- Tools: Git, GitHub, Antigravity IDE, pgAdmin

**Kontak:**
- LinkedIn: [linkedin.com/in/muhammad-alif-syafan](https://www.linkedin.com/in/muhammad-alif-syafan)
- Email: [muhalifsyafan@gmail.com](mailto:muhalifsyafan@gmail.com)