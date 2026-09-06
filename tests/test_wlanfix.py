import contextlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
import wlanfix


class SourceTests(unittest.TestCase):
    def test_symbol_crcs(self):
        self.assertEqual(build.validate_symbol_crcs('0x1234 symbol', '0x1234 symbol kernel EXPORT_SYMBOL'), 1)
        for imported in ('', '0x5678 symbol', '0x1234 unknown'):
            with self.subTest(imported=imported), self.assertRaises(build.Refused):
                build.validate_symbol_crcs(imported, '0x1234 symbol kernel EXPORT_SYMBOL')

    def test_pinned_archive_and_patch(self):
        p = build.profile()
        archive = build.BASE / 'vendor/source.tar.gz'
        self.assertEqual(build.digest(archive), p['source_archive_sha256'])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            build.unpack(archive, path)
            source = path / 'driver'
            build.patch_source(source, p)
            code = (source / 'phl/phl_cmd_ser.c').read_text()
            self.assertIn('pq_init(drv, &cser->stslist);', code)
            self.assertIn('pq_deinit(drv, &cser->stslist);', code)
            self.assertNotIn('INIT_LIST_HEAD(&cser->stslist.queue);', code)
            self.assertIn(p['fixed_version'], (source / 'include/rtw_version.h').read_text())
            self.assertIn('GCC_VER_49 := 1 # wlanfix', (source / 'Makefile').read_text())
            self.assertIn('Modified for BELABOX WLAN Fix on 2026-09-03', code)
            self.assertIn('Modified for BELABOX WLAN Fix on 2026-09-03',
                          (source / 'include/rtw_version.h').read_text())
            self.assertIn('Modified for BELABOX WLAN Fix on 2026-09-03',
                          (source / 'Makefile').read_text())
            with self.assertRaises(build.Refused):
                build.patch_source(source, p)

    def test_reject_path_traversal_and_links(self):
        for name, kind in [('../escape', tarfile.REGTYPE), ('/absolute', tarfile.REGTYPE),
                           ('driver/link', tarfile.SYMTYPE), ('wrong/file', tarfile.REGTYPE)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                path = Path(temp)
                archive = path / 'bad.tar.gz'
                with tarfile.open(archive, 'w:gz') as tf:
                    item = tarfile.TarInfo(name)
                    item.type = kind
                    item.linkname = '/etc/passwd'
                    tf.addfile(item)
                with self.assertRaises(build.Refused):
                    build.unpack(archive, path)

    def test_non_linux_refused_before_file_access(self):
        with patch('build.platform.system', return_value='Darwin'):
            with self.assertRaisesRegex(build.Refused, 'Linux'):
                build.check(build.profile())

    def test_wrong_architecture_refused(self):
        with patch('build.platform.system', return_value='Linux'), \
             patch('build.platform.machine', return_value='x86_64'):
            with self.assertRaisesRegex(build.Refused, 'Architektur'):
                build.check(build.profile())

    def test_wrong_kernel_refused(self):
        with patch('build.platform.system', return_value='Linux'), \
             patch('build.platform.machine', return_value='aarch64'), \
             patch('build.platform.release', return_value='6.1.0'):
            with self.assertRaisesRegex(build.Refused, 'Kernel'):
                build.check(build.profile())


class BootLogTests(unittest.TestCase):
    def test_dmesg_supplies_missing_journal_boot(self):
        with patch('wlanfix.run', side_effect=['-- No entries --', '[0.0] Linux version test']):
            self.assertIn('Linux version', wlanfix.checked_kernel_log())

    def test_partial_logs_never_pass(self):
        with patch('wlanfix.run', side_effect=['some late event', 'another late event']):
            with self.assertRaisesRegex(build.Refused, 'Bootanfang'):
                wlanfix.checked_kernel_log()

    def test_error_in_either_source_never_hidden(self):
        for logs in [('BUG: spinlock bad magic', 'Linux version test'),
                     ('Linux version test', 'Unknown symbol test')]:
            with self.subTest(logs=logs), patch('wlanfix.run', side_effect=logs):
                with self.assertRaisesRegex(build.Refused, 'Kernel-Fehlermeldung'):
                    wlanfix.checked_kernel_log()

    def test_unavailable_source_requires_other_complete_log(self):
        with patch('wlanfix.run', side_effect=[OSError('unavailable'), 'Linux version test']):
            wlanfix.checked_kernel_log()


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.original = self.root / 'kernel/8852be.ko'
        self.original.parent.mkdir()
        self.original.write_bytes(b'original module')
        self.target = self.root / 'updates/belabox-wlan-fix/8852be.ko'
        self.state = self.root / 'state/kernel'
        self.build_dir = self.root / 'build'
        (self.build_dir / 'driver').mkdir(parents=True)
        self.module = self.build_dir / 'driver/8852be.ko'
        self.module.write_bytes(b'fixed module')
        self.p = build.profile()
        self.p['original_sha256'] = build.digest(self.original)
        self.info = {'sha256': build.digest(self.module)}
        (self.build_dir / 'build-result.json').write_text(json.dumps({
            'sha256': self.info['sha256'], 'profile_sha256': build.digest(build.BASE / 'profile.json')}))
        self.calls = []
        self.fail_depmod = False

        def fake_run(*args):
            self.calls.append(args)
            if args[0] == 'depmod':
                if self.fail_depmod:
                    self.fail_depmod = False
                    raise OSError('simulated depmod failure')
                return ''
            if args[:3] == ('modinfo', '-F', 'signer'):
                return ''
            if args[:2] == ('modinfo', '-n'):
                return str(self.target if self.target.exists() else self.original)
            raise AssertionError(args)

        self.stack = contextlib.ExitStack()
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        for target, value in [('wlanfix.profile', self.p), ('wlanfix.check', self.original),
                              ('wlanfix.paths', (self.original, self.target, self.state)),
                              ('wlanfix.require_lan', None), ('wlanfix.require_supported_boot', None),
                              ('wlanfix.inspect_module', self.info), ('wlanfix.boot_id', 'boot-before'),
                              ('wlanfix.platform.release', self.p['kernel']),
                              ('wlanfix.os.geteuid', 0)]:
            self.stack.enter_context(patch(target, return_value=value))
        self.stack.enter_context(patch('wlanfix.run', side_effect=fake_run))

    def tearDown(self):
        self.stack.close()
        self.tmp.cleanup()

    def install(self):
        wlanfix.install(self.build_dir, 'mock-lan-peer', True)

    def test_install_keeps_original_and_does_not_reload(self):
        self.install()
        self.assertEqual(self.original.read_bytes(), b'original module')
        self.assertEqual(self.target.read_bytes(), b'fixed module')
        self.assertEqual((self.state / 'original.ko').read_bytes(), b'original module')
        self.assertEqual(json.loads((self.state / 'state.json').read_text())['status'], 'staged')
        self.assertFalse(any(c[0] in ('reboot', 'modprobe', 'systemctl') for c in self.calls))

    def test_plan_does_not_write_anything(self):
        wlanfix.plan(self.build_dir, 'mock-lan-peer')
        self.assertFalse(self.state.exists())
        self.assertFalse(self.target.exists())
        self.assertFalse(any(c[0] == 'depmod' for c in self.calls))

    def test_failed_rollback_restores_previous_override(self):
        self.install()
        self.fail_depmod = True
        with self.assertRaises(OSError):
            wlanfix.rollback(True)
        self.assertEqual(self.target.read_bytes(), b'fixed module')
        self.assertEqual(json.loads((self.state / 'state.json').read_text())['status'], 'staged')

    def test_explicit_experimental_acceptance_required(self):
        with self.assertRaises(build.Refused):
            wlanfix.install(self.build_dir, 'mock-lan-peer', False)
        self.assertFalse(self.state.exists())
        self.assertFalse(self.target.exists())

    def test_repeated_install_is_noop(self):
        self.install()
        before = self.target.stat().st_mtime_ns
        self.calls.clear()
        self.install()
        self.assertEqual(self.target.stat().st_mtime_ns, before)
        self.assertFalse(any(c[0] == 'depmod' for c in self.calls))

    def test_unknown_override_not_overwritten(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b'other owner')
        with self.assertRaises(build.Refused):
            self.install()
        self.assertEqual(self.target.read_bytes(), b'other owner')

    def test_depmod_failure_reverts_own_file(self):
        self.fail_depmod = True
        with self.assertRaises(OSError):
            self.install()
        self.assertFalse(self.target.exists())
        self.assertEqual(self.original.read_bytes(), b'original module')
        self.assertEqual(json.loads((self.state / 'state.json').read_text())['status'], 'failed-reverted')

    def test_modified_build_result_rejected(self):
        (self.build_dir / 'build-result.json').write_text('{}')
        with self.assertRaises(build.Refused):
            self.install()
        self.assertFalse(self.target.exists())

    def test_rollback_recoverable_and_original_untouched(self):
        self.install()
        wlanfix.rollback(True)
        self.assertFalse(self.target.exists())
        self.assertEqual(self.original.read_bytes(), b'original module')
        self.assertEqual((self.state / 'removed-fixed.ko').read_bytes(), b'fixed module')
        self.assertEqual(json.loads((self.state / 'state.json').read_text())['status'], 'rolled-back')
        wlanfix.rollback(True)

    def test_rollback_does_not_remove_foreign_modified_file(self):
        self.install()
        self.target.write_bytes(b'external change')
        with self.assertRaises(build.Refused):
            wlanfix.rollback(True)
        self.assertEqual(self.target.read_bytes(), b'external change')

    def test_backup_tampering_blocks_reinstall(self):
        self.install()
        wlanfix.rollback(True)
        (self.state / 'original.ko').write_bytes(b'bad backup')
        with self.assertRaises(build.Refused):
            self.install()
        self.assertFalse(self.target.exists())

    def test_atomic_write_rejects_symlink(self):
        link = self.root / 'link'
        link.symlink_to(self.original)
        with self.assertRaises(build.Refused):
            wlanfix.atomic_bytes(link, b'bad')
        self.assertEqual(self.original.read_bytes(), b'original module')

    def test_incomplete_state_requires_rollback(self):
        self.install()
        self.target.unlink()
        with self.assertRaisesRegex(build.Refused, 'Unvollständige'):
            self.install()
        wlanfix.rollback(True)
        self.install()
        self.assertTrue(self.target.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
