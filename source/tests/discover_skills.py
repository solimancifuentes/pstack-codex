#!/usr/bin/env python3
"""Ask a fresh native app-server to list skills without starting an LLM turn."""
import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

def matches_plugin_id(plugin_id, selector):
    if not isinstance(plugin_id, str) or '@' not in plugin_id:
        return False
    return plugin_id == selector if '@' in selector else plugin_id.partition('@')[0] == selector


def assess_discovery(skills, plugins, selector, expected_count=None, manifest=None):
    selected = [plugin for marketplace in plugins.get('marketplaces', [])
                for plugin in marketplace.get('plugins', [])
                if matches_plugin_id(plugin.get('id'), selector)]
    rows = [skill for entry in skills.get('data', []) for skill in entry.get('skills', [])
            if matches_plugin_id(skill.get('pluginId'), selector)]
    plugin_ids = sorted({plugin['id'] for plugin in selected} | {skill['pluginId'] for skill in rows})
    state_errors = []
    if len(plugin_ids) != 1:
        state_errors.append('Select exactly one native plugin ID; use --plugin NAME@MARKETPLACE when ambiguous')
    if not selected or any(plugin.get('installed') is not True or plugin.get('enabled') is not True
                           for plugin in selected):
        state_errors.append('The selected native plugin must be installed and enabled')
    unique = {}
    conflicts = []
    roots = {Path(plugin['source']['path']).resolve() for plugin in selected
             if plugin.get('source', {}).get('type') == 'local'
             and Path(plugin['source']['path']).is_absolute()}
    for skill in rows:
        identity = skill['pluginId'], skill['name']
        if identity in unique and any(unique[identity].get(key) != skill.get(key) for key in ('path', 'enabled')):
            conflicts.append(skill)
        unique.setdefault(identity, skill)
        path = Path(skill['path'])
        if path.is_absolute() and path.parent.parent.name == 'skills' and path.name == 'SKILL.md':
            roots.add(path.parent.parent.parent.resolve())
    matching = [skill for skill in unique.values() if skill.get('enabled') is True]
    disabled = [skill for skill in unique.values() if skill.get('enabled') is not True]
    errors = [error for entry in skills.get('data', []) for error in entry.get('errors', [])
              if error.get('path') and Path(error['path']).is_absolute()
              and any(Path(error['path']).resolve().is_relative_to(root) for root in roots)]
    expected = None
    missing = []
    unexpected = []
    if manifest is not None:
        names = [skill['name'] for skill in manifest['skills']]
        if not names or len(set(names)) != len(names) or any(not isinstance(name, str) or not name for name in names):
            raise ValueError('Expected manifest must contain unique, nonempty skill names')
        expected = sorted(selector.partition('@')[0] + ':' + name for name in names)
        actual = {skill['name'] for skill in matching}
        missing = sorted(set(expected) - actual)
        unexpected = sorted(actual - set(expected))
    passed = bool(matching) and not (state_errors or disabled or conflicts or errors or missing or unexpected)
    if expected_count is not None:
        passed = passed and len(matching) == expected_count
    return {'matching_plugin_skills': matching, 'matching_parse_errors': errors,
            'matching_plugin_ids': plugin_ids, 'matching_plugin_roots': sorted(str(root) for root in roots),
            'disabled_plugin_skills': disabled, 'conflicting_skill_rows': conflicts,
            'duplicate_skill_rows': len(rows) - len(unique), 'plugin_state_errors': state_errors,
            'expected_count': expected_count, 'expected_skill_names': expected,
            'missing_expected_skills': missing, 'unexpected_skills': unexpected, 'passed': passed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cwd', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--plugin', default='pstack-codex', help='Exact plugin name or NAME@MARKETPLACE')
    parser.add_argument('--expected-count', type=int)
    parser.add_argument('--expected-manifest', type=Path, help='release.json containing the exact expected skill names')
    args = parser.parse_args()
    manifest = json.loads(args.expected_manifest.read_text()) if args.expected_manifest else None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stderr_path = args.output.with_suffix('.stderr.txt')
    with stderr_path.open('w') as err:
        proc = subprocess.Popen(['codex', 'app-server', '--stdio'], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=err, text=True,
                                bufsize=1, cwd=args.cwd, env=dict(os.environ))
        lines = queue.Queue()

        def read_lines():
            for line in proc.stdout:
                lines.put(line)
            lines.put(None)

        threading.Thread(target=read_lines, daemon=True).start()

        def request(method, params, ident):
            proc.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': ident, 'method': method, 'params': params}) + '\n')
            proc.stdin.flush()
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                try:
                    line = lines.get(timeout=min(1, max(0, deadline-time.monotonic())))
                except queue.Empty:
                    if proc.poll() is not None:
                        raise RuntimeError(f'app-server exited {proc.returncode}; see {stderr_path}')
                    continue
                if not line:
                    raise RuntimeError(f'app-server closed stdout; see {stderr_path}')
                message = json.loads(line)
                if message.get('id') == ident:
                    if 'error' in message:
                        raise RuntimeError(json.dumps(message['error']))
                    return message['result']
            raise TimeoutError(f'{method} did not respond within 45 seconds')

        try:
            init = request('initialize', {'clientInfo': {'name': 'pstack-port-verification', 'version': '1.0'},
                                         'capabilities': {'experimentalApi': True}}, 1)
            proc.stdin.write(json.dumps({'jsonrpc': '2.0', 'method': 'initialized'}) + '\n')
            proc.stdin.flush()
            skills = request('skills/list', {'cwds': [str(args.cwd.resolve())], 'forceReload': True}, 2)
            plugins = request('plugin/list', {'cwds': [str(args.cwd.resolve())],
                                              'marketplaceKinds': ['local'], 'forceRefetch': False}, 3)
            assessment = assess_discovery(skills, plugins, args.plugin, args.expected_count, manifest)
            report = {'initialize': init, 'skills': skills, 'plugins': plugins, **assessment,
                      'expected_manifest': str(args.expected_manifest.resolve()) if args.expected_manifest else None}
            args.output.write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps({'output': str(args.output.resolve()),
                              'matching_skill_count': len(assessment['matching_plugin_skills']),
                              'matching_parse_errors': len(assessment['matching_parse_errors']),
                              'passed': assessment['passed']}))
            return 0 if assessment['passed'] else 1
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


if __name__ == '__main__':
    raise SystemExit(main())
