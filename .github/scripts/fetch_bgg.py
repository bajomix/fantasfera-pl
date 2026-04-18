import cloudscraper, json, time, os, re, xml.etree.ElementTree as ET
import requests as req_lib

USERNAME = 'Bajomix'
BGG_USER = os.environ.get('BGG_USERNAME', '')
BGG_PASS = os.environ.get('BGG_PASSWORD', '')

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'linux', 'mobile': False}
)

# Login
if BGG_USER and BGG_PASS:
    print("Logging in...")
    r = scraper.post(
        'https://boardgamegeek.com/login/api/v1',
        json={"credentials": {"username": BGG_USER, "password": BGG_PASS}}
    )
    print(f"Login status: {r.status_code}")

# Fetch collection (with retry for BGG 202)
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

# Parse collection
root = ET.fromstring(text)
games, ids = [], []
for item in root.findall('item'):
    gid   = item.get('objectid')
    name  = item.find('name')
    thumb = item.find('thumbnail')
    stats = item.find('stats')
    ids.append(gid)
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
game_map = {g['id']: g for g in games}
print(f"Parsed {len(games)} games. Fetching weights via geekitems API...")

# Fresh session (geekitems API is public)
fresh = req_lib.Session()
fresh.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, */*',
    'Referer': 'https://boardgamegeek.com/',
})

def find_weight_in_dict(d, depth=0):
    """Recursively search for weight-related fields in a dict."""
    if depth > 5 or not isinstance(d, dict):
        return None
    for k, v in d.items():
        if 'weight' in k.lower() and isinstance(v, (int, float, str)):
            try:
                w = float(v)
                if 0 < w <= 5:
                    return w
            except (ValueError, TypeError):
                pass
        if isinstance(v, dict):
            result = find_weight_in_dict(v, depth + 1)
            if result is not None:
                return result
    return None

# Probe first game to understand JSON structure
probe_id = ids[0]
probe_url = f'https://api.geekdo.com/api/geekitems?objecttype=thing&objectid={probe_id}&subtype=boardgame&ajax=1'
probe_resp = fresh.get(probe_url, timeout=15)
print(f"\nProbe game {probe_id}: HTTP {probe_resp.status_code}")
if probe_resp.status_code == 200:
    probe_data = probe_resp.json()
    probe_item = probe_data.get('item', {})
    probe_stats = probe_item.get('stats', {})
    print(f"  stats keys: {list(probe_stats.keys())}")
    print(f"  stats content: {json.dumps(probe_stats, indent=2)[:500]}")
    w = find_weight_in_dict(probe_data)
    print(f"  auto-detected weight: {w}")
time.sleep(2)

# Fetch weights for all games
weights_found = 0
errors = 0

for i, gid in enumerate(ids):
    url = f'https://api.geekdo.com/api/geekitems?objecttype=thing&objectid={gid}&subtype=boardgame&ajax=1'
    try:
        resp = fresh.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            item = data.get('item', {})
            stats = item.get('stats', {})
            # Try known field names first
            w = (stats.get('avgweight')
                 or stats.get('averageweight')
                 or stats.get('weight'))
            # Fall back to recursive search
            if w is None:
                w = find_weight_in_dict(data)
            if w is not None:
                try:
                    wf = float(w)
                    if 0 < wf <= 5:
                        game_map[gid]['w'] = round(wf, 3)
                        weights_found += 1
                except (ValueError, TypeError):
                    pass
        else:
            errors += 1
            if errors <= 3:
                print(f"  Game {gid}: HTTP {resp.status_code}")
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f"  Game {gid}: ERROR {e}")

    if (i + 1) % 10 == 0 or i == len(ids) - 1:
        print(f"  Progress: {i+1}/{len(ids)}, weights={weights_found}, errors={errors}")
    time.sleep(1.5)

with open('bgg-collection.json', 'w', encoding='utf-8') as f:
    json.dump(games, f, ensure_ascii=False)

has_w = sum(1 for g in games if g['w'] > 0)
print(f"\nDone! {len(games)} games, {has_w} with weight data.")
