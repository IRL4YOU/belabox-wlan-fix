#!/usr/bin/env python3
"""Separate, version-locked WLAN test package. Never restarts the box or services."""
import argparse
from contextlib import contextmanager
import fcntl
import ipaddress
import json
import os
import platform
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from build import BASE, Refused, check, digest, inspect_module, profile, require, run


def paths(p):
    modules = Path('/lib/modules') / p['kernel']
    return (modules / p['original_relative'],
            modules / 'updates/belabox-wlan-fix/8852be.ko',
            Path('/var/lib/belabox-wlan-fix') / p['kernel'])


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def atomic_bytes(path, data, mode=0o600):
    require(not path.is_symlink(), 'Symbolischer Link als Ziel abgelehnt: ' + str(path))
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.wlanfix-', delete=False) as f:
        temporary = Path(f.name)
        try:
            os.fchmod(f.fileno(), mode)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temporary.unlink()
            raise
    try:
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_state(directory, data):
    atomic_bytes(directory / 'state.json', (json.dumps(data, indent=2) + '\n').encode())


@contextmanager
def lock(directory):
    for parent in (directory, directory.parent):
        require(not parent.is_symlink(), 'Verlinktes Statusverzeichnis nicht unterstützt.')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    lockfile = directory / 'operation.lock'
    require(not lockfile.is_symlink(), 'Verlinkte Sperrdatei abgelehnt.')
    with lockfile.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refused('Eine andere WLAN-Paketoperation läuft bereits.')
        yield


def require_lan(peer):
    ipaddress.ip_address(peer)
    route = json.loads(run('ip', '-j', 'route', 'get', peer))
    require(len(route) == 1 and 'dev' in route[0], 'Keine eindeutige Route zum LAN-Rechner.')
    dev = route[0]['dev']
    require(re.fullmatch(r'[a-zA-Z0-9_.:-]+', dev) is not None and dev != 'lo', 'Ungültige LAN-Schnittstelle.')
    path = Path('/sys/class/net') / dev
    require(not (path / 'wireless').exists() and not (path / 'phy80211').exists(),
            'Zugriffsweg läuft über WLAN. Installation nur über LAN oder lokale Konsole vorbereiten.')
    require((path / 'operstate').read_text().strip() == 'up', 'LAN-Schnittstelle ist nicht aktiv.')
    print('Geprüfter LAN-Zugriffsweg:', dev)


def require_supported_boot(p):
    # This test release deliberately does not rewrite any initramfs/boot configuration.
    boot = Path('/boot')
    require(boot.is_dir(), '/boot fehlt.')
    for file in boot.rglob('*'):
        name = file.name.lower()
        require(not any(word in name for word in ('initrd', 'initramfs', 'uinitrd')),
                'Initramfs-Bootlayout noch nicht unterstützt: ' + str(file))
    config = (Path('/lib/modules') / p['kernel'] / 'build/.config').read_text()
    require('CONFIG_INITRAMFS_SOURCE=""' in config or '# CONFIG_BLK_DEV_INITRD is not set' in config,
            'Eingebettetes Initramfs nicht sicher ausgeschlossen.')
    extlinux = boot / 'extlinux/extlinux.conf'
    require(extlinux.is_file(), 'Nur das geprüfte Extlinux-Bootlayout wird unterstützt.')
    boot_text = extlinux.read_text()
    require(not re.search(r'^\s*initrd\s', boot_text, re.I | re.M),
            'Extlinux verweist auf ein Initramfs; Testpaket bricht sicher ab.')
    require(re.findall(r'^\s*linux\s+(\S+)\s*$', boot_text, re.I | re.M) == ['/boot/Image'],
            'Unbekannter Kernel-/FIT-Bootpfad. Keine Installation.')


def read_state(directory, p):
    file = directory / 'state.json'
    require(file.is_file() and not file.is_symlink(), 'Kein eigener Installationsstatus gefunden.')
    state = json.loads(file.read_text())
    require(state.get('kernel') == p['kernel'] and
            state.get('original_sha256') == p['original_sha256'], 'Unpassender Installationsstatus.')
    require(re.fullmatch('[0-9a-f]{64}', state.get('fixed_sha256', '')) is not None,
            'Ungültige Modulprüfsumme im Installationsstatus.')
    return state


