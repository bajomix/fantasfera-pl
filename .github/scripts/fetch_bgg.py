import cloudscraper, json, time, os, xml.etree.ElementTree as ET
import requests as req_lib
from playwright.sync_api import sync_playwright

USERNAME = 'Bajomix'
BGG_USER = os.environ.get('BGG_USERNAME', '')
BGG_PASS = os.environ.get('BGG_PASSWORD', '')

# ── Step 1: fetch collection (cloudscraper) ───────────────────────────────────

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
print(f"Parsed {len(games)} games. Fetching weights via in-browser fetch…")

# ── Step 2: fetch weights using Playwright in-browser fetch() ────────────────
# Requests made inside the browser context carry all browser headers
# (sec-fetch-site, sec-fetch-mode, sec-ch-ua, cookies, etc.) — BGG treats
# them as real browser requests, bypassing IP-based API blocking.

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

BATCH = 20
batches = [ids[i:i+BATCH] for i in range(0, len(ids), BATCH)]

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-dev-shm-usage']
    )
    context = browser.new_context()
    page = context.new_page()

    # Login via form
    print("Playwright: logging in…")
    page.goto('https://boardgamegeek.com/login',
              timeout=40000, wait_until='domcontentloaded')
    page.wait_for_timeout(2000)

    for sel in ['#inputUsername', 'input[name="username"]']:
        try:
            page.fill(sel, BGG_USER, timeout=3000)
            break
        except Exception:
            pass
    for sel in ['#inputPassword', 'input[name="password"]']:
        try:
            page.fill(sel, BGG_PASS, timeout=3000)
            break
        except Exception:
            pass
    for sel in ['button.btn-primary', 'button[type="submit"]']:
        try:
            page.click(sel, timeout=3000)
            break
        except Exception:
            pass

    page.wait_for_timeout(4000)
    print(f"  Post-login URL: {page.url}")

    # Navigate to BGG homepage so same-origin fetch works
    page.goto('https://boardgamegeek.com/', timeout=30000, wait_until='domcontentloaded')
    page.wait_for_timeout(2000)

    # Test single-game fetch first
    probe_result = page.evaluate("""
        async (id) => {
            const url = 'https://boardgamegeek.com/xmlapi2/thing?stats=1&id=' + id;
            const r = await fetch(url, { credentials: 'include' });
            const text = await r.text();
            return { status: r.status, preview: text.slice(0, 120) };
        }
    """, ids[0])
    print(f"Probe (game {ids[0]}): HTTP {probe_result['status']}, preview={probe_result['preview']!r}")

    weights_found = 0

    for bi, batch in enumerate(batches):
        batch_ids = ','.join(batch)
        thing_text = None

        for attempt in range(3):
            result = page.evaluate("""
                async (ids) => {
                    const url = 'https://boardgamegeek.com/xmlapi2/thing?stats=1&id=' + ids;
                    try {
                        const r = await fetch(url, { credentials: 'include' });
                        const text = await r.text();
                        return { status: r.status, text: text };
                    } catch (e) {
                        return { status: 0, text: '', error: String(e) };
                    }
                }
            """, batch_ids)

            status = result.get('status', 0)
            resp_text = result.get('text', '')
            print(f"  Batch {bi+1}/{len(batches)} attempt {attempt+1}: "
                  f"HTTP {status}, preview={resp_text[:80]!r}")

            if status == 200 and '<items' in resp_text:
                thing_text = resp_text
                break
            if status == 202:
                page.wait_for_timeout(12000)
                continue
            page.wait_for_timeout(3000)

        if thing_text is None:
            print(f"  Batch {bi+1} failed — skipping")
            continue

        try:
            found = extract_weights(thing_text)
            weights_found += found
            print(f"  weights found: {found}")
        except Exception as e:
            print(f"  Parse error: {e}")

        page.wait_for_timeout(2000)

    browser.close()

print(f"\nTotal weights found: {weights_found}")

# ── Save ──────────────────────────────────────────────────────────────────────

with open('bgg-collection.json', 'w', encoding='utf-8') as f:
    json.dump(games, f, ensure_ascii=False)

has_w = sum(1 for g in games if g['w'] > 0)
print(f"Done! {len(games)} games, {has_w} with weight data.")
