# Veröffentlichung über IRL4YOU

Repository: https://github.com/IRL4YOU/belabox-wlan-fix

Dieses Repository enthält das Quellpaket,
die Bau-/Installationswerkzeuge, die vollständige festgelegte Treiberquelle,
Tests, Rückweg und Lizenzhinweise. Es enthält keine privaten
Boxkonfigurationen, Kamera-/WLAN-Zugangsdaten oder Projektgesamtsicherungen.

## Testversion, keine Produktivfreigabe

`0.1.0-test3` wird als Vorabversion bereitgestellt. Abgeschlossene Prüfungen
und die ausdrücklich noch offenen Tests stehen in `TESTSTAND.md`.
Die Veröffentlichung zum Nachvollziehen und kontrollierten Testen ersetzt
keine Dauerstabilitätsprüfung. Der bekannte Startfehler wurde gezielt
behoben; sämtliche früheren Box-Hänger sind dadurch nicht erklärt.

## Quellcode und Download

`python3 -B make_release.py` führt die Pakettests aus und erzeugt das
Quellarchiv samt SHA-256-Datei unter `dist/`. Beide Dateien gehören als
Anhänge zur entsprechenden GitHub-Vorabversion. Der Treiber wird auf der
kompatiblen Box gebaut; kein vorgebautes Modul wird separat verteilt.

Vor jedem neuen Release:

1. Exakten Quell-/Bauzustand, Tests und Änderungsumfang dokumentieren.
2. Dateien und verschachtelte Archive auf private Informationen prüfen.
3. Lizenz- und Urheberhinweise erhalten; Änderungen kennzeichnen.
4. Quellarchiv neu bauen, Prüfsumme und Inhalt prüfen.
5. Quellstand und passendes Archiv gemeinsam versioniert bereitstellen.

GitHub-Hilfe: https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository

## Homepage

Die IRL4YOU-Homepage soll nur eine kurze Einordnung und einen Link auf
dieses Repository anbieten. Anleitung, Prüfstand und Downloads bleiben
zentral auf GitHub. `HOMEPAGE-ANLEITUNG.md` ist trotz des historischen Namens
die vollständige Schritt-für-Schritt-Installationsanleitung dieses Pakets.

Die Testkennzeichnung beschreibt technische Grenzen; sie beschränkt keine
Rechte aus der GPL. Lizenztext und Herkunft siehe `LICENSE`, `QUELLEN.md`
und `vendor/README.md`.
