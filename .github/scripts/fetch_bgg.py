import cloudscraper, json, time, os, xml.etree.ElementTree as ET
import requests as req_lib
from playwright.sync_api import sync_playwright

USERNAME = 'Bajomix'
BGG_USER = os.environ.get('BGG_USERNAME', '')
BGG_PASS = os.environ.get('BGG_PASSWORD', '')

# ── Step 1: get Bearer JWT via Playwright ─────────────────────────────────────

def get_bearer_token(user, password, probe_id):
    captured = {'token': None}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        def on_request(request):
            if captured['token']:
                return
            auth = request.headers.get('authorization', '')
            if auth.startswith('Bearer eyJ'):
                captured['token'] = auth[7:]
                print(f"  Token captured from {request.url[:70]!r} (len={len(captured['token'])})")

        page.on('request', on_request)

        # Login via form
        try:
            print("Playwright: loading login page…")
            page.goto('https://boardgamegeek.com/login',
                      timeout=40000, wait_until='domcontentloaded')
            page.wait_for_timeout(2000)

            for sel in ['#inputUsername', 'input[name="username"]', 'input[type="text"]']:
                try:
                    page.fill(sel, user, timeout=3000)
                    print(f"  Filled username via {sel!r}")
                    break
                except Exception:
                    pass

            for sel in ['#inputPassword', 'input[name="password"]', 'input[type="password"]']:
                try:
                    page.fill(sel, password, timeout=3000)
                    print(f"  Filled password via {sel!r}")
                    break
                except Exception:
                    pass

            for sel in ['button[type="submit"]', 'input[type="submit"]', 'button.btn-primary']:
                try:
                    page.click(sel, timeout=3000)
                    print(f"  Clicked submit via {sel!r}")
                    break
                except Exception:
                    pass

            page.wait_for_timeout(4000)
            print(f"  Post-login URL: {page.url}")
        except Exception as e:
            print(f"  Login error: {e}")

        # Navigate to game page to trigger authenticated API requests
        if not captured['token']:
            print(f"Playwright: loading game page {probe_id}…")
            try:
                page.goto(f'https://boardgamegeek.com/boardgame/{probe_id}',
                          timeout=40000, wait_until='domcontentloaded')
                page.wait_for_timeout(6000)
            except Exception as e:
                print(f"  Game page error: {e}")

        # Try user page as last resort
        if not captured['token']:
            print(f"Playwright: loading user page…")
            try:
                page.goto(f'https://boardgamegeek.com/user/{user}',
                          timeout=40000, wait_until='domcontentloaded')
                page.wait_for_timeout(4000)
            except Exception as e:
                print(f"  User page error: {e}")

        browser.close()

    return captured['token']


print("=== Getting Bearer token via Playwright ===")
bearer_token = get_bearer_token(BGG_USER, BGG_PASS, '174430')
if bearer_token:
    print(f"Bearer token: OK (len={len(bearer_token)})")
else:
    print("Bearer token: NOT FOUND — weights will be 0")

# ── Step 2: fetch collection (cloudscraper + session cookies) ─────────────────

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'linux', 'mobile': False}
)
if BGG_USER and BGG_PASS:
    r = scraper.post(
        'https://boardgamegeek.com/login/api/v1',
        json={"credentials": {"username": BGG_USER, "password": BGG_PASS}}
    )
    print(f"Collection login: {r.status_code}")

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
print(f"Parsed {len(games)} games.")

# ── Step 3: fetch weights via thing API with Bearer token ─────────────────────

api = req_lib.Session()
api.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/xml, text/xml, */*',
    'Referer': 'https://boardgamegeek.com/',
})
if bearer_token:
    api.headers['Authorization'] = f'Bearer {bearer_token}'

def extract_weights(xml_text):
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

print("Fetching weights…")
BATCH = 20
batches = [ids[i:i+BATCH] for i in range(0, len(ids), BATCH)]

for bi, batch in enumerate(batches):
    batch_ids = ','.join(batch)
    url = f'https://boardgamegeek.com/xmlapi2/thing?stats=1&id={batch_ids}'
    thing_text = None

    for attempt in range(3):
        try:
            resp = api.get(url, timeout=30)
        except Exception as e:
            print(f"  Batch {bi+1} request error: {e}")
            time.sleep(5)
            continue

        print(f"  Batch {bi+1}/{len(batches)} attempt {attempt+1}: "
              f"HTTP {resp.status_code}, preview={resp.text[:80]!r}")

        if resp.status_code == 200 and '<items' in resp.text:
            thing_text = resp.text
            break
        if resp.status_code == 202:
            time.sleep(12)
            continue
        time.sleep(5)

    if thing_text is None:
        print(f"  Batch {bi+1} failed — skipping")
        time.sleep(5)
        continue

    try:
        found = extract_weights(thing_text)
        print(f"  weights found: {found}")
    except Exception as e:
        print(f"  Parse error: {e}")
    time.sleep(3)

# ── Save ──────────────────────────────────────────────────────────────────────

with open('bgg-collection.json', 'w', encoding='utf-8') as f:
    json.dump(games, f, ensure_ascii=False)

has_w = sum(1 for g in games if g['w'] > 0)
print(f"\nDone! {len(games)} games, {has_w} with weight data.")