def check_selected(expected):
    selected = Path(run('modinfo', '-n', '8852be'))
    require(selected.resolve() == expected.resolve(),
            'Modulauswahl unerwartet: ' + str(selected) + '. Keine Aktivierung durchführen.')


def preflight(build_dir, peer):
    p = profile()
    original = check(p)
    require_lan(peer)
    require_supported_boot(p)
    original_path, target, directory = paths(p)
    require(original.resolve() == original_path.resolve(), 'Originalpfad nicht eindeutig.')
    for parent in (target, target.parent, target.parent.parent):
        require(not parent.is_symlink(), 'Verlinktes Modulziel wird nicht unterstützt.')
    result_file = build_dir / 'build-result.json'
    require(result_file.is_file(), 'Erfolgreicher Bauabschluss fehlt.')
    result = json.loads(result_file.read_text())
    require(result.get('profile_sha256') == digest(BASE / 'profile.json'), 'Bauprofil weicht ab.')
    module = build_dir / 'driver/8852be.ko'
    info = inspect_module(module, p, original)
    require(info['sha256'] == result.get('sha256'), 'Modul seit Bauabschluss verändert.')
    require(not run('modinfo', '-F', 'signer', str(original)), 'Signiertes Original derzeit nicht unterstützt.')
    return p, original, target, directory, module, info


def plan(build_dir, peer):
    p, original, target, directory, module, info = preflight(build_dir, peer)
    require(not target.exists() and not target.is_symlink(), 'Zusatzmodul bereits vorhanden; zuerst Status/Rückweg prüfen.')
    check_selected(original)
    print('INSTALLATIONS-VORPRÜFUNG OK. Keine Änderungen.')
    print('Geplantes Zusatzmodul:', target)
    print('Geplante Sicherung:', directory / 'original.ko')
    print('Original bleibt unverändert:', original)
    print('Geprüfte Modul-SHA256:', info['sha256'])


def install(build_dir, peer, confirmed):
    require(confirmed, 'Installation erfordert --accept-experimental. Noch keine Änderungen.')
    require(os.geteuid() == 0, 'Installation als root ausführen.')
    p, original, target, directory, module, info = preflight(build_dir, peer)
    with lock(directory):
        state_file = directory / 'state.json'
        if target.exists():
            state = read_state(directory, p)
            require(state.get('status') == 'staged', 'Unvollständiger Status; zuerst rollback ausführen.')
            require(digest(target) == state['fixed_sha256'] == info['sha256'],
                    'Vorhandenes Zusatzmodul stimmt nicht überein; kein Überschreiben.')
            check_selected(target)
            print('Diese Testversion ist bereits für den nächsten Start ausgewählt. Nichts verändert.')
            return
        check_selected(original)
        if state_file.exists():
            old = read_state(directory, p)
            require(old.get('status') in ('rolled-back', 'failed-reverted'),
                    'Unvollständige frühere Installation: zuerst rollback ausführen.')
        backup = directory / 'original.ko'
        if backup.exists():
            require(not backup.is_symlink() and digest(backup) == p['original_sha256'], 'Sicherung stimmt nicht.')
        else:
            atomic_bytes(backup, original.read_bytes())
        require(digest(backup) == p['original_sha256'], 'Sicherungsprüfung fehlgeschlagen.')
        state = {'kernel': p['kernel'], 'original_sha256': p['original_sha256'],
                 'fixed_sha256': info['sha256'], 'fixed_version': p['fixed_version'],
                 'package_version': p['package_version'], 'install_boot_id': boot_id(),
                 'status': 'preparing'}
        write_state(directory, state)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        try:
            atomic_bytes(target, module.read_bytes(), mode=0o644)
            require(digest(target) == info['sha256'], 'Kopierprüfung fehlgeschlagen.')
            run('depmod', '-a', p['kernel'])
            check_selected(target)
        except BaseException:
            # Remove only the exact file created by this operation, never a foreign module.
            if target.is_file() and not target.is_symlink() and digest(target) == info['sha256']:
                target.unlink()
                run('depmod', '-a', p['kernel'])
            state['status'] = 'failed-reverted' if not target.exists() else 'needs-review'
            write_state(directory, state)
            raise
        state['status'] = 'staged'
        write_state(directory, state)
    print('INSTALLIERT FÜR DEN NÄCHSTEN START. Laufender Treiber unverändert.')
    print('Originalmodul bleibt am bisherigen Ort; zusätzliche Sicherung:', directory / 'original.ko')
    print('Kein automatischer Neustart. Nach geplantem Neustart: sudo python3 wlanfix.py verify')


