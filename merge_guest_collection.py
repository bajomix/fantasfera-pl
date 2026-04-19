#!/usr/bin/env python3
"""
Merge a friend's BGG collection CSV into bgg-collection.json.
Only adds games not already in the collection (deduplicated by objectid).

Usage:
    python3 merge_guest_collection.py <friend.csv>
"""
import json, csv, sys, time, os, xml.etree.ElementTree as ET
import requests

if len(sys.argv) < 2:
    raise SystemExit("Usage: python3 merge_guest_collection.py <friend.csv>")

CSV_FILE       = sys.argv[1]
COLLECTION_FILE = 'bgg-collection.json'
WEIGHTS_FILE   = 'weights.json'

if not os.path.exists(CSV_FILE):
    raise SystemExit(f"File not found: {CSV_FILE}")
if not os.path.exists(COLLECTION_FILE):
    raise SystemExit(f"'{COLLECTION_FILE}' not found — run the GitHub Action first.")

# Load existing collection
with open(COLLECTION_FILE, encoding='utf-8') as f:
    games = json.load(f)
existing_ids = {g['id'] for g in games}
print(f"Your collection: {len(games)} games")

# Load existing weights
weights = {}
if os.path.exists(WEIGHTS_FILE):
    with open(WEIGHTS_FILE, encoding='utf-8') as f:
        weights = json.load(f)

# Parse friend's CSV — collect only new games
new_games = []
skipped = 0
with open(CSV_FILE, encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        gid = row.get('objectid', '').strip()
        if not gid:
            continue
        if gid in existing_ids:
            skipped += 1
            continue
        try:
            w = round(float(row.get('avgweight') or 0), 3)
        except ValueError:
            w = 0.0
        new_games.append({
            'id':   gid,
            'name': (row.get('objectname') or '?').strip(),
            'min':  int(row.get('minplayers') or 0),
            'max':  int(row.get('maxplayers') or 0),
            'minT': int(row.get('minplaytime') or 0),
            'maxT': int(row.get('maxplaytime') or 0),
            'w':    w,
            'thumb': '',
        })

print(f"Friend's CSV: {len(new_games)} new games, {skipped} already in your collection")

if not new_games:
    print("Nothing to add.")
    sys.exit(0)

# Try to fetch thumbnails from BGG thing API (no stats= param)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/xml, text/xml, */*',
})

game_map = {g['id']: g for g in new_games}
ids = list(game_map.keys())
BATCH = 20
batches = [ids[i:i+BATCH] for i in range(0, len(ids), BATCH)]

print("Fetching thumbnails from BGG...")
for bi, batch in enumerate(batches):
    url = f'https://boardgamegeek.com/xmlapi2/thing?id={",".join(batch)}'
    try:
        resp = session.get(url, timeout=20)
        print(f"  Batch {bi+1}/{len(batches)}: HTTP {resp.status_code}")
        if resp.status_code == 200 and '<items' in resp.text:
            for item in ET.fromstring(resp.text).findall('item'):
                gid = item.get('id')
                if gid in game_map:
                    t = item.find('thumbnail')
                    if t is not None and t.text:
                        game_map[gid]['thumb'] = t.text.strip()
        elif resp.status_code == 401:
            print("  BGG blocked — thumbnails will be empty (game data still added)")
            break
    except Exception as e:
        print(f"  Error: {e}")
    time.sleep(2)

# Update weights.json with new games that have weight data
added_weights = 0
for g in new_games:
    if g['w'] > 0:
        weights[g['id']] = g['w']
        added_weights += 1

# Merge and sort alphabetically
games.extend(new_games)
games.sort(key=lambda g: g['name'].lower())

# Save
with open(COLLECTION_FILE, 'w', encoding='utf-8') as f:
    json.dump(games, f, ensure_ascii=False)
with open(WEIGHTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(weights, f, ensure_ascii=False, indent=2, sort_keys=True)

thumbs = sum(1 for g in new_games if g['thumb'])
print(f"\nAdded {len(new_games)} games ({thumbs} with thumbnail, {added_weights} with weight)")
print(f"Total collection: {len(games)} games")
print(f"\nNow run:")
print(f"  git add bgg-collection.json weights.json")
print(f"  git commit -m 'Add friend collection from {os.path.basename(CSV_FILE)}'")
print(f"  git push")
