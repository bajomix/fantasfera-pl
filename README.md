# Fantasfera — Strona internetowa

Oficjalna strona **Fantasfery** — trójmiejskiej grupy pasjonatów gier planszowych i RPG.

🌐 **fantasfera.pl**

---

## O stronie

Strona statyczna (HTML + CSS + JS) hostowana na InfinityFree. Zaprojektowana w klimacie średniowiecznej tawerny — ciemne drewno, złote akcenty, czcionki Cinzel i Lora.

### Sekcje

| Sekcja | Opis |
|---|---|
| **Hero** | Logo, hasło, wstęp |
| **O nas** | Opis grupy, karty informacyjne (Gdzie / Rodzaj gier / Nowi gracze / Spotkania) |
| **Harmonogram** | Tabela cyklicznych spotkań + widget kalendarza Google |
| **Biblioteka Gier** | Placeholder na embed BoardGameGeek |
| **Znajdź nas w sieci** | Linki do Aftergame, Facebooka, Instagrama, Discorda |

---

## Technologie

- **HTML5 / CSS3** — bez frameworków, czysty vanilla
- **Google Fonts** — Cinzel Decorative, Cinzel, Lora
- **JavaScript** — widget kalendarza Google (iCal parser)
- **PHP** — `ical-proxy.php` (nieaktywny, InfinityFree blokuje outbound HTTP)
- **Hosting** — InfinityFree (HTTPS, PHP 7/8)

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
├── index.html                  # Strona główna
├── ical-proxy.php              # PHP proxy dla kalendarza (nieaktywny)
├── directory/.htaccess         # Konfiguracja serwera InfinityFree
├── Fantasfera_logo.png         # Logo graficzne (kwadrat)
├── Logo_bez_deski_transparent.png  # Logo hero (bez tła)
├── Napis_transparent.png       # Logo tekstowe (nawigacja, stopka)
├── aftergame.png               # Ikona Aftergame
├── Facebook_Logo_Primary.png   # Ikona Facebook
├── Instagram_Glyph_White.png   # Ikona Instagram (biała)
├── Instagram_Glyph_Gradient.png # Ikona Instagram (gradient)
├── Discord-Symbol-Blurple.png  # Ikona Discord
├── README.md
└── CHANGELOG.md
```

---

## Social Media

| Platforma | Link |
|---|---|
| Aftergame | [aftergame.app/groups/fantasfera](https://aftergame.app/groups/fantasfera) |
| Facebook | [facebook.com/fantasfera](https://www.facebook.com/fantasfera) |
| Instagram | [instagram.com/fanta.sfera](https://www.instagram.com/fanta.sfera) |
| Discord | [discord.gg/NsTztxrE8X](https://discord.gg/NsTztxrE8X) |