def rollback(confirmed):
    require(confirmed, 'Rückweg erfordert --confirm. Noch keine Änderungen.')
    require(os.geteuid() == 0, 'Rückweg als root ausführen.')
    p = profile()
    require(platform.release() == p['kernel'], 'Rückweg nur unter dem zugehörigen Kernel ausführen.')
    original, target, directory = paths(p)
    require(directory.is_dir(), 'Keine Installation dieses Pakets vorhanden.')
    require(original.is_file() and digest(original) == p['original_sha256'],
            'Originalmodul wurde anderweitig verändert; manuellen Rückweg prüfen.')
    require(not any(path.is_symlink() for path in (original, target, target.parent, target.parent.parent)),
            'Unerwarteter Link im Modulpfad.')
    with lock(directory):
        state = read_state(directory, p)
        require(not (directory / 'original.ko').is_symlink() and
                digest(directory / 'original.ko') == p['original_sha256'], 'Sicherung stimmt nicht.')
        removed = None
        if target.exists():
            require(digest(target) == state['fixed_sha256'], 'Zusatzmodul wurde fremd verändert; wird nicht entfernt.')
            # Recoverable move to our backup directory, not deletion.
            removed = target.read_bytes()
            atomic_bytes(directory / 'removed-fixed.ko', removed)
            target.unlink()
        try:
            run('depmod', '-a', p['kernel'])
            check_selected(original)
        except BaseException:
            if removed is not None and not target.exists():
                atomic_bytes(target, removed, mode=0o644)
                run('depmod', '-a', p['kernel'])
            raise
        state['status'] = 'rolled-back'
        write_state(directory, state)
    print('RÜCKWEG VORBEREITET: Originaltreiber wird beim nächsten Start verwendet.')
    print('Nur unser Zusatzmodul entfernt; Kopie unter', directory / 'removed-fixed.ko')
    print('Sicherungen bleiben erhalten. Kein automatischer Neustart und kein Entladen.')


def checked_kernel_log():
    """Keep errors from every available source; require a complete boot source."""
    logs = []
    for command in [('journalctl', '-k', '-b', '0', '--no-pager', '-o', 'short-monotonic'),
                    ('dmesg', '--color=never')]:
        try:
            log = run(*command)
        except (OSError, subprocess.CalledProcessError):
            continue
        logs.append(log)
    combined = '\n'.join(logs)
    require(not re.search(r'BUG:|Oops:|Kernel panic|Unknown symbol|invalid module format', combined),
            'Kernel-Fehlermeldung vorhanden; Test nicht bestanden, Protokoll untersuchen.')
    require(any('Linux version ' in log for log in logs),
            'Kernelprotokoll enthält keinen Bootanfang; Prüfung unvollständig.')
    return combined


def verify():
    p = profile()
    check(p, need_build=False)
    original, target, directory = paths(p)
    state = read_state(directory, p)
    require(state['status'] == 'staged', 'Paket ist nicht als installiert vorgemerkt.')
    require(boot_id() != state['install_boot_id'], 'Noch kein neuer Boot seit Installation; Starttest fehlt.')
    require(target.is_file() and digest(target) == state['fixed_sha256'], 'Installiertes Modul verändert oder fehlt.')
    check_selected(target)
    loaded = Path('/sys/module/8852be/version')
    require(loaded.is_file() and loaded.read_text().strip() == p['fixed_version'], 'Korrigierter Treiber nicht geladen.')
    checked_kernel_log()
    require(Path('/sys/module/8852be/holders').is_dir(), 'Modulzustand unvollständig.')
    print('STARTPRÜFUNG OK: Fix geladen, geprüfte Kernel-Fehlermuster nicht vorhanden.')
    print('Das ist noch KEIN bestandener WLAN- oder Langzeittest. WLAN verbinden und test-wifi ausführen.')


