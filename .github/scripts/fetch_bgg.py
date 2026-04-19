import cloudscraper, json, time, os, xml.etree.ElementTree as ET

USERNAME = 'Bajomix'
BGG_USER = os.environ.get('BGG_USERNAME', '')
BGG_PASS = os.environ.get('BGG_PASSWORD', '')

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'linux', 'mobile': False}
)

if BGG_USER and BGG_PASS:
    r = scraper.post(
        'https://boardgamegeek.com/login/api/v1',
        json={"credentials": {"username": BGG_USER, "password": BGG_PASS}}
    )
    print(f"Login: {r.status_code}")

coll_url = f'https://boardgamegeek.com/xmlapi2/collection?username={USERNAME}&stats=1&own=1'
text = None
for attempt in range(6):
    r = scraper.get(coll_url)
    print(f"Collection attempt {attempt+1}: HTTP {r.status_code}, preview={r.text[:80]!r}")
    if r.status_code == 200 and '<items' in r.text:
        text = r.text
        break
    time.sleep(15)

if not text:
    raise SystemExit("Failed to fetch collection")

root = ET.fromstring(text)
games = []
for item in root.findall('item'):
    gid   = item.get('objectid')
    name  = item.find('name')
    thumb = item.find('thumbnail')
    stats = item.find('stats')
    games.append({
        'id':    gid,
        'name':  (name.text or '?').strip() if name is not None else '?',
        'thumb': (thumb.text or '').strip() if thumb is not None else '',
        'min':   int(stats.get('minplayers', 0)) if stats is not None else 0,
        'max':   int(stats.get('maxplayers', 0)) if stats is not None else 0,
        'minT':  int(stats.get('minplaytime', 0)) if stats is not None else 0,
        'maxT':  int(stats.get('maxplaytime', 0)) if stats is not None else 0,
        'w':     0.0,
    })

print(f"Parsed {len(games)} games.")

# Merge weights from weights.json (maintained locally via fetch_weights_local.py)
weights_file = 'weights.json'
if os.path.exists(weights_file):
    with open(weights_file, encoding='utf-8') as f:
        weights = json.load(f)
    merged = sum(1 for g in games if g['id'] in weights)
    for g in games:
        if g['id'] in weights:
            g['w'] = weights[g['id']]
    print(f"Merged weights for {merged}/{len(games)} games from {weights_file}.")
else:
    print("weights.json not found — weights will be 0. Run fetch_weights_local.py locally.")

with open('bgg-collection.json', 'w', encoding='utf-8') as f:
    json.dump(games, f, ensure_ascii=False)

has_w = sum(1 for g in games if g['w'] > 0)
print(f"Done! {len(games)} games, {has_w} with weight data.")
