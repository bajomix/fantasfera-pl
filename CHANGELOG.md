# Changelog

## [2026-04-19] — BGG weight fetch: lokalny skrypt + weights.json

### Zmiany
- Porzucono próby fetchowania wag w CI (BGG blokuje thing API ze wszystkich IP datacenter niezależnie od metody)
- Dodano `fetch_weights_local.py` — skrypt do uruchomienia raz lokalnie, generuje `weights.json` z mapą `{id: weight}`
- CI script uproszczony: pobiera tylko kolekcję, merguje wagi z `weights.json` (jeśli istnieje)
- Usunięto Playwright z workflow — czas buildu z ~2min do ~15s

---

## [2026-04-19] — Paginacja: stały limit 8 gier na stronę

### Zmiany
- Zmieniono rozmiar strony z dynamicznego (cols × 3) na stały: 8 gier

---

## [2026-04-19] — BGG weight fetch: in-browser fetch() via Playwright

### Zmiany
- Bearer token nie istnieje w BGG (używa cookie-based auth) — nowe podejście: `page.evaluate()` wywołuje `fetch()` bezpośrednio z wnętrza przeglądarki Chromium, z cookies i nagłówkami `sec-fetch-*`; BGG traktuje to jako prawdziwy request przeglądarki

---

## [2026-04-18] — BGG weight fetch: Playwright (headless Chrome)

### Zmiany
- Skrypt przepisany na Playwright — headless Chromium loguje się do BGG przez formularz, przechwytuje Bearer JWT z nagłówków `Authorization` wychodzących requestów API, następnie używa go do zapytań thing XML API
- GitHub Action zaktualizowany: instaluje `playwright` + `playwright install chromium --with-deps`
- Rozwiązuje problem 401 z datacenter IP — BGG blokuje xmlapi2/thing z Azure IP, ale Bearer JWT (z prawdziwej sesji browserowej) pozwala ominąć blokadę

---

## [2026-04-18] — Katalog gier: paginacja + naprawa BGG weight fetch

### Zmiany
- **Paginacja katalogu gier** — lista podzielona na strony po 3 wiersze (dynamicznie obliczane wg szerokości siatki × 3); przyciski Poprzednia/Następna z licznikiem stron; zmiana filtra lub wyszukiwarki resetuje do strony 1; scroll do siatki z offsetem 90px dla sticky navbara
- **Naprawa scope paginacji** — fix bugu gdzie `currentPage++` w callbacku modyfikował lokalny parametr zamiast zmiennej z closure
- **BGG weight fetch — diagnoza** — BGG XML API v1 i v2 zwracają 401 ze wszystkich metod (fresh/authed/cloudscraper) dla IP datacenter (GitHub Actions = Azure); `api.geekdo.com/api/geekitems` zwraca HTTP 200 — skrypt przepisany na per-game JSON API; probe diagnostyczny drukuje pełną strukturę JSON itema

---

## [2026-04-18] — Katalog gier: filtry trudności + badge'y + JSON z weight

### Zmiany
- Filtry zmienione z "liczba graczy" na "trudność" (Wszystkie / Początkujący / Łatwy / Średni / Zaawansowany / Ekspercki)
- Frontend czyta `bgg-collection.json` zamiast XML — JSON zawiera pole `w` (averageweight z BGG thing API)
- Badge'y trudności działają poprawnie — `averageweight` nie było dostępne w collection API, teraz pobierane osobno z thing API przez GitHub Action
- GitHub Action zaktualizowany: po pobraniu kolekcji fetchuje thing API partiami po 50 gier i zapisuje `bgg-collection.json` z pełnymi danymi

---

## [2026-04-18] — Katalog gier BGG + GitHub Action do synchronizacji

### Nowe funkcje
- **Sekcja "Katalog Gier"** zastępuje placeholder BGG:
  - Grid okładek pobierany z kolekcji BGG użytkownika Bajomix
  - Badge trudności na okładce: Początkujący / Łatwy / Średni / Zaawansowany / Ekspercki (na podstawie `averageweight` z BGG)
  - Liczba graczy i czas gry przy każdej grze
  - Link do strony gry na BGG
  - Wyszukiwarka po tytule
  - Filtry po liczbie graczy (2 / 3 / 4 / 5 / 6+)
- **GitHub Action** (`.github/workflows/update-bgg.yml`): co poniedziałek o 4:00 UTC pobiera kolekcję z BGG API i zapisuje jako `bgg-collection.xml` w repo; dostępny też ręczny trigger z GitHub UI