def test_wifi(interface, peer):
    verify()
    require(re.fullmatch(r'[a-zA-Z0-9_.:-]+', interface) is not None, 'Ungültiger Schnittstellenname.')
    address = ipaddress.ip_address(peer)
    require(address.version == 4 and not address.is_loopback and not address.is_multicast, 'IPv4-Testziel im WLAN erforderlich.')
    net = Path('/sys/class/net') / interface
    require((net / 'phy80211').exists(), 'Keine WLAN-Schnittstelle.')
    require((net / 'device/driver/module').resolve().name == '8852be', 'WLAN-Gerät gehört nicht zum korrigierten Treiber.')
    own = json.loads(run('ip', '-j', 'address', 'show'))
    require(not any(a.get('local') == peer for item in own for a in item.get('addr_info', [])), 'Testziel darf nicht die eigene Adresse sein.')
    link = run('iw', 'dev', interface, 'link')
    require('Connected to ' in link, 'WLAN ist noch nicht mit einem Access Point verbunden.')
    print('Teste fünf Pakete ausdrücklich über', interface, '(nicht über LAN).')
    result = subprocess.run(['ping', '-I', interface, '-c', '5', '-W', '2', peer],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            env={**os.environ, 'LC_ALL': 'C'})
    print(result.stdout)
    require(result.returncode == 0 and re.search(r'\b5 (?:packets )?received', result.stdout) is not None,
            'WLAN-Pakettest nicht vollständig bestanden.')
    print('WLAN-KURZTEST OK. Langzeittest und Neuinstallationstest stehen separat aus.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check', help='Nur Kompatibilität prüfen')
    dry = sub.add_parser('plan', help='Vollständige Installationsvorprüfung, ohne Änderungen')
    dry.add_argument('--build-dir', type=Path, required=True)
    dry.add_argument('--lan-peer', required=True)
    ins = sub.add_parser('install', help='Nach Testfreigabe für nächsten Boot installieren, ohne Neustart')
    ins.add_argument('--build-dir', type=Path, required=True)
    ins.add_argument('--lan-peer', required=True, help='LAN-IP des steuernden Rechners')
    ins.add_argument('--accept-experimental', action='store_true')
    back = sub.add_parser('rollback', help='Eigenes Zusatzmodul entfernen, Original unverändert lassen')
    back.add_argument('--confirm', action='store_true')
    sub.add_parser('verify', help='Nach Neustart geladenen Fix und Kernelmeldungen prüfen')
    wifi = sub.add_parser('test-wifi', help='Nach manueller WLAN-Verbindung gezielt WLAN testen')
    wifi.add_argument('--interface', default='wlan0')
    wifi.add_argument('--peer', required=True, help='Erreichbares IPv4-Ziel im eigenen WLAN, z. B. Router')
    args = parser.parse_args()
    try:
        if args.command == 'check':
            check(profile())
            print('KOMPATIBEL für die Testversion. Keine Änderungen.')
        elif args.command == 'install':
            install(args.build_dir, args.lan_peer, args.accept_experimental)
        elif args.command == 'plan':
            plan(args.build_dir, args.lan_peer)
        elif args.command == 'rollback':
            rollback(args.confirm)
        elif args.command == 'verify':
            verify()
        elif args.command == 'test-wifi':
            test_wifi(args.interface, args.peer)
    except (Refused, OSError, subprocess.CalledProcessError, ValueError, KeyError) as exc:
        print('ABBRUCH: ' + str(exc), file=sys.stderr)
        sys.exit(1)
