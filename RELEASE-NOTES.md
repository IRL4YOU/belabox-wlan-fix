# 0.1.0-test3 – experimenteller WLAN-Fix

Unabhängiger RTL8852BE-Initialisierungsfix für BELABOX auf dem ROCK 5B Plus.
**Vorabversion, keine Produktiv- oder allgemeine Stabilitätsfreigabe.**

## Download

- `belabox-wlan-fix-0.1.0-test3.tar.gz`: Quellpaket mit festgelegter
  Originalquelle, Bau-/Installationswerkzeugen, Tests und Dokumentation.
- `belabox-wlan-fix-0.1.0-test3.tar.gz.sha256`: zugehörige Prüfsumme.

Kein fertiges Treiber-Binärmodul und kein BELABOX-Image. Bau auf der exakt
passenden Box; vor Installation Anleitung, Kompatibilität und Rückweg lesen.

## Geprüfter Stand

Kernel `5.10.160-belabox #167`, Kernelpaket `20260116-1`, RTL8852BE.
23 Pakettests, nativer Bau, 227 Kernel-Symbolprüfungen sowie Installations-
und Neustartprüfung bestanden. Der bekannte `BUG: spinlock bad magic` war
nach Neustart mit dem Fix nicht mehr vorhanden. WLAN-0-Kurztest,
fünf Minuten Kameraempfang und 15 Minuten Hauptkamera-Ausgabe über LAN
blieben in den überwachten Messwerten unauffällig.

## Noch offen

WLAN-Ausgabe/LAN+WLAN-Betrieb, längere Laufzeit, Rückweg-Boot aus geladenem
Fix, Offline-Rettung und vollständiger Endnutzer-Neuinstallationsdurchlauf.
Kein Beweis, dass sämtliche früheren Systemhänger behoben sind.
Keine Freigabe für andere Kernel/Boards oder zwei Router über WLAN 0 und WLAN 1.

Ausführlicher Prüfstand: `TESTSTAND.md`. Installation/Rückweg:
`HOMEPAGE-ANLEITUNG.md`. Lizenz/Herkunft: `LICENSE` und `QUELLEN.md`.
