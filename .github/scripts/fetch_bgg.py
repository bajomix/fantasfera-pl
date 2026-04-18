import cloudscraper, json, time, os, re, xml.etree.ElementTree as ET

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

# Try to extract Bearer token from BGG page (needed for thing API)
bearer_token = None
try:
    page = scraper.get('https://boardgamegeek.com/')
    match = re.search(r'"(?:accessToken|access_token|token|jwt)"\s*:\s*"(eyJ[A-Za-z0-9._-]+)"', page.text)
    if match:
        bearer_token = match.group(1)
        print(f"Bearer token found (len={len(bearer_token)})")
        scraper.headers.update({'Authorization': f'Bearer {bearer_token}'})
    else:
        print(f"No Bearer token in page. Cookies: {[c.name for c in scraper.cookies]}")
except Exception as e:
    print(f"Bearer extraction error: {e}")

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
print(f"Parsed {len(games)} games. Fetching weights...")

# Fetch weights
import requests as req_lib

# Fresh session — no cookies, no auth (thing API is public)
fresh = req_lib.Session()
fresh.headers.update({
    'User-Agent': 'python-requests/2.31.0',
    'Accept': 'application/xml, text/xml, */*',
})

def extract_weights(thing_text):
    tr = ET.fromstring(thing_text)
    found = 0
    for item in tr.findall('item'):
        gid = item.get('id')
        if gid in game_map:
            wEl = item.find('.//averageweight')
            if wEl is not None:
                try:
                    game_map[gid]['w'] = round(float(wEl.get('value', 0) or 0), 3)
                    found += 1
                except Exception:
                    pass
    return found

BATCH = 20
batches = [ids[i:i+BATCH] for i in range(0, len(ids), BATCH)]

for bi, batch in enumerate(batches):
    batch_ids = ','.join(batch)
    thing_text = None

    for label, sess, url in [
        ('fresh/bgg',        fresh,   f'https://boardgamegeek.com/xmlapi2/thing?stats=1&id={batch_ids}'),
        ('fresh/geekdo',     fresh,   f'https://api.geekdo.com/xmlapi2/thing?stats=1&id={batch_ids}'),
        ('cloudscraper/bgg', scraper, f'https://boardgamegeek.com/xmlapi2/thing?stats=1&id={batch_ids}'),
    ]:
        resp = sess.get(url)
        print(f"Thing batch {bi+1}/{len(batches)} [{label}]: HTTP {resp.status_code}, preview={resp.text[:80]!r}")
        if resp.status_code == 200 and '<items' in resp.text:
            thing_text = resp.text
            break
        if resp.status_code == 202:
            time.sleep(10)
            resp = sess.get(url)
            print(f"  retry: HTTP {resp.status_code}, preview={resp.text[:80]!r}")
            if resp.status_code == 200 and '<items' in resp.text:
                thing_text = resp.text
                break

    if thing_text is None:
        print(f"  All methods failed for batch {bi+1}")
        time.sleep(5)
        continue
    try:
        found = extract_weights(thing_text)
        print(f"  weights found: {found}")
    except Exception as e:
        print(f"  Parse error: {e}")
    time.sleep(5)

with open('bgg-collection.json', 'w', encoding='utf-8') as f:
    json.dump(games, f, ensure_ascii=False)

has_w = sum(1 for g in games if g['w'] > 0)
print(f"Done! {len(games)} games, {has_w} with weight data.")
