#!/usr/bin/env python3
"""
Run this script locally (not in CI) to fetch game weights from BGG.
BGG XML API works fine from home IPs — saves weights.json to repo.

Usage:
    python3 fetch_weights_local.py
"""
import json, time, xml.etree.ElementTree as ET, os
import requests

COLLECTION_FILE = 'bgg-collection.json'
WEIGHTS_FILE = 'weights.json'

if not os.path.exists(COLLECTION_FILE):
    raise SystemExit(f"'{COLLECTION_FILE}' not found. Run the GitHub Action first to generate it.")

with open(COLLECTION_FILE, encoding='utf-8') as f:
    games = json.load(f)

ids = [g['id'] for g in games]
print(f"Loaded {len(ids)} games from {COLLECTION_FILE}")

# Load existing weights (preserve any already fetched)
weights = {}
if os.path.exists(WEIGHTS_FILE):
    with open(WEIGHTS_FILE, encoding='utf-8') as f:
        weights = json.load(f)
    print(f"Loaded {len(weights)} existing weights from {WEIGHTS_FILE}")

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/xml, text/xml, */*',
})

BATCH = 20
batches = [ids[i:i+BATCH] for i in range(0, len(ids), BATCH)]
total_found = 0

for bi, batch in enumerate(batches):
    batch_ids = ','.join(batch)
    url = f'https://boardgamegeek.com/xmlapi2/thing?stats=1&id={batch_ids}'
    thing_text = None

    for attempt in range(4):
        try:
            resp = session.get(url, timeout=30)
        except Exception as e:
            print(f"  Batch {bi+1} error: {e}")
            time.sleep(5)
            continue

        print(f"Batch {bi+1}/{len(batches)} attempt {attempt+1}: HTTP {resp.status_code}")

        if resp.status_code == 200 and '<items' in resp.text:
            thing_text = resp.text
            break
        if resp.status_code == 202:
            print("  BGG queuing request, waiting 15s...")
            time.sleep(15)
            continue
        time.sleep(5)

    if thing_text is None:
        print(f"  Batch {bi+1} failed — skipping")
        continue

    try:
        tr = ET.fromstring(thing_text)
        found = 0
        for item in tr.findall('item'):
            gid = item.get('id')
            wEl = item.find('.//averageweight')
            if wEl is not None:
                try:
                    w = round(float(wEl.get('value', 0) or 0), 3)
                    if w > 0:
                        weights[gid] = w
                        found += 1
                except Exception:
                    pass
        total_found += found
        print(f"  weights found: {found}")
    except Exception as e:
        print(f"  Parse error: {e}")

    time.sleep(2)

with open(WEIGHTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(weights, f, ensure_ascii=False, indent=2, sort_keys=True)

print(f"\nDone! {total_found} weights fetched. Total in weights.json: {len(weights)}")
print(f"Now commit and push weights.json to the repo.")
