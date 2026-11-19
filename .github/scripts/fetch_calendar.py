"""Fetch the public Fantasfera Google Calendar (iCal) and save upcoming events
as calendar.json, served same-origin by GitHub Pages (no CORS proxy needed).

Output is deterministic (no fetch timestamps), so the workflow only commits
when the events actually change.
"""
import json, re, sys, urllib.request
from datetime import datetime, timedelta, timezone

ICAL_URL = ('https://calendar.google.com/calendar/ical/'
            '2da0751953a6122c8f81e7f4840092cac413ef4c5a4070ff395bcf0c3c450b2e'
            '%40group.calendar.google.com/public/basic.ics')
OUT = 'calendar.json'
MAX_EVENTS = 30

req = urllib.request.Request(ICAL_URL, headers={'User-Agent': 'fantasfera.pl calendar sync'})
text = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
if 'BEGIN:VCALENDAR' not in text:
    sys.exit('Not an iCal file')

# Unfold continuation lines (RFC 5545 3.1)
lines = re.sub(r'\r?\n[ \t]', '', text).splitlines()


def unescape(v):
    return v.replace('\\n', ' ').replace('\\N', ' ').replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\').strip()


def parse_dt(params, value):
    """Return (iso_string, all_day). Timed events -> UTC ISO with Z."""
    value = value.strip()
    if 'VALUE=DATE' in params or len(value) == 8:
        return f'{value[0:4]}-{value[4:6]}-{value[6:8]}', True
    dt = datetime.strptime(value[:15], '%Y%m%dT%H%M%S')
    if value.endswith('Z'):
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Floating / TZID times: Fantasfera calendar is Europe/Warsaw.
        from zoneinfo import ZoneInfo
        tz = re.search(r'TZID=([^;:]+)', params)
        dt = dt.replace(tzinfo=ZoneInfo(tz.group(1) if tz else 'Europe/Warsaw'))
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), False


events, evt = [], None
for line in lines:
    if line == 'BEGIN:VEVENT':
        evt = {}
    elif line == 'END:VEVENT':
        if evt and evt.get('start') and evt.get('status') != 'CANCELLED':
            evt.pop('status', None)
            events.append(evt)
        evt = None
    elif evt is not None and ':' in line:
        prop, val = line.split(':', 1)
        name, _, params = prop.partition(';')
        name = name.upper()
        if name == 'SUMMARY':
            evt['title'] = unescape(val)
        elif name == 'LOCATION':
            evt['location'] = unescape(val)
        elif name == 'STATUS':
            evt['status'] = val.strip().upper()
        elif name == 'DTSTART':
            evt['start'], evt['allDay'] = parse_dt(params, val)
        elif name == 'RRULE':
            print(f"WARNING: recurring event not expanded: {evt.get('title', '?')}")

# Keep events from yesterday on; the browser hides past ones by its own clock.
cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
upcoming = sorted((e for e in events if e['start'][:10] >= cutoff), key=lambda e: e['start'])[:MAX_EVENTS]

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(upcoming, f, ensure_ascii=False, indent=1)
print(f'{len(events)} events in feed, {len(upcoming)} upcoming saved to {OUT}')
