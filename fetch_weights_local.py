#!/usr/bin/env python3
"""
Fetches game weights from BGG game pages using Playwright.
Run this locally (once) to generate weights.json.

Usage:
    python3 fetch_weights_local.py
"""
import json, re, os
from playwright.sync_api import sync_playwright

COLLECTION_FILE = 'bgg-collection.json'
WEIGHTS_FILE = 'weights.json'

if not os.path.exists(COLLECTION_FILE):
    raise SystemExit(f"'{COLLECTION_FILE}' not found. Run the GitHub Action first.")

with open(COLLECTION_FILE, encoding='utf-8') as f:
    games = json.load(f)

# Load existing weights (preserve already fetched)
weights = {}
if os.path.exists(WEIGHTS_FILE):
    with open(WEIGHTS_FILE, encoding='utf-8') as f:
        weights = json.load(f)
    print(f"Loaded {len(weights)} existing weights from {WEIGHTS_FILE}")

to_fetch = [g for g in games if g['id'] not in weights]
print(f"Need to fetch weights for {len(to_fetch)}/{len(games)} games\n")

if not to_fetch:
    print("All weights already fetched!")
else:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page()

        for i, g in enumerate(to_fetch):
            gid = g['id']
            url = f'https://boardgamegeek.com/boardgame/{gid}'
            try:
                page.goto(url, timeout=30000, wait_until='domcontentloaded')
                page.wait_for_timeout(3000)

                # Weight data is embedded in the page HTML as JSON
                html = page.content()

                # BGG embeds game data in page source
                match = re.search(r'"averageweight"\s*:\s*\{\s*"value"\s*:\s*"([0-9.]+)"', html)
                if not match:
                    match = re.search(r'"averageweight"\s*:\s*([0-9.]+)', html)
                if not match:
                    # Try page text for "X.XX / 5" weight display
                    text = page.inner_text('body')
                    match = re.search(r'(?:Weight|Complexity)[^\d]*([1-4]\.[0-9]{1,4})\s*/\s*5', text)

                if match:
                    w = round(float(match.group(1)), 3)
                    if 0 < w <= 5:
                        weights[gid] = w
                        print(f"[{i+1}/{len(to_fetch)}] {g['name']}: {w}")
                    else:
                        print(f"[{i+1}/{len(to_fetch)}] {g['name']}: invalid value {w}")
                else:
                    print(f"[{i+1}/{len(to_fetch)}] {g['name']}: weight not found")

            except Exception as e:
                print(f"[{i+1}/{len(to_fetch)}] {g['name']}: ERROR {e}")

            # Save after each game (so progress isn't lost on interrupt)
            with open(WEIGHTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(weights, f, ensure_ascii=False, indent=2, sort_keys=True)

        browser.close()

print(f"\nDone! {len(weights)}/{len(games)} weights saved to {WEIGHTS_FILE}")
print("Now run: git add weights.json && git commit -m 'Add game weights' && git push")
