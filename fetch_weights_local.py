#!/usr/bin/env python3
"""
Extracts game weights from BGG collection CSV export.
Run this locally to regenerate weights.json from your BGG CSV export.

How to get the CSV:
    1. Go to https://boardgamegeek.com/collection/user/<your_username>
    2. Export → Download as CSV
    3. Run: python3 fetch_weights_local.py <collection.csv>

Usage:
    python3 fetch_weights_local.py <collection.csv>
"""
import json, csv, sys, os

if len(sys.argv) < 2:
    raise SystemExit("Usage: python3 fetch_weights_local.py <collection.csv>")

CSV_FILE     = sys.argv[1]
WEIGHTS_FILE = 'weights.json'

if not os.path.exists(CSV_FILE):
    raise SystemExit(f"File not found: {CSV_FILE}")

weights = {}
if os.path.exists(WEIGHTS_FILE):
    with open(WEIGHTS_FILE, encoding='utf-8') as f:
        weights = json.load(f)
    print(f"Loaded {len(weights)} existing weights from {WEIGHTS_FILE}")

added = 0
with open(CSV_FILE, encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        gid = row.get('objectid', '').strip()
        if not gid:
            continue
        raw = row.get('avgweight') or row.get('complexity') or ''
        try:
            w = round(float(raw), 3)
        except ValueError:
            continue
        if 0 < w <= 5:
            weights[gid] = w
            added += 1

with open(WEIGHTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(weights, f, ensure_ascii=False, indent=2, sort_keys=True)

print(f"Done! {added} weights saved to {WEIGHTS_FILE}")
print("Now run: git add weights.json && git commit -m 'Update game weights' && git push")
