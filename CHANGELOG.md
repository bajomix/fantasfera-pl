# Changelog

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
