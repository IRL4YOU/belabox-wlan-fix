# Unveränderte Treiberquelle

`source.tar.gz` enthält den unveränderten Unterbaum `src/` des in
`../profile.json` festgelegten Radxa-Commits, mit Archivpräfix `driver/`.
Die Prüfsumme ist im Profil festgelegt. Die eigentliche Korrektur wird erst
beim Bau angewendet. Upstream-Urheber- und Lizenzhinweise bleiben erhalten.

Erzeugung aus einem geprüften Git-Checkout:

```sh
git archive --format=tar --prefix=driver/ 554dbbb89380915ad89e4727a5d5c566d6d788fe:src | gzip -n > source.tar.gz
```

Quelle: https://github.com/radxa-pkg/8852be-dkms
Treiberlizenz: GNU GPL Version 2, gemäß den Quelldateien.
