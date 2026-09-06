# WLAN-Fix: geprüfter Stand

Stand: 6. September 2026. Paket `0.1.0-test3`.
Keine allgemeine Stabilitäts- oder Produktivfreigabe.

## Prüfumgebung

- Radxa ROCK 5B Plus, interner RTL8852BE, PCI `10ec:b852`.
- Vom Nutzer bestätigtes frisch installiertes Image:
  `belabox_rock_5b_plus-20250915-a84acea`. ZIP-SHA-256 noch nicht erfasst.
- Anschließend 218 reguläre Updates; zwei Ubuntu-Netzwerkupdates wegen
  gestaffelter Auslieferung zurückgestellt.
- Ubuntu 22.04.5, Kernel `5.10.160-belabox #167`,
  `belabox-linux-rk3588=20260116-1`, GCC 11.4.0.
- Extlinux mit `/boot/Image`, ohne Initramfs.
- Keine eigene Routing-/Powersave-Korrektur.
  Separate Lüftersteuerung und SSH-Autostart vorhanden.
- WLAN-Testwerkzeuge `iw=5.16-1build1`,
  `iputils-ping=3:20211215-1ubuntu0.1` ergänzt.

## Abgeschlossene Prüfungen am 6. September

1. Originalfehler im aktualisierten Originalsystem wieder nachgewiesen:
   `BUG: spinlock bad magic`, Aufrufkette `pq_push`,
   `_phl_ser_mdl_init`, `bk_module_init` aus `8852be`.
2. Unveränderte Quelle und gezielter Patch geprüft: `pq_init` vor erster
   Warteschlangennutzung, zugehöriges `pq_deinit` beim Abbau.
3. 23 automatisierte Pakettests auf Mac und Box bestanden. Vier neue Tests
   decken unvollständige Bootjournale, direkten Kernelpuffer sowie Fehler
   in beiden Quellen ab. Fehler dürfen nicht durch die zweite Quelle
   verborgen werden; ohne Bootanfang bleibt die Prüfung unvollständig.
4. Nativer Bau am 6. September um 06:55:29 UTC erfolgreich abgeschlossen.
   Vermagic, Abhängigkeiten, alle 227 importierten Symbol-CRCs und
   `pq_init` vor `pq_push` im Objektcode bestätigt.
   Keine Treffer für `error:`, `warning:`, `not found` im abgeschlossenen Bauprotokoll.
5. Installationsvorprüfung über LAN bestanden. Installation, tatsächlicher
   Rückweg zur Original-Modulauswahl und erneute Installation erfolgreich.
   Originalmodul und Sicherung unverändert. Dieser Rückwegtest erfolgte
   **vor** der ersten Aktivierung; kein Rückweg-Boot aus geladenem Fix.
6. Kontrollierter Neustart abgeschlossen. `verify` mit Exit 0:
   neuer Boot, `+wlanfix1` geladen, Bootanfang lesbar und die geprüften
   schweren Kernel-Fehlermuster nicht vorhanden. Der bekannte Spinlock-BUG
   fehlt. SSH, Lüftersteuerung und BELABOX-Dienst aktiv, etwa 41,6 °C.

7. WLAN 0 nach erneuter Anmeldung in der Weboberfläche verbunden;
   Authentifizierung und DHCP erfolgreich. WLAN 1 bleibt getrennt.
   Gebundener Router-Pakettest: 5 gesendet, 5 empfangen, 0 % Verlust;
   Laufzeit rund 4 Sekunden, Antwortzeiten 2,606–77,317 ms.
   `test-wifi` und anschließendes `verify` jeweils Exit 0. Seit Beginn
   der Verbindungsversuche keine neuen Kernelwarnungen im Journal.
   Damit ist nur die lokale WLAN-Grundfunktion geprüft, nicht Internet,
   Durchsatz oder Dauerstabilität.
8. Anschließend fünf Minuten reiner WLAN-Empfang zweier RTMP-Kameras:
   30 von 30 Messintervallen ohne Alarm, im Mittel 21,3 Mbit/s,
   keine zusätzlichen RX-Fehler/Drops oder Kernelwarnungen,
   Temperatur 39,8–41,6 °C. Abschließende Treiberprüfung erfolgreich.
9. Separater 15-Minuten-Systemvergleich: beide Kameraeingänge über WLAN,
   Hauptkamera als H.265/Opus über ausschließlich LAN ausgegeben.
   90 von 90 Messintervallen ohne Alarm oder Senderneustart; 40,7–41,6 °C.
   Hauptbild und Audioausschlag in OBS vom Nutzer bestätigt. Abschließende
   Treiberprüfung und kontrollierter Ausgabestopp erfolgreich.
   Das ist KEIN Test der WLAN-Ausgabe und kein Beweis, dass sämtliche
   früheren Hänger behoben sind; Bild-/Tonqualität nicht vollständig geprüft.

## Exakter Kandidat

- Paketprofil SHA-256:
  `c62f2c709a7a3ec11824efa4ecdb725a16eb3552cf88035795f85bafc1ef149a`
- Modul SHA-256:
  `1a41939bb17020915fd876e3b37d1b5ea782410848aafe4303f70155d51aa261`
- Originalmodul SHA-256:
  `00d2d3d8875942debf5b1931c4862ac1c8124777e89f3233e8e4bb88aabb0cc1`
- Version: `v1.15.10.0.5-0-gfa2af07cf.20220503+wlanfix1`
- Srcversion: `74925493EB0B2C0C4B67833`
- Abhängigkeiten: `rtkm,cfg80211`.
- Vollständige Quell-/Headerprüfsummen stehen in `profile.json`.
- Quelle und Bauparameter sind festgelegt. Byteidentität über andere
  Baupfade/Compilerstände ist nicht nachgewiesen.

## Was noch fehlt

- Upload-/Downloadlast, Wiederverbindung und längerer Betrieb.
- Rückweg einschließlich Neustart aus aktiv geladenem Fix und Offline-Rettungsweg.
- Vollständiges Durcharbeiten der Endnutzer-Anleitung ab normalem `user`;
  die aktuelle Installation wurde durch den Assistenten als Root durchgeführt.
- SHA-256 des tatsächlich geflashten Images.
- Abschließender Release-/Lizenzumfang und tatsächliche Homepageintegration.

Frühere Tests am 3. September beseitigten den Start-BUG und bestanden einen
fünfminütigen begrenzten WLAN-Download. Trotzdem gab es später weitere
systemweite Hänger. WLAN-1-Parallelbetrieb mit zwei Routern war nicht
erfolgreich; einzelne bestandene Kurztests beweisen keine Dauerstabilität.

Die ausführliche private Projekthistorie bleibt außerhalb dieses
Auslieferungspakets erhalten. Öffentliche Unterlagen enthalten keine
SSH-Schlüssel, Box-Konfigurationen oder Stream-Zugangsdaten.
