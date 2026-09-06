# BELABOX WLAN-Fix für ROCK 5B Plus

IRL4YOU · Stand 6. September 2026 · Paket `0.1.0-test3`

**Unveröffentlichte Testversion.** Eigenständiger Seiteninhalt für die spätere
IRL4YOU-Homepage. Downloadlinks werden nach den vereinbarten Prüfungen ergänzt.

## Was wird korrigiert?

Der interne Realtek-WLAN-Treiber benutzt beim Start eine Warteschlange,
deren Sperre nicht korrekt initialisiert wurde. Typische Meldung:

```text
BUG: spinlock bad magic
pq_push [8852be]
_phl_ser_mdl_init [8852be]
bk_module_init [8852be]
```

Der Fix ergänzt Initialisierung und Freigabe dieser Sperre. Er verändert weder WLAN-Passwörter, Kameraadressen, Stream-Ziele noch
die BELABOX-Oberfläche. Er ist **keine nachgewiesene Lösung für alle Hänger**:
Frühere Gesamtausfälle traten auch mit dem damaligen WLAN-Fix auf.

## Prüfstand und Voraussetzungen

Am 6. September bestanden: 23 Pakettests auf Mac und Box, nativer Treiberbau,
alle 227 Kernel-Schnittstellenprüfungen, Installation und Neustartprüfung.
Der bekannte Spinlock-Startfehler fehlt im neuen Bootprotokoll. Der Rückweg
zur Original-Modulauswahl wurde vor der ersten Aktivierung praktisch geprüft.
WLAN 0 ist verbunden; der gezielt über WLAN gesendete Router-Kurztest bestand
mit 5 von 5 beantworteten Paketen. Lasttests, längerer Betrieb und Rückweg
samt Neustart aus dem geladenen Fix stehen noch aus. Details und exakte
Modulprüfsumme: `TESTSTAND.md`.

- Radxa ROCK 5B Plus mit internem RTL8852BE (`10ec:b852`).
- Vom Nutzer frisch installiertes Image:
  `belabox_rock_5b_plus-20250915-a84acea`. Dateiname bestätigt,
  SHA-256 des geflashten ZIP-Archivs noch nicht erfasst.
- Danach reguläre BELABOX-/Ubuntu-Updates: Ubuntu 22.04.5,
  Kernel `5.10.160-belabox #167`, Kernelpaket
  `belabox-linux-rk3588=20260116-1`.
- Originalmodul und Kernel-Baudateien müssen die festgelegten Prüfsummen haben.
  Das Prüfprogramm kontrolliert dies. Keine Ablehnung umgehen.
- Python 3, GCC 11, make, binutils und kmod; mindestens 1 GiB freier
  Bauplatz unter `/var/tmp`, besser 2 GiB.
- Funktionierender SSH-Zugang über LAN und eine Sicherung der Startkarte.

Das unveränderte Image enthielt zunächst ein älteres Kernelpaket. Der
Image-Dateiname allein genügt deshalb nicht als Kompatibilitätsnachweis.
Der WLAN-Installer führt kein Systemupgrade aus.

LAN angeschlossen lassen. Stream-Ausgabe und deren Autostart ausschalten.
Für die ersten Tests nur WLAN 0 verbinden und WLAN 1 getrennt lassen.
Beide Schnittstellen gehören zum selben Funkchip; der bisherige Paralleltest
mit zwei Routern war nicht erfolgreich. WLAN 1 wird durch den Fix nicht entfernt.

## 1. Paket kopieren – am Mac oder PC

Aus demselben veröffentlichten Release werden benötigt:
`belabox-wlan-fix-0.1.0-test3.tar.gz` und die gleichnamige `.sha256`-Datei.
**Es gibt noch keinen öffentlichen Download.** Nicht das BELABOX-Image
anstelle des Zusatzpakets verwenden.

Terminal im Downloadordner öffnen, `BOX-IP` durch die LAN-IP der Box ersetzen:

```bash
scp belabox-wlan-fix-0.1.0-test3.tar.gz belabox-wlan-fix-0.1.0-test3.tar.gz.sha256 user@BOX-IP:/home/user/
ssh user@BOX-IP
```

Ab jetzt laufen alle Befehle **auf der Box**. Jeden Block einzeln ausführen,
auf Abschluss warten und bei einer Fehlermeldung anhalten.
Passwörter nur in die Passwortabfrage eingeben; dabei erscheinen keine Zeichen.

## 2. Prüfen und entpacken – auf der Box

```bash
cd /home/user
sha256sum -c belabox-wlan-fix-0.1.0-test3.tar.gz.sha256
```

Erwartet: `belabox-wlan-fix-0.1.0-test3.tar.gz: OK`. Nur dann:

```bash
mkdir /home/user/belabox-wlan-test3 && tar -xzf /home/user/belabox-wlan-fix-0.1.0-test3.tar.gz -C /home/user/belabox-wlan-test3
cd /home/user/belabox-wlan-test3/wlan-fix
sudo python3 -B build.py --check
```

Erwartet: `KOMPATIBEL für den Bau der Testversion. Noch kein Funktionstest.`
Vorhandene Zielordner nicht überschreiben. Bei einem erneuten Versuch neue
Namen wählen und diese in allen folgenden Befehlen durchgängig verwenden.

## 3. Testwerkzeuge ergänzen und Treiber bauen

```bash
sudo apt-get install --no-install-recommends iw iputils-ping
python3 -B -m unittest discover -s tests -v
sudo python3 -B build.py --output /var/tmp/belabox-wlan-build-test3
```

