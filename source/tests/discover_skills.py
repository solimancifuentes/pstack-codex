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

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cwd', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--plugin', default='pstack-codex')
parser.add_argument('--expected-count', type=int)
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
env = dict(os.environ)
stderr_path = args.output.with_suffix('.stderr.txt')
with stderr_path.open('w') as err:
    proc = subprocess.Popen(['codex', 'app-server', '--stdio'], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=err, text=True,
                            bufsize=1, cwd=args.cwd, env=env)
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
        matching = [s for entry in skills.get('data', []) for s in entry.get('skills', [])
                    if args.plugin in (s.get('pluginId') or '') or args.plugin in s.get('path', '')]
        errors = [e for entry in skills.get('data', []) for e in entry.get('errors', [])
                  if args.plugin in e.get('path', '')]
        report = {'initialize': init, 'skills': skills, 'plugins': plugins,
                  'matching_plugin_skills': matching, 'matching_parse_errors': errors,
                  'expected_count': args.expected_count}
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        passed = not errors and bool(matching)
        if args.expected_count is not None:
            passed = passed and len(matching) == args.expected_count
        print(json.dumps({'output': str(args.output.resolve()), 'matching_skill_count': len(matching),
                          'matching_parse_errors': len(errors), 'passed': passed}))
        raise SystemExit(0 if passed else 1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
