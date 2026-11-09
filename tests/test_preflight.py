import json
from pathlib import Path
import tempfile
import unittest

from g1devkit.actions import inspect_action
from g1devkit.config import ROOT, load
from g1devkit.preflight import preflight
from g1devkit.reports import save_report


class ActionTests(unittest.TestCase):
    def inspect(self, content, dof=29, **kwargs):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'stage.json'
            path.write_text(content if isinstance(content, str) else json.dumps(content), encoding='utf-8')
            return inspect_action(path, dof, **kwargs)

    def test_existing_shape_and_explicit_conversion(self):
        for width, dof, conversion, target_count in [(18, 23, '18_to_12', 11),
                                                   (12, 29, '12_to_18', 17),
                                                   (18, 29, 'unchanged', 17),
                                                   (12, 23, 'unchanged', 11)]:
            with self.subTest(width=width, dof=dof):
                report = self.inspect([{'data': [2.5] + [0.1] * (width - 1)}], dof)
                self.assertEqual(report['legacy_conversions'][conversion], 1)
                self.assertEqual(report['target_count'], target_count)
                self.assertEqual(report['total_duration_s'], 2.5)
                self.assertFalse(report['motion_validated'])
                self.assertFalse(report['executed'])

    def test_invalid_stage_data_and_duplicates(self):
        invalid = [[], {}, [1], [{'data': [1] * 13}], [{'data': [0] * 12}],
                   [{'data': [-1] + [0] * 11}], [{'data': [1, True] + [0] * 10}],
                   [{'data': [1, '0'] + [0] * 10}], [{'data': [1, float('nan')] + [0] * 10}],
                   [{'data': [1, float('inf')] + [0] * 10}],
                   [{'data': [1, 10 ** 400] + [0] * 10}],
                   '[{"data":[],"data":[1,0,0,0,0,0,0,0,0,0,0,0]}]']
        for content in invalid:
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    self.inspect(content)
        with self.assertRaises(ValueError):
            self.inspect([{'data': [1] + [0.1] * 11}], max_abs_rad=float('nan'))
        # A target that 23-DOF drops must still be reviewed for nonfinite/out-of-bound data.
        values = [1] + [0] * 17
        values[17] = 8
        with self.assertRaises(ValueError):
            self.inspect([{'data': values}], dof=23, max_abs_rad=2)


class PreflightTests(unittest.TestCase):
    def test_real_baseline_is_reviewed_without_importing_robot_dependencies(self):
        report = preflight(load())
        checks = {check['check']: check for check in report['checks']}
        for name in ('subscriber_command_port', 'subscriber_status_port', 'action_action_port',
                     'subscriber_action_forward'):
            self.assertEqual(checks[name]['status'], 'pass')
        self.assertEqual(checks['device_baseline']['status'], 'blocked')
        self.assertFalse(report['offline_checks_passed'])
        self.assertFalse(report['adapter_programs_executed'])
        self.assertFalse(report['network_accessed'])

    def test_port_mismatch_is_reported(self):
        config = load()
        config['ports']['command'] = 19006
        report = preflight(config)
        check = next(c for c in report['checks'] if c['check'] == 'subscriber_command_port')
        self.assertEqual(check['status'], 'blocked')
        self.assertEqual(check['detail'], {'configured': 19006, 'source_literal': 2006})

    def test_literal_sources_resources_and_case_sensitive_filenames(self):
        # Importing this fixture would fail and write a marker: preflight must only parse AST.
        (ROOT / '.local').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as temporary:
            folder = Path(temporary)
            marker = folder / 'executed.txt'
            subscriber = folder / 'subscriber.py'
            subscriber.write_text("raise RuntimeError('DO NOT IMPORT')\nUDP_RECV_PORT=2006\nUDP_SEND_PORT=3840\nChannelFactoryInitialize(0, 'eth0')\ndef forward_to_action_service():\n socket.sendto(b'', ('127.0.0.1',6789))\n", encoding='utf-8')
            action = folder / 'action.py'
            action.write_text(f"open({str(marker)!r}, 'w').write('unexpected')\nUDP_PORT=6789\nUDP_IP='127.0.0.1'\nChannelFactoryInitialize(0, 'eth0')\nclass Handler:\n def __init__(self):\n  self.action_map={{'2025':{{'path':'/old/output/Welcome'}}}}\n", encoding='utf-8')
            config = load()
            config['robot'].update(model='test-fixture', dof=29, firmware='fixture',
                                   interface='eth0', sdk_commit='a' * 40)
            config['services'].update(subscriber=subscriber.relative_to(ROOT).as_posix(),
                                      action=action.relative_to(ROOT).as_posix())
            (folder / 'Welcome.json').write_text(json.dumps([{'data': [1] + [0] * 17}]), encoding='utf-8')
            report = preflight(config, folder)
            self.assertTrue(report['offline_checks_passed'])
            self.assertEqual(report['action_files'][0]['command'], '2025')
            self.assertFalse(marker.exists())
            (folder / 'Welcome.json').rename(folder / 'other.json')
            (folder / 'welcome.json').write_text(json.dumps([{'data': [1] + [0] * 17}]), encoding='utf-8')
            report = preflight(config, folder)
            self.assertFalse(report['offline_checks_passed'])
            self.assertEqual(report['summary']['blocked'], 1)

    def test_malformed_configuration_has_actionable_errors(self):
        cases = [[], {'robot': []}, {'ports': []}, {'services': []}, {'resources': []},
                 {'robot': {'dof': True}}, {'robot': {'sdk_commit': 'main'}},
                 {'robot': {'interface': 5}}, {'robot': {'state_topic': 'wrong'}},
                 {'services': {'action': []}}, {'resources': {'actions': ''}}]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'config.json'
            for patch in cases:
                data = load()
                if not isinstance(patch, dict):
                    data = patch
                else:
                    for name, value in patch.items():
                        if isinstance(value, dict):
                            data[name].update(value)
                        else:
                            data[name] = value
                with self.subTest(patch=patch):
                    path.write_text(json.dumps(data), encoding='utf-8')
                    with self.assertRaises(ValueError):
                        load(path)

    def test_reports_are_local_exclusive_and_do_not_overwrite(self):
        folder = ROOT / '.local/reports'
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder) as temporary:
            path = Path(temporary) / 'result.json'
            save_report({'passed': True}, path)
            with self.assertRaises(FileExistsError):
                save_report({'passed': False}, path)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), {'passed': True})
        with self.assertRaises(ValueError):
            save_report({}, ROOT / 'public-report.json')


if __name__ == '__main__':
    unittest.main()