### Architektura
- Frontend ładuje `/bgg-collection.xml` (same-origin, zero CORS) — fallback na live BGG API przez proxy
- BGG API blokuje zapytania server-side z publicznych IP (401 Cloudflare); GitHub Actions może omijać ten limit; jeśli nie — użytkownik może ręcznie wgrać plik z eksportu BGG

---

## [2026-04-18] — Responsywność mobilna + fix kalendarza CORS + favicon

### Nowe funkcje
- **Hamburger menu** na mobile (≤640px): przycisk z animacją X/☰, rozwijana lista linków na pełną szerokość ekranu; menu zamyka się po kliknięciu linku
- **Favicon** — ikona kości RPG (`dice_favicon.png`) w zakładce przeglądarki

### Poprawki responsywności (375px / 414px)
- `section { padding: 70px → 44px }` na mobile
- `page-wrap { padding: 0 16px }` zamiast 24px na mobile
- Tabela harmonogramu przelana na karty: każdy wiersz jako oddzielna karta z border-left, kolumna "Opis" ukryta (zbędna na małym ekranie)
- Tytuł wydarzenia w kalendarzu: `white-space: nowrap` → `normal` na mobile — długie tytuły zawijają się zamiast być obcinane

### Fix kalendarza Google na GitHub Pages
- Dodano dwa dodatkowe fallbacki CORS proxy:
  - `corsproxy.io/?url=` (nowy format z encoded URL)
  - `api.codetabs.com/v1/proxy?quest=` (nowy fallback)
- Kolejność prób: corsproxy.io (nowy format) → corsproxy.io (stary format) → allorigins.win → codetabs.com

---

## [2026-04-17] — Favicon + wyśrodkowanie wtyczki Facebook

### Zmiany
- Dodano favicon (`dice_favicon.png` — ikona kości RPG) wyświetlany w zakładce przeglądarki
- Wyśrodkowano wtyczkę Facebook Page Plugin w kontenerze (flexbox `justify-content: center`)
- Usunięto nadmiarowe `width: 100% !important` na elementach `.fb-page`, które blokowały wyśrodkowanie

---

## [2026-04-17] — Responsywna szerokość wtyczki Facebook Page Plugin

### Poprawki
- Wtyczka Facebook nie rozciągała się do pełnej szerokości kontenera — wyświetlała się wąsko po lewej stronie
- Usunięto `xfbml=1` z URL SDK (zapobieganie przedwczesnemu renderowaniu przed ustawieniem szerokości)
- Dodano `window.fbAsyncInit` z ręcznym wywołaniem `FB.XFBML.parse()` po ustawieniu `data-width` na rzeczywistą szerokość kontenera (px)
- Dodano handler `resize` z debouncingiem (300ms) — wtyczka ponownie renderuje się po zmianie rozmiaru okna

---

## [2026-04-17] — Przeniesienie wtyczki Facebook pod widget Aftergame

### Zmiany
- Wtyczka Facebook Page Plugin przeniesiona z sekcji "Znajdź nas w sieci" do sekcji Harmonogram, bezpośrednio pod widget Aftergame
- Poprawiono responsywność wtyczki: `.fb-embed-inner` ustawiony na `width: 100%`, iframe Facebooka rozciąga się do szerokości kontenera

---

## [2026-04-17] — Facebook Page Plugin + poprawki logo w nawigacji

### Nowe funkcje
- Dodano Facebook Page Plugin w sekcji "Znajdź nas w sieci":
  - Boks `.fb-embed-box` poniżej kart social media, styl zgodny ze stroną (ciemne tło, złoty nagłówek, niebieska kreska akcentująca)
  - SDK Facebook: `sdk.js#xfbml=1&version=v25.0&appId=1696226208381172`, język pl_PL
  - Plugin wyświetla timeline strony facebook.com/fantasfera, dopasowuje szerokość do kontenera

### Poprawki
- Logo nawigacji (`Napis_transparent.png`): usunięto hardcodowane atrybuty `width`/`height`, zastąpione przez CSS (`height: 48px; width: auto`) — brak ucinania
- Wysokość navbara zwiększona z 60px do 72px
- To samo w stopce

---

## [2026-04-17] — Widget Aftergame w sekcji harmonogramu

### Nowe funkcje
- Dodano widget Aftergame jako osobny boks poniżej kalendarza Google w sekcji Harmonogram
  - Tytuł: "Odkryj nasze wydarzenia w Aftergame"
  - iframe: `https://aftergame.app/groups/fantasfera/events?mode=embed`, wysokość 400px
  - Styl zgodny z resztą strony (`.calendar-embed-box`, pomarańczowa kreska, Cinzel)
  - Zredukowany padding i margin-top dla zwartego wyglądu

