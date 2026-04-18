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
    print(f"Cookies after login: {[c.name for c in scraper.cookies]}")

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

# ---- Weight extraction helpers ----

def extract_weights_v2(xml_text):
    """Parse XMLAPIv2 thing response."""
    tr = ET.fromstring(xml_text)
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

def extract_weights_v1(xml_text):
    """Parse XMLAPIv1 boardgame response (weight is text node, not attribute)."""
    tr = ET.fromstring(xml_text)
    found = 0
    for item in tr.findall('boardgame'):
        gid = item.get('objectid')
        if gid in game_map:
            wEl = item.find('.//averageweight')
            if wEl is not None and wEl.text:
                try:
                    game_map[gid]['w'] = round(float(wEl.text), 3)
                    found += 1
                except Exception:
                    pass
    return found

def extract_weights_json(json_text, gid):
    """Parse api.geekdo.com/api/geekitems JSON response for a single game."""
    try:
        data = json.loads(json_text)
        w = None
        # Try common paths in geekdo internal API
        item = data.get('item') or (data.get('items') or [None])[0]
        if item:
            stats = item.get('stats') or item.get('statistics') or {}
            w = stats.get('avgweight') or stats.get('averageweight') or stats.get('weight')
            if w is None:
                # Try nested
                ratings = stats.get('ratings', {})
                w = ratings.get('averageweight')
        if w is not None:
            game_map[gid]['w'] = round(float(w), 3)
            return 1
    except Exception as e:
        print(f"  JSON parse error: {e}")
    return 0

# ---- Fresh sessions ----

# No-cookie session for public endpoints
fresh = req_lib.Session()
fresh.headers.update({
    'User-Agent': 'BGGCollectionFetcher/1.0',
    'Accept': 'application/xml, text/xml, */*',
})

# Session with BGG cookies (for authenticated endpoints)
authed = req_lib.Session()
authed.cookies.update({c.name: c.value for c in scraper.cookies})
authed.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/xml, text/xml, */*',
    'Referer': 'https://boardgamegeek.com/',
})

# ---- Diagnostic: probe single game with all methods ----
probe_id = ids[0]
print(f"\n--- Probing game id={probe_id} ---")
for label, sess, url in [
    ('fresh/v2/bgg',     fresh,   f'https://boardgamegeek.com/xmlapi2/thing?stats=1&id={probe_id}'),
    ('fresh/v2/geekdo',  fresh,   f'https://api.geekdo.com/xmlapi2/thing?stats=1&id={probe_id}'),
    ('fresh/v1/bgg',     fresh,   f'https://www.boardgamegeek.com/xmlapi/boardgame/{probe_id}?stats=1'),
    ('authed/v2/bgg',    authed,  f'https://boardgamegeek.com/xmlapi2/thing?stats=1&id={probe_id}'),
    ('authed/v1/bgg',    authed,  f'https://www.boardgamegeek.com/xmlapi/boardgame/{probe_id}?stats=1'),
    ('scraper/v2/bgg',   scraper, f'https://boardgamegeek.com/xmlapi2/thing?stats=1&id={probe_id}'),
    ('scraper/v1/bgg',   scraper, f'https://www.boardgamegeek.com/xmlapi/boardgame/{probe_id}?stats=1'),
]:
    try:
        resp = sess.get(url, timeout=15)
        print(f"  [{label}]: HTTP {resp.status_code}, preview={resp.text[:120]!r}")
    except Exception as e:
        print(f"  [{label}]: ERROR {e}")
    time.sleep(2)

# Also probe internal JSON API
for label, sess in [('fresh', fresh), ('authed', authed), ('scraper', scraper)]:
    url = f'https://api.geekdo.com/api/geekitems?objecttype=thing&objectid={probe_id}&subtype=boardgame&ajax=1'
    try:
        resp = sess.get(url, timeout=15)
        print(f"  [geekitems/{label}]: HTTP {resp.status_code}, preview={resp.text[:200]!r}")
    except Exception as e:
        print(f"  [geekitems/{label}]: ERROR {e}")
    time.sleep(2)

print("--- End probe ---\n")

# ---- Batch weight fetching ----
BATCH = 20
batches = [ids[i:i+BATCH] for i in range(0, len(ids), BATCH)]

for bi, batch in enumerate(batches):
    batch_ids = ','.join(batch)
    thing_text = None
    parser = None

    for label, sess, url, parse_fn in [
        ('fresh/v1/bgg',    fresh,   f'https://www.boardgamegeek.com/xmlapi/boardgame/{batch_ids}?stats=1', extract_weights_v1),
        ('authed/v1/bgg',   authed,  f'https://www.boardgamegeek.com/xmlapi/boardgame/{batch_ids}?stats=1', extract_weights_v1),
        ('scraper/v1/bgg',  scraper, f'https://www.boardgamegeek.com/xmlapi/boardgame/{batch_ids}?stats=1', extract_weights_v1),
        ('fresh/v2/bgg',    fresh,   f'https://boardgamegeek.com/xmlapi2/thing?stats=1&id={batch_ids}',     extract_weights_v2),
        ('authed/v2/bgg',   authed,  f'https://boardgamegeek.com/xmlapi2/thing?stats=1&id={batch_ids}',     extract_weights_v2),
        ('scraper/v2/bgg',  scraper, f'https://boardgamegeek.com/xmlapi2/thing?stats=1&id={batch_ids}',     extract_weights_v2),
    ]:
        try:
            resp = sess.get(url, timeout=30)
        except Exception as e:
            print(f"Thing batch {bi+1}/{len(batches)} [{label}]: ERROR {e}")
            continue

        print(f"Thing batch {bi+1}/{len(batches)} [{label}]: HTTP {resp.status_code}, preview={resp.text[:80]!r}")

        if resp.status_code == 202:
            time.sleep(10)
            resp = sess.get(url, timeout=30)
            print(f"  retry: HTTP {resp.status_code}, preview={resp.text[:80]!r}")

        root_tag = None
        if resp.status_code == 200:
            t = resp.text.strip()
            if t.startswith('<'):
                root_tag = re.search(r'<(\w+)', t)
                root_tag = root_tag.group(1) if root_tag else ''

        if resp.status_code == 200 and root_tag in ('items', 'boardgames'):
            thing_text = resp.text
            parser = parse_fn
            break

        time.sleep(2)

    if thing_text is None:
        print(f"  All methods failed for batch {bi+1}")
        time.sleep(5)
        continue

    try:
        found = parser(thing_text)
        print(f"  weights found: {found}")
    except Exception as e:
        print(f"  Parse error: {e}")
    time.sleep(5)

with open('bgg-collection.json', 'w', encoding='utf-8') as f:
    json.dump(games, f, ensure_ascii=False)

has_w = sum(1 for g in games if g['w'] > 0)
print(f"Done! {len(games)} games, {has_w} with weight data.")
