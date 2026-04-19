# Fantasfera — Strona internetowa

Oficjalna strona **Fantasfery** — trójmiejskiej grupy pasjonatów gier planszowych i RPG.

🌐 **fantasfera.pl**

---

## O stronie

Strona statyczna (HTML + CSS + JS) hostowana na **GitHub Pages**. Zaprojektowana w klimacie średniowiecznej tawerny — ciemne drewno, złote akcenty, czcionki Cinzel i Lora.

### Sekcje

| Sekcja | Opis |
|---|---|
| **Hero** | Logo, hasło, wstęp |
| **O nas** | Opis grupy, karty informacyjne (Gdzie / Rodzaj gier / Nowi gracze / Spotkania) |
| **Harmonogram** | Tabela cyklicznych spotkań + widget kalendarza Google + widget Aftergame + Facebook Page Plugin |
| **Katalog Gier** | Grid okładek z kolekcji BGG; badge trudności (averageweight); filtrowanie po trudności; wyszukiwarka; paginacja (8 gier / strona) |
| **Znajdź nas w sieci** | Linki do Aftergame, Facebooka, Instagrama, Discorda |

---

## Technologie

- **HTML5 / CSS3** — bez frameworków, czysty vanilla
- **Google Fonts** — Cinzel Decorative, Cinzel, Lora
- **JavaScript** — widget kalendarza Google (iCal parser + CORS proxy), katalog gier BGG (JSON fetch + paginacja)
- **Hosting** — GitHub Pages (domena niestandardowa: `fantasfera.pl`, HTTPS automatyczny)

---

## Kalendarz Google

Widget kalendarza pobiera wydarzenia z publicznego kalendarza Google przez iCal (`.ics`) za pomocą CORS proxy. Próbuje kolejno:
1. `corsproxy.io`
2. `allorigins.win`

Wyświetla nadchodzące wydarzenia z pełną datą (dzień tygodnia, numer, miesiąc, rok) i godziną.

---

## Struktura plików

```
/
├── index.html                      # Strona główna
├── bgg-collection.json             # Kolekcja BGG (generowana przez GitHub Action)
├── CNAME                           # Domena niestandardowa dla GitHub Pages
├── Fantasfera_logo.png             # Logo graficzne (kwadrat)
├── Logo_bez_deski_transparent.png  # Logo hero (bez tła)
├── Napis_transparent.png           # Logo tekstowe (nawigacja, stopka)
├── aftergame.png                   # Ikona Aftergame
├── Facebook_Logo_Primary.png       # Ikona Facebook
├── Instagram_Glyph_White.png       # Ikona Instagram (biała)
├── Instagram_Glyph_Gradient.png    # Ikona Instagram (gradient)
├── Discord-Symbol-Blurple.png      # Ikona Discord
├── dice_favicon.png                # Favicon
├── weights.json                    # Wagi trudności gier ({id: weight}), commitowane ręcznie
├── fetch_weights_local.py          # Skrypt: ekstrakcja wag z CSV eksportu BGG
├── merge_guest_collection.py       # Skrypt: scalanie kolekcji znajomego z CSV
├── .github/
│   ├── workflows/update-bgg.yml    # GitHub Action: cotygodniowa sync kolekcji BGG
│   └── scripts/fetch_bgg.py        # Skrypt Python: pobiera kolekcję + merguje wagi
├── README.md
└── CHANGELOG.md
```

---

## Deployment

Strona jest automatycznie publikowana przez GitHub Pages przy każdym pushu na gałąź `main`.

---

## Katalog Gier BGG

Dane kolekcji pobierane są przez GitHub Action (`.github/workflows/update-bgg.yml`):
- Uruchamiany co poniedziałek o 4:00 UTC + ręczny trigger
- Skrypt `fetch_bgg.py` loguje się do BGG, pobiera kolekcję użytkownika `Bajomix` przez XML API v2, merguje wagi z `weights.json`
- Wynik zapisywany jako `bgg-collection.json` i commitowany do repo
- Frontend czyta `/bgg-collection.json` (same-origin, zero CORS)

> **Uwaga:** BGG XML API zwraca 401 dla wszystkich metod z IP datacenter. Wagi (`averageweight`) pobierane są raz lokalnie z eksportu CSV kolekcji BGG i commitowane jako `weights.json`.

### Aktualizacja wag trudności

1. Wejdź na BGG → Kolekcja → Eksportuj jako CSV
2. Uruchom: `python3 fetch_weights_local.py collection.csv`
3. `git add weights.json && git commit -m "Update weights" && git push`

### Dodanie kolekcji znajomego

1. Poproś znajomego o eksport CSV z BGG (Kolekcja → Eksportuj jako CSV)
2. Uruchom: `python3 merge_guest_collection.py kolekcja_znajomego.csv`
3. Skrypt pominie gry już istniejące w Twojej kolekcji (deduplicacja po ID)
4. `git add bgg-collection.json weights.json && git commit -m "Add friend collection" && git push`

### Progi trudności (badge'y)

| Badge | Zakres averageweight |
|---|---|
| Początkujący | < 2.0 |
| Łatwy | < 3.0 |
| Średniozaaw. | < 3.6 |
| Zaawansowany | < 4.2 |
| Ekspercki | ≥ 4.2 |

---

## Social Media

| Platforma | Link |
|---|---|
| Aftergame | [aftergame.app/groups/fantasfera](https://aftergame.app/groups/fantasfera) |
| Facebook | [facebook.com/fantasfera](https://www.facebook.com/fantasfera) |
| Instagram | [instagram.com/fanta.sfera](https://www.instagram.com/fanta.sfera) |
| Discord | [discord.gg/NsTztxrE8X](https://discord.gg/NsTztxrE8X) |