---

## [2026-04-17] — Poprawki tabeli harmonogramu

### Zmiany UI
- Tabela harmonogramu (Termin / Wydarzenie / Miejsce / Opis):
  - `table-layout: fixed` z `colgroup` — kolumny o stałych proporcjach (14% / 34% / 20% / 32%)
  - `vertical-align: middle` — tekst wyśrodkowany pionowo we wszystkich komórkach
  - Zwiększony padding komórek (`18px 20px`)
  - Badge "Cykliczne" / "Specjalne" zawsze w jednej linii z tytułem: komórka wydarzeń oparta na flexbox (`event-cell`), tytuł rozciąga się (`flex: 1`), badge przypięty do prawej — działa poprawnie nawet gdy tytuł się zawija

---

## [2026-04-17] — Migracja na GitHub Pages

### Zmiany hostingu
- Przeniesiono hosting z InfinityFree na **GitHub Pages**
- Strona publikowana automatycznie z gałęzi `main` przy każdym pushu
- HTTPS obsługiwany natywnie przez GitHub Pages

### Usunięte pliki
- `ical-proxy.php` — PHP proxy zbędne, GitHub Pages nie obsługuje PHP; widget kalendarza działa przez CORS proxy w JS
- `directory/.htaccess` — konfiguracja specyficzna dla InfinityFree (przekierowania HTTP→HTTPS, strony błędów 403/404/500); GitHub Pages obsługuje to natywnie

---

## [2026-04-17] — Widget kalendarza Google + poprawki UI

### Nowe funkcje
- Zastąpiono iframe Google Calendar własnym widgetem JavaScript:
  - Pobiera wydarzenia z publicznego kalendarza przez iCal (`.ics`)
  - Wyświetla nadchodzące wydarzenia posortowane chronologicznie (max 12)
  - Każde wydarzenie: boksik z datą (skrót dnia tygodnia, numer dnia, skrót miesiąca) + tytuł + pełna data + godzina + lokalizacja
  - Fallback na dwa CORS proxy (`corsproxy.io`, `allorigins.win`) — działa bez PHP
  - Styl pasuje do kolorystyki strony (ciemne tło, złote akcenty, Cinzel)
- Dodano `ical-proxy.php` (PHP proxy — nieaktywny, InfinityFree blokuje outbound HTTP)

### Poprawki UI
- Sekcja "Kto jesteśmy?" → "Kim jesteśmy?"
- Karty informacyjne (Gdzie / Rodzaj gier / Nowi gracze / Spotkania):
  - Treść wyśrodkowana poziomo i pionowo (flexbox)
  - Jednakowa wysokość kart (`min-height: 120px`)
  - Równomierne odstępy między elementami (`gap`)
  - Skrócone etykiety nie łamią się (`white-space: nowrap`)
- Widget kalendarza: pełna nazwa miesiąca i dnia tygodnia w metadanych wydarzenia, skrót dnia tygodnia w boksiku daty

---

## [2026-04-17] — Synchronizacja z InfinityFree

### Zmiany
- Zastąpiono całą zawartość repozytorium plikami pobranymi z serwera InfinityFree (produkcja)
- Nowa wersja `index.html` z pełnym redesignem strony:
  - Motyw wizualny: ciemna tawerna, tekstura drewniana, złote akcenty
  - Czcionki: Cinzel Decorative, Cinzel, Lora (Google Fonts)
  - Sekcje: nawigacja sticky, hero, O nas, Harmonogram Spotkań, Biblioteka Gier, Social Media, stopka
  - Responsywny layout (mobile/tablet/desktop)
  - Tabela harmonogramu ze spotkaniami (wtorki w Pub U7, 3. sobota miesiąca w TEB Technikum)
  - Linki do Aftergame, Facebooku, Instagrama, Discorda z ikonami

### Dodane pliki
- `Napis_transparent.png` — logo tekstowe Fantasfera (używane w nawigacji i stopce)
- `Logo_bez_deski_transparent.png` — logo graficzne (używane w sekcji hero)
- `directory/.htaccess` — konfiguracja serwera InfinityFree (przekierowanie HTTP→HTTPS, strony błędów)

### Zmiany struktury
- Obrazy przeniesione z `obrazy/socials/` do katalogu głównego (zgodnie ze strukturą na serwerze)
- Usunięto katalog `claude/` (stare prototypy, nie produkcja)
- Usunięto katalog `obrazy/socials/` (zastąpiony przez pliki w katalogu głównym)
