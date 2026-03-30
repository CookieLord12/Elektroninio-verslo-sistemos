#!/usr/bin/env python3
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'data' / 'products.csv'
outfile = ROOT / 'data' / 'products.import.csv'
base_url = os.environ.get('IMAGE_BASE_URL', 'http://localhost:8081/product-images').rstrip('/')

with source.open('r', encoding='utf-8', newline='') as src, outfile.open('w', encoding='utf-8', newline='') as dst:
    reader = csv.DictReader(src, delimiter=';')
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(dst, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    for row in reader:
        image_path = row['Image URLs (x,y,z...)'].split('/')[-1]
        row['Image URLs (x,y,z...)'] = f'{base_url}/{image_path}'
        writer.writerow(row)

print(f'Prepared {outfile}')