Paketvorschlag vor Bestätigung lesen: nur die beiden Testwerkzeuge ergänzen,
falls sie fehlen. Der Bau verwendet zwei parallele Jobs und ein neues
Bauverzeichnis. Erwarteter Abschluss:
`BUILD GEPRÜFT. Noch NICHT installiert oder geladen.`

Bei Problemen:

```bash
tail -n 30 /var/tmp/belabox-wlan-build-test3/build.log
```

## 4. Installation vorprüfen

Die LAN-IP des steuernden Rechners eingeben, nicht die Box- oder Router-IP:

```bash
read -r -p 'LAN-IP deines Rechners: ' WLANFIX_LAN_PEER
sudo python3 -B wlanfix.py plan --build-dir /var/tmp/belabox-wlan-build-test3 --lan-peer "$WLANFIX_LAN_PEER"
```

Erwartet: `INSTALLATIONS-VORPRÜFUNG OK. Keine Änderungen.`
Geprüft werden LAN-Zugriff, Bootlayout, Originalmodul und Kernel-Schnittstellen.

## 5. Installieren und neu starten

Nach erfolgreicher Vorprüfung und bewusster Entscheidung für die Testversion:

```bash
sudo python3 -B wlanfix.py install --build-dir /var/tmp/belabox-wlan-build-test3 --lan-peer "$WLANFIX_LAN_PEER" --accept-experimental
```

Erwartet: `INSTALLIERT FÜR DEN NÄCHSTEN START. Laufender Treiber unverändert.`
Das Original bleibt erhalten. Zusätzliche Sicherung:
`/var/lib/belabox-wlan-fix/5.10.160-belabox/`.
Das Zusatzmodul wird erst beim nächsten Boot verwendet.

Nur nach Erfolg:

```bash
sudo reboot
```

Danach vom Rechner erneut mit `ssh user@BOX-IP` anmelden.

## 6. Startprüfung

```bash
cd /home/user/belabox-wlan-test3/wlan-fix
sudo python3 -B wlanfix.py verify
```

Erwartet: `STARTPRÜFUNG OK`. Geladene Version mit `+wlanfix1`, neuer Boot
und lesbarer Bootanfang sind erforderlich. Journal und direktes Kernelprotokoll
werden auf bestimmte schwere Fehler geprüft. Das ist keine pauschale
Fehlerfreiheit des gesamten Systems und noch kein WLAN-Datenverkehrstest.

## 7. WLAN 0 prüfen

WLAN 0 über die BELABOX-Oberfläche verbinden. LAN bleibt angeschlossen,
WLAN 1 getrennt und die Ausgabe aus:

```bash
nmcli -f GENERAL.STATE,IP4.ADDRESS,IP4.GATEWAY device show wlan0
read -r -p 'Router-IP des verbundenen WLANs: ' WLANFIX_WIFI_PEER
sudo python3 -B wlanfix.py test-wifi --interface wlan0 --peer "$WLANFIX_WIFI_PEER"
```

Erwartet: verbundenes WLAN, fünf Antworten, kein Paketverlust und
`WLAN-KURZTEST OK`. Die Pakete werden ausdrücklich an WLAN gebunden.
Ein Router, der Ping blockiert, ist kein geeignetes Testziel.

Dieser Kurztest ersetzt keine Upload-/Downloadlast, Wiederverbindung oder
mehrstündigen Betrieb. Große Testdownloads müssen blockweise im RAM
verworfen werden; keine Videodaten oder riesigen Logs auf der Box speichern.

## 8. Rückweg zum Original

Auf der erreichbaren Box unter demselben Kernel:

```bash
cd /home/user/belabox-wlan-test3/wlan-fix
sudo python3 -B wlanfix.py rollback --confirm
```

Erwartet: `RÜCKWEG VORBEREITET`. Nur das eigene, prüfsummengeprüfte
Zusatzmodul wird entfernt; eine Kopie bleibt in der Sicherung. Erst nach Erfolg:

```bash
sudo reboot
```

Nach erneuter Anmeldung:

```bash
cat /sys/module/8852be/version
modinfo -n 8852be
```

Version ohne `+wlanfix1`, Modulpfad wieder unter
`kernel/drivers/net/wireless/rockchip_wlan/rtl8852be/`.
Damit kann der ursprüngliche Startfehler zurückkehren.

Bei fehlendem LAN/SSH den Rückweg über eine lokale Konsole durchführen
oder auf die vorbereitete Startkartensicherung zurückgreifen.
Der Offline-Rettungsweg ist noch nicht praktisch freigegeben.
Vor späteren Kernelupdates die Kompatibilität erneut prüfen lassen.

## Quellen, Lizenz und GitHub

Unabhängiges Projekt, keine Herstellerfreigabe von BELABOX, Radxa oder Realtek.
Vorgesehenes GitHub-Konto: [IRL4YOU](https://github.com/IRL4YOU).
Repository- und Release-Link werden erst nach Veröffentlichung ergänzt.

Das Paket enthält die festgelegte Originalquelle, das Patchverfahren,
Bauwerkzeuge und den vollständigen GPL-v2-Text. Herkunft und Lizenzumfang:
`QUELLEN.md`, `vendor/README.md`, `LICENSE`.
Die Testkennzeichnung beschreibt den Prüfstand und beschränkt keine Lizenzrechte.
Private Boxkonfigurationen, SSH-Schlüssel und Stream-Zugangsdaten gehören
nicht in öffentliche Fehlerberichte oder das Repository.
