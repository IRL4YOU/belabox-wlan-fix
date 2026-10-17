# 0.1.0-test4 – Anpassung an Kernelpaket 20261010-2

Dasselbe WLAN-Fix-Paket wie 0.1.0-test3, nur das Profil ist auf das neue
BELABOX-Kernelpaket angepasst. Treiberquelle und Fix sind unverändert.
**Vorabversion, keine Produktiv- oder allgemeine Stabilitätsfreigabe.**

- Für: ROCK 5B Plus, Kernel `5.10.160-belabox #168`, Kernelpaket
  `belabox-linux-rk3588=20261010-2`.
- Warum nötig: test3 prüft das Kernelpaket exakt (`20260116-1`) und bricht beim
  neuen Paket ab. Originaltreiber, Kernelkonfiguration und Symboltabelle des neuen
  Pakets sind bitgleich zum alten Stand; die Prüfsummen in `profile.json` sind
  unverändert, nur die Paketversion wurde angepasst.
- Für Kernel `#167` / Paket `20260116-1` gilt weiter 0.1.0-test3.
- Dateien: `belabox-wlan-fix-0.1.0-test4.tar.gz` und `.sha256`.

Geprüft am 11. Oktober 2026 auf der Box: Kompatibilitätsprüfung, Bau (227
Symbolprüfungen), Installationsplan, Installation, Neustart und `verify`
(`STARTPRÜFUNG OK`), WLAN-Kurztest (5 von 5 Paketen über 5 GHz, Kanal 44).
23 Pakettests. **Nicht geprüft:** Langzeittest, Kameraempfang über WLAN,
Rückweg-Boot, Offline-Rettung. Kein Beweis, dass sämtliche früheren
Systemhänger behoben sind.

---

# 0.1.0-test3 – experimenteller WLAN-Fix (für Kernel #167)

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
