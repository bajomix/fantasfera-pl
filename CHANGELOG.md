# Changelog

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
