#!/usr/bin/env python3
"""Create a source-only test archive with deterministic metadata and checksum."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

BASE = Path(__file__).resolve().parent


def main():
    subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(BASE / 'tests'), '-v'], check=True)
    p = json.loads((BASE / 'profile.json').read_text())
    source = BASE / 'vendor/source.tar.gz'
    if hashlib.sha256(source.read_bytes()).hexdigest() != p['source_archive_sha256']:
        raise RuntimeError('Quellarchiv-Prüfsumme stimmt nicht')
    files = [f for f in BASE.rglob('*') if f.is_file() and f.name != '.DS_Store' and
             not set(f.relative_to(BASE).parts).intersection({'dist', '__pycache__', '.git'})]
    if any(f.is_symlink() for f in files):
        raise RuntimeError('Keine Links im Auslieferungspaket erlaubt')
    destination = BASE / 'dist'
    destination.mkdir(exist_ok=True)
    archive = destination / ('belabox-wlan-fix-' + p['package_version'] + '.tar.gz')
    with archive.open('wb') as output, gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w', format=tarfile.USTAR_FORMAT) as tf:
            for file in sorted(files):
                data = file.read_bytes()
                info = tarfile.TarInfo('wlan-fix/' + file.relative_to(BASE).as_posix())
                info.mode = 0o644
                info.uid = info.gid = info.mtime = 0
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(archive.suffix + '.sha256').write_text(checksum + '  ' + archive.name + '\n')
    print('TESTPAKET (keine Hardware-Freigabe):', archive)
    print('SHA256:', checksum)


if __name__ == '__main__':
    main()
