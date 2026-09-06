#!/usr/bin/env python3
"""Reproducible source build only. Never installs or loads a module."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent


class Refused(RuntimeError):
    pass


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def require(ok, reason):
    if not ok:
        raise Refused(reason)


def profile():
    return json.loads((BASE / 'profile.json').read_text())


def check(p, need_build=True):
    require(platform.system() == 'Linux', 'Nur auf der unterstützten Linux-Box ausführen.')
    require(platform.machine() == p['architecture'], 'Nicht unterstützte Architektur.')
    require(platform.release() == p['kernel'], 'Kernel stimmt nicht mit dem geprüften Profil überein.')
    model = Path('/proc/device-tree/model').read_text().rstrip('\0\n')
    require(model == p['board'], 'Nicht unterstütztes Board: ' + model)
    os_data = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines()
                   if '=' in line)
    require(os_data.get('ID', '').strip('"') == p['os_id'] and
            os_data.get('VERSION_ID', '').strip('"') == p['os_version'], 'Nicht unterstütztes Betriebssystem.')
    for cmd in ('modinfo', 'dpkg-query'):
        require(shutil.which(cmd), 'Benötigtes Programm fehlt: ' + cmd)
    package = run('dpkg-query', '-W', '-f=${Version}', p['kernel_package'])
    require(package == p['kernel_package_version'], 'Abweichende BELABOX-Kernelpaketversion.')
    original = Path('/lib/modules') / p['kernel'] / p['original_relative']
    require(original.is_file() and not original.is_symlink(), 'Originalmodul fehlt oder ist ein Link.')
    require(digest(original) == p['original_sha256'], 'Originaltreiber-Prüfsumme weicht ab. Kein automatischer Eingriff.')
    require(run('modinfo', '-F', 'version', str(original)) == p['driver_version'], 'Abweichende Treiberversion.')
    devices = Path('/sys/bus/pci/devices').glob('*')
    require(any((d / 'vendor').read_text().strip() == p['pci_vendor'] and
                (d / 'device').read_text().strip() == p['pci_device'] for d in devices),
            'RTL8852BE-PCIe-Gerät nicht gefunden.')
    if need_build:
        for cmd in ('make', 'gcc', 'ld', 'objdump', 'nm'):
            require(shutil.which(cmd), 'Build-Programm fehlt: ' + cmd)
        require(run('gcc', '-dumpversion').split('.')[0] == '11', 'Erste Testversion erfordert GCC 11.')
        headers = Path('/lib/modules') / p['kernel'] / 'build'
        for name, key in (('.config', 'config_sha256'), ('Module.symvers', 'symvers_sha256')):
            require((headers / name).is_file() and digest(headers / name) == p[key],
                    'Nicht passende Kernel-Baudatei: ' + name)
        require(os.access(headers / 'scripts/mod/modpost', os.X_OK), 'Kernel modpost fehlt.')
        require(p['kernel'] in (headers / 'include/generated/utsrelease.h').read_text(), 'Falsche Header-Version.')
    return original


def unpack(archive, destination):
    with tarfile.open(archive, 'r:gz') as tf:
        for item in tf.getmembers():
            parts = Path(item.name).parts
            require(parts and parts[0] == 'driver' and '..' not in parts and
                    not Path(item.name).is_absolute(), 'Unsicherer Archivpfad.')
            require(item.isfile() or item.isdir(), 'Links/Spezialdateien sind im Quellarchiv nicht erlaubt.')
        tf.extractall(destination)


def patch_source(src, p):
    ser = src / 'phl/phl_cmd_ser.c'
    version = src / 'include/rtw_version.h'
    makefile = src / 'Makefile'
    require(digest(ser) == p['source_file_sha256'], 'Unerwartete SER-Quelle; Patch abgebrochen.')
    require(digest(version) == p['source_version_sha256'], 'Unerwartete Versionsdatei.')
    require(digest(makefile) == p['source_makefile_sha256'], 'Unerwartete Build-Datei.')
    code = ser.read_text()
    old = '\tINIT_LIST_HEAD(&cser->stslist.queue);'
    deinit = '\t_os_spinlock_free(drv, &cser->_lock);'
    require(code.count(old) == 1 and code.count(deinit) == 1, 'Patchstellen nicht eindeutig.')
    change_notice = ('/* Modified for BELABOX WLAN Fix on 2026-09-03: initialize and '\
                     'deinitialize the SER status queue lock. */\n')
    require(change_notice not in code, 'Änderungshinweis bereits vorhanden.')
    code = change_notice + code
    code = code.replace(old, '\tpq_init(drv, &cser->stslist);')
    code = code.replace(deinit, '\tpq_deinit(drv, &cser->stslist);\n' + deinit)
    ser.write_text(code)
    text = version.read_text()
    require(text.count(p['driver_version']) == 1, 'Versionsmarkierung nicht eindeutig.')
    version_notice = ('/* Modified for BELABOX WLAN Fix on 2026-09-03: identify the '\
                      'corrected module build. */\n')
    version.write_text(version_notice + text.replace(p['driver_version'], p['fixed_version']))
    # GCC 11 is explicitly checked before building. The legacy decimal-version
    # probe is unnecessary and otherwise calls a missing `bc` even with a CLI override.
    lines = makefile.read_text().splitlines(keepends=True)
    probes = [i for i, line in enumerate(lines) if line.startswith('GCC_VER_49 :=')]
    require(len(probes) == 1, 'Compiler-Prüfstelle nicht eindeutig.')
    lines.insert(0, '# Modified for BELABOX WLAN Fix on 2026-09-03: use prechecked GCC 11.\n')
    lines[probes[0] + 1] = 'GCC_VER_49 := 1 # wlanfix builder requires GCC 11\n'
    makefile.write_text(''.join(lines))


def inspect_module(module, p, original):
    require(module.is_file(), 'Kompiliertes Modul fehlt.')
    require(run('modinfo', '-F', 'name', str(module)) == p['driver'], 'Falscher Modulname.')
    require(run('modinfo', '-F', 'version', str(module)) == p['fixed_version'], 'Fix-Versionsmarkierung fehlt.')
    for field in ('vermagic', 'depends'):
        require(run('modinfo', '-F', field, str(module)) == run('modinfo', '-F', field, str(original)),
                'Modulmerkmal weicht ab: ' + field)
    # Verify every imported kernel symbol CRC, not just the vermagic string.
    symvers = Path('/lib/modules') / p['kernel'] / 'build/Module.symvers'
    imported = run('modprobe', '--show-modversions', str(module))
    count = validate_symbol_crcs(imported, symvers.read_text())
    # Keep structural evidence from the corrected SER object for manual audit.
    obj = module.parent / 'phl/phl_cmd_ser.o'
    assembly = run('objdump', '-dr', str(obj))
    fn = assembly.split('<_phl_ser_mdl_init>:', 1)
    require(len(fn) == 2, 'SER-Initialisierung nicht gefunden.')
    fn = fn[1].split('\n\n', 1)[0]
    require('pq_init' in fn and 'pq_push' in fn and fn.index('pq_init') < fn.index('pq_push'),
            'pq_init vor pq_push im erzeugten Modulobjekt nicht belegt.')
    return {'sha256': digest(module), 'version': p['fixed_version'],
            'vermagic': run('modinfo', '-F', 'vermagic', str(module)),
            'depends': run('modinfo', '-F', 'depends', str(module)),
            'srcversion': run('modinfo', '-F', 'srcversion', str(module)),
            'symbol_crcs_checked': count}


def validate_symbol_crcs(imported, reference):
    expected = {}
    for line in reference.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            expected[parts[1]] = int(parts[0], 16)
    require(bool(imported.strip()), 'Keine Modul-Symbolversionen gefunden.')
    for line in imported.splitlines():
        crc, symbol = line.split()[:2]
        require(symbol in expected and int(crc, 16) == expected[symbol], 'Unpassendes Kernelsymbol: ' + symbol)
    return len(imported.splitlines())


def build(destination):
    p = profile()
    original = check(p)
    for cmd in ('modprobe',):
        require(shutil.which(cmd), 'Benötigtes Programm fehlt: ' + cmd)
    archive = BASE / 'vendor/source.tar.gz'
    require(digest(archive) == p['source_archive_sha256'], 'Quellarchiv-Prüfsumme stimmt nicht.')
    destination = destination.absolute()
    require(not destination.exists(), 'Build-Ziel existiert bereits; neuen leeren Zielpfad wählen.')
    require(destination.parent.is_dir(), 'Übergeordnetes Build-Verzeichnis fehlt.')
    require(shutil.disk_usage(destination.parent).free > 1024**3, 'Mindestens 1 GiB freier Platz nötig; nicht /tmp verwenden.')
    require(not any(c.isspace() for c in str(destination)), 'Build-Pfad darf keine Leerzeichen enthalten.')
    destination.mkdir(mode=0o700)
    unpack(archive, destination)
    src = destination / 'driver'
    patch_source(src, p)
    command = ['make', '-C', '/lib/modules/' + p['kernel'] + '/build',
               'M=' + str(src), 'ARCH=arm64', 'CROSS_COMPILE=',
               'CONFIG_RTL8852BE=m', 'CONFIG_RTKM=m', 'GCC_VER_49=1', '-j2', 'modules']
    print('Bau läuft mit zwei parallelen Jobs. Protokoll:', destination / 'build.log', flush=True)
    with (destination / 'build.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env={
            **os.environ, 'KBUILD_BUILD_TIMESTAMP': 'Thu Jan 15 23:24:20 UTC 2026',
            'KBUILD_BUILD_USER': 'belabox-wlan-fix', 'KBUILD_BUILD_HOST': 'reproducible'})
    require(result.returncode == 0, 'Build fehlgeschlagen; build.log prüfen. Nichts installiert.')
    metadata = inspect_module(src / '8852be.ko', p, original)
    metadata.update(package_version=p['package_version'], profile_sha256=digest(BASE / 'profile.json'),
                    source_commit=p['source_commit'], source_archive_sha256=p['source_archive_sha256'],
                    gcc=run('gcc', '-dumpfullversion'), command=command,
                    built_at=datetime.now(timezone.utc).isoformat(),
                    hardware_tested=False)
    (destination / 'build-result.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('BUILD GEPRÜFT. Noch NICHT installiert oder geladen.', flush=True)
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Nur Kompatibilität und Bauvoraussetzungen prüfen')
    parser.add_argument('--output', type=Path, help='Neues Build-Verzeichnis auf der Box, z. B. /var/tmp/wlanfix-build-1')
    args = parser.parse_args()
    try:
        if args.check:
            check(profile())
            print('KOMPATIBEL für den Bau der Testversion. Noch kein Funktionstest.')
        elif args.output:
            build(args.output)
        else:
            parser.error('--check oder --output angeben')
    except (Refused, OSError, subprocess.CalledProcessError, ValueError) as exc:
        print('ABBRUCH: ' + str(exc), file=sys.stderr)
        sys.exit(1)
