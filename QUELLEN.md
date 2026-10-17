# Quellen und Lizenzhinweise

- Unveränderte Treiberquelle: https://github.com/radxa-pkg/8852be-dkms
- Festgelegter Commit: `554dbbb89380915ad89e4727a5d5c566d6d788fe`.
- Betroffene Stelle: `src/phl/phl_cmd_ser.c`, ursprüngliche Zeile 662.
- Queue-Hilfsfunktionen: `src/phl/phl_util.c`, `pq_init` und `pq_push`.
- Der Treiber enthält GPL-v2-Urheber-/Lizenzhinweise von Realtek; diese
  bleiben im unveränderten Quellarchiv und beim Bau erhalten.
- Vollständiger GPL-v2-Text liegt unter `vendor/COPYING-GPL-2.0.txt`.
  Bezugsquelle: https://github.com/torvalds/linux/blob/master/LICENSES/preferred/GPL-2.0
- Die neu erstellten Paketwerkzeuge in diesem Ordner werden ebenfalls
  unter GPL-2.0-only bereitgestellt. Es gibt keine Funktionsgarantie.

Der Fix ist ein lokaler, nicht als Herstellerfreigabe ausgegebener
Korrekturvorschlag. Ein erfolgreicher Bau ersetzt keinen Hardwaretest.
Die im Quellcode eingetragene Versionsgleichheit allein wurde nicht als
Beweis für eine vollständig identische Original-Baukonfiguration verwendet.
Zusätzlich wurden die betroffene Folge im installierten Modul und die
benötigten Symbol-Prüfsummen untersucht.

## Bedingungen vor einer öffentlichen Weitergabe

Technische Arbeitsnotiz, keine Rechtsberatung. Das Paket darf erst als
Veröffentlichungskandidat bezeichnet werden, wenn mindestens Folgendes geprüft ist:

- Unveränderte Urheber-, Lizenz- und Gewährleistungshinweise bleiben erhalten.
- Der vollständige GPL-v2-Text wird zusammen mit dem Paket ausgeliefert.
- Vollständiger, maschinenlesbarer korrespondierender Quellcode einschließlich
  der verwendeten Änderungen und Bauwerkzeuge ist am selben Downloadort erhältlich.
- Die beim Bau geänderten Dateien tragen einen sichtbaren Hinweis mit Datum und
  Art der Änderung. Der Builder ergänzt diese Hinweise seit dem Stand 2026-09-03.
- Binärmodul und genau dazugehöriges Quellpaket werden eindeutig versioniert;
  nicht das alte Testarchiv neben einem neu gebauten Binärmodul veröffentlichen.
- Empfänger erhalten das Paket unter GPL Version 2 ohne zusätzliche Einschränkungen.
- Realtek, Radxa und BELABOX werden nicht als Herausgeber oder Gewährleistende
  dieses unabhängigen Fixes dargestellt. Marken-/Namensfragen bleiben getrennt.

Eine bloße Verlinkung auf das Upstream-Repository ist für einen veränderten
konkreten Binärstand nicht der sichere Auslieferungsweg. Dieses Paket führt die
festgelegte Originalquelle und den reproduzierbaren Änderungsschritt deshalb mit.
Vor einer echten Veröffentlichung soll der fertige Kandidat nochmals vollständig
gegen GPL v2 Abschnitte 1 bis 3 geprüft werden; bei kommerzieller oder sonst
risikoreicher Verteilung zusätzlich qualifizierten Rechtsrat einholen.
