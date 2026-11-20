import cloudscraper, json, time, os, xml.etree.ElementTree as ET

USERNAME = 'Bajomix'
BGG_USER = os.environ.get('BGG_USERNAME', '')
BGG_PASS = os.environ.get('BGG_PASSWORD', '')
BGG_TOKEN = os.environ.get('BGG_API_TOKEN', '')

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'linux', 'mobile': False}
)

if BGG_TOKEN:
    # Since autumn 2025 BGG requires a registered application token for XML API
    # (https://boardgamegeek.com/applications). This avoids the login flow, which
    # BGG often blocks (403) from GitHub Actions IPs.
    scraper.headers['Authorization'] = f'Bearer {BGG_TOKEN}'
    print("Using BGG_API_TOKEN (Bearer auth).")
elif BGG_USER and BGG_PASS:
    print("WARNING: BGG_API_TOKEN not set, falling back to login (unreliable from CI).")
    for attempt in range(3):
        r = scraper.post(
            'https://boardgamegeek.com/login/api/v1',
            json={"credentials": {"username": BGG_USER, "password": BGG_PASS}}
        )
        print(f"Login attempt {attempt+1}: {r.status_code}")
        if r.status_code in (200, 204):
            break
        time.sleep(20)

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
        'name':  ' '.join((name.text or '?').split()) if name is not None else '?',
        'thumb': (thumb.text or '').strip() if thumb is not None else '',
        'min':   int(stats.get('minplayers', 0)) if stats is not None else 0,
        'max':   int(stats.get('maxplayers', 0)) if stats is not None else 0,
        'minT':  int(stats.get('minplaytime', 0)) if stats is not None else 0,
        'maxT':  int(stats.get('maxplaytime', 0)) if stats is not None else 0,
        'w':     0.0,
    })

print(f"Parsed {len(games)} games.")

# The collection XML marks expansions as subtype="boardgame", so fetch the
# expansion IDs with a separate request. If that fails, keep the flags from
# the previous bgg-collection.json (also set from CSV by the local scripts).
exp_ids = None
exp_url = f'https://boardgamegeek.com/xmlapi2/collection?username={USERNAME}&own=1&subtype=boardgameexpansion'
for attempt in range(4):
    r = scraper.get(exp_url)
    print(f"Expansions attempt {attempt+1}: HTTP {r.status_code}")
    if r.status_code == 200 and '<items' in r.text:
        exp_ids = {it.get('objectid') for it in ET.fromstring(r.text).findall('item')}
        break
    time.sleep(10)

if exp_ids is None:
    exp_ids = set()
    if os.path.exists('bgg-collection.json'):
        with open('bgg-collection.json', encoding='utf-8') as f:
            exp_ids = {g['id'] for g in json.load(f) if g.get('exp')}
    print(f"Expansion fetch failed, reusing {len(exp_ids)} flags from previous data.")

for g in games:
    if g['id'] in exp_ids:
        g['exp'] = True
print(f"Marked {sum(1 for g in games if g.get('exp'))} expansions.")

# Difficulty weights. weights.json is a cache ({id: weight}) that also holds
# manual values for games BGG has no weight for yet (e.g. Dylematy 2).
weights_file = 'weights.json'
weights = {}
if os.path.exists(weights_file):
    with open(weights_file, encoding='utf-8') as f:
        weights = json.load(f)

# With an application token, fetch current averageweight from the thing API
# (max 20 ids per request). A real BGG value (> 0) overrides the cache.
if BGG_TOKEN:
    ids = [g['id'] for g in games]
    updated = 0
    for i in range(0, len(ids), 20):
        batch = ids[i:i + 20]
        url = f"https://boardgamegeek.com/xmlapi2/thing?id={','.join(batch)}&stats=1"
        for attempt in range(4):
            r = scraper.get(url)
            if r.status_code == 200 and '<items' in r.text:
                break
            print(f"Thing batch {i // 20 + 1} attempt {attempt+1}: HTTP {r.status_code}")
            time.sleep(10)
        else:
            print(f"Thing batch {i // 20 + 1} failed, keeping cached weights.")
            continue
        for item in ET.fromstring(r.text).findall('item'):
            aw = item.find('statistics/ratings/averageweight')
            try:
                w = round(float(aw.get('value')), 3) if aw is not None else 0.0
            except (TypeError, ValueError):
                w = 0.0
            if w > 0 and weights.get(item.get('id')) != w:
                weights[item.get('id')] = w
                updated += 1
        time.sleep(3)  # be gentle with the API
    print(f"Fetched weights from BGG, {updated} changed.")
    with open(weights_file, 'w', encoding='utf-8') as f:
        json.dump(weights, f, ensure_ascii=False, indent=2, sort_keys=True)

merged = 0
for g in games:
    if g['id'] in weights:
        g['w'] = weights[g['id']]
        merged += 1
print(f"Weights for {merged}/{len(games)} games.")

# Expansions without their own BGG weight inherit the weight of their base
# game, matched by name prefix ("Revenant: Reason and Faith" -> "Revenant").
bases = sorted((g for g in games if not g.get('exp') and g['w'] > 0), key=lambda g: -len(g['name']))
for g in games:
    if g.get('exp') and not g['w']:
        for b in bases:
            if g['name'].startswith(b['name']) and g['name'][len(b['name']):][:2] in (': ', ' –', ' -', ' ('):
                g['w'] = b['w']
                print(f"Expansion '{g['name']}' inherits weight {b['w']} from '{b['name']}'.")
                break

with open('bgg-collection.json', 'w', encoding='utf-8') as f:
    json.dump(games, f, ensure_ascii=False)

has_w = sum(1 for g in games if g['w'] > 0)
print(f"Done! {len(games)} games, {has_w} with weight data.")
