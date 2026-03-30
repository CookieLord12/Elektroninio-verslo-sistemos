# PrestaShop demo store package - Handmade jewelry

This package contains everything needed to complete the assignment with a working open-source e-commerce solution based on PrestaShop.

## Included deliverables

- Docker-based PrestaShop environment
- 20 demo products in 4 categories
- Product CSV for import
- 20 local catalog images
- Review module setup instructions
- Testing checklist and example results
- Submission report in Markdown and DOCX

## Technology stack

- PrestaShop 9 (Docker image)
- MariaDB 11
- Nginx static image server for importable product images
- CSV-based product import
- Product Comments module for reviews

## Folder structure

- `docker-compose.yml` - launches the shop, database, and image server
- `assets/product-images/` - 20 product images
- `data/categories.csv` - category list
- `data/products.csv` - master product dataset
- `data/products.import.csv` - generated import file with full image URLs
- `scripts/prepare_import.py` - rewrites image paths into absolute URLs
- `docs/report.md` - full report text
- `docs/testing-checklist.md` - functional testing checklist

## Quick start

### 1. Start the environment
```bash
docker compose up -d
```

PrestaShop will be available at `http://localhost:8080`.
Static product images will be available at `http://localhost:8081/product-images/...`.

### 2. Generate the final import CSV
```bash
python3 scripts/prepare_import.py
```

### 3. Import categories and products
In the PrestaShop admin panel:

1. Open **Advanced Parameters -> Import**.
2. Import `data/categories.csv` as categories.
3. Import `data/products.import.csv` as products.
4. Map fields using the CSV headers.
5. Verify that all products, descriptions, prices, and images were loaded.

### 4. Enable product reviews
Install the official **Product Comments** module.

Repository: `https://github.com/PrestaShop/productcomments`

Recommended workflow:
1. Open **Modules -> Module Manager**.
2. Search for **Product Comments**.
3. Install and enable the module.
4. Turn on customer ratings and comments.
5. Allow moderation if required by the assignment/testing process.

## Suggested design choices

- Theme direction: clean boutique / handmade jewelry
- Palette: ivory, gold, muted pink, soft green
- Homepage sections:
  - Hero banner
  - Featured products
  - New arrivals
  - Category highlights
  - Customer review teaser

## Assignment coverage

- 20+ products: yes
- 3+ categories: yes (4 categories)
- Open-source platform: yes (PrestaShop)
- Reviews: yes (Product Comments module)
- Report: yes (`docs/report.md` and DOCX)
- Testing section: yes
- Innovation section: yes

## Notes

- The included images are original demo visuals created specifically for the academic product catalog.
- The CSV headers are intentionally simple and suitable for manual field mapping during import.
- Default credentials in `docker-compose.yml` are for academic/demo use only.
