# ROCK 5B+ WLAN-Fix

**0.1.0-test3 · Experimentelle Vorabversion · Keine Produktivfreigabe**

Ein unabhängiger Nachrüstfix von IRL4YOU für einen konkret nachgewiesenen
Initialisierungsfehler im internen Realtek-RTL8852BE-Treiber.
Kein offizielles Produkt oder freigegebenes Update von BELABOX, Radxa oder Realtek.

## Was wird behoben?

Der Originaltreiber initialisiert eine interne Warteschlange unvollständig.
Beim Start wurde folgende Meldung mit der Aufrufkette `pq_push` →
`_phl_ser_mdl_init` → `bk_module_init` beobachtet:

```text
BUG: spinlock bad magic
```

Der gezielte Patch verwendet `pq_init` vor der ersten Warteschlangennutzung
und ergänzt das zugehörige `pq_deinit`. Das Originalmodul bleibt erhalten;
ein separat installiertes Zusatzmodul wird beim nächsten Neustart geladen.

**Dieser Fix ist keine nachgewiesene Lösung für alle Systemhänger.**
Frühere Gesamtausfälle traten auch mit dem damaligen WLAN-Fix auf.
Kameraadressen, RTMP-Ziele und WLAN-Passwörter werden vom Installer
nicht verändert. Der Fix schaltet WLAN nicht ab.

## Unterstützte Testumgebung

- Radxa ROCK 5B Plus, interner RTL8852BE (`10ec:b852`).
- Ubuntu 22.04.5, BELABOX-Kernel `5.10.160-belabox #167`.
- Kernelpaket exakt `belabox-linux-rk3588=20260116-1`.
- Bau mit GCC 11; exakte Originalmodul-, Kernelkonfigurations- und
  Symboltabellenprüfsummen werden vom Paket kontrolliert.
- Ausgangsimage laut Nutzer: `belabox_rock_5b_plus-20250915-a84acea`,
  anschließend reguläre Updates. Image-Archivprüfsumme noch nicht erfasst.

Andere Boards, Kernel und WLAN-Chips sind nicht freigegeben.
Kompatibilitätsprüfungen niemals entfernen oder an unbekannte Systeme anpassen.

## Anleitung und Download

1. Lies zuerst die [Schritt-für-Schritt-Anleitung](HOMEPAGE-ANLEITUNG.md)
   und den [vollständigen Prüfstand](TESTSTAND.md).
2. Verwende das versionierte **Quellpaket** samt SHA-256-Datei aus dem
   Bereich [Releases](../../releases). Nicht ein beliebiges fremdes `.ko` laden.
3. Halte LAN-Zugang und eine Sicherung bereit. Baue und prüfe das Modul
   gemäß Anleitung auf der exakt passenden Box.
4. Installiere nur bewusst als experimentellen Test; starte neu und führe
   die Start- sowie WLAN-Prüfungen aus. Der Rückweg steht in derselben Anleitung.

Das Quellpaket enthält die vollständige festgelegte Treiberquelle, den
Änderungsschritt und die Bau-/Installationswerkzeuge. Es enthält kein fertiges
Binärmodul und kein BELABOX-Image. Die automatisch von GitHub erzeugten
Quellarchive heißen anders; die Anleitung bezieht sich auf das angehängte
`belabox-wlan-fix-0.1.0-test3.tar.gz`.

## Tatsächlich abgeschlossene Prüfungen

Stand 6. September 2026:

- 23 automatisierte Pakettests auf Mac und Box; am separaten Release-Ort erneut geprüft.
- Nativer Bau, 227 importierte Kernel-Symbolprüfsummen und Installationsprüfung.
- Installation → Rückweg zur Original-Modulauswahl → erneute Installation,
  noch vor dem ersten Laden des Fixes.
- Neustart mit geladenem Fix: bekannter Spinlock-BUG nicht erneut vorhanden.
- WLAN-0-Router-Kurztest und fünf Minuten Empfang von zwei RTMP-Kameras.
- 15 Minuten Hauptkamera-Ausgabe über LAN mit H.265/Opus, beide Eingänge
  weiterhin über WLAN; keine Alarme in den überwachten Messwerten.

## Offene Grenzen

- WLAN als Sendeweg bzw. LAN+WLAN-Ausgabe und längerer Betrieb stehen noch aus.
- Rückweg mit Neustart aus aktiv geladenem Fix und Offline-Rettungsweg fehlen noch.
- Vollständiger Durchlauf der Endnutzer-Anleitung ab normalem Benutzer fehlt noch.
- WLAN 1 für parallele Verbindungen zu einem zweiten Router ist nicht freigegeben.
- Kein vollständiger Nachweis von Bild-/Tonqualität oder Dauerstabilität.

Eine bestandene Prüfung ist keine Garantie für andere Geräte oder Lastsituationen.
Details und präzise Modulprüfsummen stehen in [TESTSTAND.md](TESTSTAND.md).

## Paketinhalt

| Datei | Zweck |
| --- | --- |
| `wlanfix.py`, `build.py`, `profile.json` | Prüfung, Bau, Installation und Rückweg |
| `tests/` | Pakettests sowie separat manuell gestarteter Lasttest |
| `vendor/source.tar.gz` | Festgelegte unveränderte Treiberquelle |
| `make_release.py` | Tests und Verpackung des Quellpakets |
| `LICENSE`, `QUELLEN.md`, `vendor/README.md` | Lizenztext und Herkunft |

`belabox-source-routing` ist eine mitgeführte ältere, separate Routing-
Hilfsdatei. Sie wird vom WLAN-Installer **nicht** installiert und gehört
nicht zum geprüften frischen Systemstand. Nicht zusätzlich auf Verdacht einbauen.
Der manuelle Downloadtest in `tests/` ist kein Unit-Test: Er benötigt
Root-Rechte und kann bis zu 750 MB Internetverkehr erzeugen.

## Lizenz und Herkunft

Die Paketwerkzeuge werden unter GPL-2.0-only bereitgestellt.
Urheber- und Lizenzhinweise der Realtek-/Radxa-Treiberquelle bleiben erhalten.
Der vollständige Lizenztext und die Quelle sind mit enthalten.
Siehe [LICENSE](LICENSE) und [QUELLEN.md](QUELLEN.md).

Fehlermeldungen ohne Zugangsdaten melden: keine WLAN-Passwörter,
SSH-Schlüssel, Stream-IDs oder vollständigen privaten Box-Konfigurationen hochladen.
