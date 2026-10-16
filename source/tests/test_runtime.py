import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]


class RuntimeCLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.package = self.root / "plugin"
        self.launcher = self.package / "tools/runtime.py"
        self.launcher.parent.mkdir(parents=True)
        shutil.copyfile(PROJECT / "runtime/runtime.py", self.launcher)
        self.scripts = self.package / "skills/poteto-mode/scripts"
        self.scripts.mkdir(parents=True)
        for name, text in {"package.json": '{"dependencies":{"commander":"14.0.0"}}', "bun.lock": 'fixture lock\n',
                           "bootstrap.ts": "// Never installs implicitly\n", "orch/orch.ts": "console.log('fixture');\n",
                           "watch-pr/watch-pr": "console.log('fixture');\n"}.items():
            path = self.scripts / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        log = self.package / "skills/show-me-your-work/scripts/log.sh"
        log.parent.mkdir(parents=True)
        log.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$2" >> "$1"\n')
        self.defaults = {"schema_version": 1, "model": "inherit-parent", "reasoning_effort": "inherit-parent",
                         "roles": {}, "panels": {"arena": 2}, "implicit_invocation": {"unslop": True}}
        self.write_json(self.package / "defaults.json", self.defaults)
        self.refresh_manifest()
        self.profile = self.root / "personal/preferences.json"
        self.state = self.root / "state"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.bun_log = self.root / "bun-calls.jsonl"
        bun = self.bin / "bun"
        bun.write_text("#!" + sys.executable + "\n" + '''import json, os, pathlib, sys
with open(os.environ["TEST_BUN_LOG"], "a") as output:
    output.write(json.dumps({"arguments":sys.argv[1:], "cwd":os.getcwd(), "cache":os.environ.get("BUN_INSTALL_CACHE_DIR")})+"\\n")
if sys.argv[1:] == ["--version"]:
    print("fixture-bun-1")
elif sys.argv[1:] == ["install", "--frozen-lockfile", "--ignore-scripts"]:
    commander = pathlib.Path("node_modules/commander")
    commander.mkdir(parents=True, exist_ok=True)
    (commander / "package.json").write_text('{"name":"commander"}')
else:
    print(json.dumps({"arguments":sys.argv[1:], "cwd":os.getcwd()}))
''')
        bun.chmod(0o755)
        self.environment = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ.get("PATH", ""), TEST_BUN_LOG=str(self.bun_log))

    def tearDown(self):
        self.temporary.cleanup()

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def refresh_manifest(self):
        files = {}
        for directory in (self.scripts, self.package / "skills/show-me-your-work/scripts"):
            for path in directory.rglob("*"):
                if path.is_file():
                    files[path.relative_to(self.package).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.write_json(self.package / "tools/helper-sources.json", {"schema_version": 1, "files": files})

    def run_cli(self, *arguments, expected=0, state=None):
        result = subprocess.run([sys.executable, str(self.launcher), "--state-root", str(state or self.state), *arguments],
                                env=self.environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def call_records(self):
        return [json.loads(row) for row in self.bun_log.read_text().splitlines()] if self.bun_log.exists() else []

    def package_hashes(self):
        return {path.relative_to(self.package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.package.rglob("*") if path.is_file()}

    def prepared_runtime(self):
        return next((self.state / "helpers").glob("*/scripts"))

    def test_missing_profile_is_effective_defaults_without_filesystem_writes(self):
        result = json.loads(self.run_cli("profile", "show", "--profile", str(self.profile)).stdout)
        self.assertFalse(result["exists"])
        self.assertEqual(result["effective"], self.defaults)
        self.assertFalse(self.profile.parent.exists())
        self.assertFalse(self.state.exists())
        self.assertFalse(self.call_records())

    def test_profile_dry_run_and_partial_write_preserve_unknown_nested_values(self):
        self.write_json(self.profile, {"newer_plugin": {"retain": 42}, "roles": {"reviewer": {"model": "chosen-future-model", "other": True}}, "panels": {"architect": 3}})
        proposed = self.root / "proposed.json"
        self.write_json(proposed, {"roles": {"reviewer": {"reasoning_effort": "high"}}, "panels": {"arena": 4}})
        original = self.profile.read_bytes()
        preview = json.loads(self.run_cli("profile", "set", "--profile", str(self.profile), "--file", str(proposed), "--dry-run").stdout)
        self.assertEqual(self.profile.read_bytes(), original)
        self.assertEqual(preview["overrides"]["roles"]["reviewer"]["model"], "chosen-future-model")
        saved = json.loads(self.run_cli("profile", "set", "--profile", str(self.profile), "--file", str(proposed), "--yes").stdout)
        self.assertEqual(saved["overrides"]["newer_plugin"], {"retain": 42})
        self.assertEqual(saved["effective"]["panels"], {"arena": 4, "architect": 3})
        self.assertTrue(saved["overrides"]["roles"]["reviewer"]["other"])
        self.assertFalse(self.state.exists())
        self.assertFalse(self.call_records())

    def test_invalid_profile_never_changes_existing_file(self):
        self.write_json(self.profile, {"unknown": ["keep"]})
        original = self.profile.read_bytes()
        invalid = ({"model": 12}, {"model": ""}, {"reasoning_effort": "invented"}, {"roles": {"coder": "string"}},
                   {"panels": {"arena": 0}}, {"panels": {"arena": True}}, {"panels": {"arena": 1.2}}, {"implicit_invocation": {"x": "yes"}})
        proposed = self.root / "invalid.json"
        for value in invalid:
            with self.subTest(value=value):
                self.write_json(proposed, value)
                self.run_cli("profile", "set", "--profile", str(self.profile), "--file", str(proposed), "--yes", expected=1)
                self.assertEqual(self.profile.read_bytes(), original)

    def test_profile_set_requires_explicit_action(self):
        proposed = self.root / "proposal.json"
        self.write_json(proposed, {"model": "inherit-parent"})
        self.run_cli("profile", "set", "--file", str(proposed), "--profile", str(self.profile), expected=2)
        self.assertFalse(self.profile.exists())

    def test_all_help_and_unprepared_tool_never_install(self):
        for arguments in (("--help",), ("profile", "--help"), ("profile", "show", "--help"), ("profile", "set", "--help"),
                          ("tools-setup", "--help"), ("tool", "--help"), ("tool", "orch", "--help")):
            with self.subTest(arguments=arguments):
                self.run_cli(*arguments)
        result = self.run_cli("tool", "orch", "--", "--help", expected=1)
        self.assertIn("No packages were installed", result.stderr)
        self.run_cli("tools-setup", expected=2)
        self.assertFalse(self.state.exists())
        self.assertFalse(self.call_records())

    def test_locked_setup_external_state_and_idempotent_retries(self):
        self.write_json(self.profile, {"user": "exact preserved bytes"})
        original = self.profile.read_bytes()
        before = self.package_hashes()
        first = json.loads(self.run_cli("tools-setup", "--yes").stdout)
        second = json.loads(self.run_cli("tools-setup", "--yes").stdout)
        self.assertFalse(first["already_prepared"])
        self.assertTrue(second["already_prepared"])
        self.assertTrue(Path(first["runtime"]).is_relative_to(self.state))
        calls = self.call_records()
        self.assertEqual([row["arguments"] for row in calls], [["install", "--frozen-lockfile", "--ignore-scripts"], ["--version"]])
        self.assertEqual(calls[0]["cache"], str(self.state / "cache/bun"))
        self.assertEqual(self.profile.read_bytes(), original)
        self.assertEqual(self.package_hashes(), before)

    def test_prepared_dispatch_forwards_arguments_without_installing(self):
        self.run_cli("tools-setup", "--yes")
        before = len(self.call_records())
        result = json.loads(self.run_cli("tool", "orch", "--", "--store", "my store", "--json", "status").stdout)
        self.assertTrue(result["arguments"][0].endswith("orch/orch.ts"))
        self.assertEqual(result["arguments"][1:], ["--store", "my store", "--json", "status"])
        self.assertEqual(len(self.call_records()), before + 1)
        self.assertEqual(Path(result["cwd"]), Path.cwd())

    def test_explicit_setup_repairs_missing_dependencies_and_marker(self):
        self.write_json(self.profile, {"preserve": {"user": "exact bytes"}})
        original_profile = self.profile.read_bytes()
        original_package = self.package_hashes()
        self.run_cli("tools-setup", "--yes")
        runtime = self.prepared_runtime()
        for missing in ("node_modules", "node_modules/.poteto-mode-tools-install-key"):
            with self.subTest(missing=missing):
                target = runtime / missing
                shutil.rmtree(target) if target.is_dir() else target.unlink()
                before = len(self.call_records())
                self.assertIn("Prepared dependencies are missing", self.run_cli("tool", "orch", "--", "status", expected=1).stderr)
                self.assertEqual(len(self.call_records()), before)
                repaired = json.loads(self.run_cli("tools-setup", "--yes").stdout)
                self.assertFalse(repaired["already_prepared"])
                self.assertEqual([row["arguments"] for row in self.call_records()[before:]],
                                 [["install", "--frozen-lockfile", "--ignore-scripts"], ["--version"]])
                self.run_cli("tool", "orch", "--", "status")
                self.assertEqual(self.profile.read_bytes(), original_profile)
                self.assertEqual(self.package_hashes(), original_package)

    def test_explicit_setup_rejects_invalid_receipt_even_with_missing_dependencies(self):
        self.run_cli("tools-setup", "--yes")
        runtime = self.prepared_runtime()
        shutil.rmtree(runtime / "node_modules")
        receipt = runtime.parent / "setup-receipt.json"
        self.write_json(receipt, {"source_key": "different-source", "package_lock_key": "different-lock"})
        original = receipt.read_bytes()
        count = len(self.call_records())
        self.assertIn("receipt does not match", self.run_cli("tools-setup", "--yes", expected=1).stderr)
        self.assertEqual(len(self.call_records()), count)
        self.assertEqual(receipt.read_bytes(), original)
        self.assertFalse((runtime / "node_modules").exists())

    def test_packaged_source_mutation_and_extra_file_are_rejected(self):
        self.run_cli("tools-setup", "--yes")
        count = len(self.call_records())
        original = (self.scripts / "orch/orch.ts").read_text()
        (self.scripts / "orch/orch.ts").write_text("mutated source")
        result = self.run_cli("tool", "orch", "--", "status", expected=1)
        self.assertIn("Packaged helper sources differ", result.stderr)
        (self.scripts / "orch/orch.ts").write_text(original)
        (self.scripts / "unexpected.ts").write_text("injected helper")
        self.run_cli("tools-setup", "--yes", expected=1)
        self.assertEqual(len(self.call_records()), count)

    def test_prepared_source_mutation_and_receipt_mismatch_are_rejected(self):
        self.run_cli("tools-setup", "--yes")
        count = len(self.call_records())
        runtime = self.prepared_runtime()
        script = runtime / "orch/orch.ts"
        original = script.read_bytes()
        script.write_text("changed")
        self.assertIn("Prepared helper sources differ", self.run_cli("tool", "orch", "--", "status", expected=1).stderr)
        script.write_bytes(original)
        self.write_json(runtime.parent / "setup-receipt.json", {"source_key": "unrelated"})
        self.assertIn("receipt does not match", self.run_cli("tool", "orch", "--", "status", expected=1).stderr)
        self.assertEqual(len(self.call_records()), count)

    def test_log_helper_requires_no_bun_setup(self):
        target = self.root / "decisions.tsv"
        self.run_cli("tool", "log", "--", str(target), "planning", "choose", "why", "evidence", "result")
        self.assertEqual(target.read_text(), "planning\n")
        self.assertFalse(self.state.exists())
        self.assertFalse(self.call_records())

    def test_state_inside_plugin_and_symlink_escapes_rejected(self):
        self.run_cli("tools-setup", "--yes", state=self.package / "mutable", expected=1)
        self.assertFalse((self.package / "mutable").exists())
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "linked-state").symlink_to(outside, target_is_directory=True)
        self.run_cli("tools-setup", "--yes", state=self.root / "linked-state", expected=1)
        linked = self.scripts / "orch/orch.ts"
        linked.unlink()
        linked.symlink_to(self.root / "outside-script")
        (self.root / "outside-script").write_text("unsafe")
        self.run_cli("tools-setup", "--yes", expected=1)
        self.assertFalse(self.call_records())

    def test_profile_symlink_write_rejected(self):
        outside = self.root / "other-profile.json"
        outside.write_text('{"protected":true}')
        self.profile.parent.mkdir()
        self.profile.symlink_to(outside)
        proposed = self.root / "proposal.json"
        self.write_json(proposed, {"panels": {"arena": 4}})
        self.run_cli("profile", "set", "--profile", str(self.profile), "--file", str(proposed), "--yes", expected=1)
        self.assertEqual(outside.read_text(), '{"protected":true}')

    def test_versioned_setup_and_return_to_old_source_preserve_profile(self):
        self.write_json(self.profile, {"preserve": {"unknown": "value"}})
        original = self.profile.read_bytes()
        old = json.loads(self.run_cli("tools-setup", "--yes").stdout)
        script = self.scripts / "orch/orch.ts"
        source = script.read_text()
        script.write_text(source + "// next published version\n")
        self.refresh_manifest()
        newer = json.loads(self.run_cli("tools-setup", "--yes").stdout)
        self.assertNotEqual(newer["source_key"], old["source_key"])
        script.write_text(source)
        self.refresh_manifest()
        rollback = json.loads(self.run_cli("tools-setup", "--yes").stdout)
        self.assertTrue(rollback["already_prepared"])
        self.assertEqual(rollback["source_key"], old["source_key"])
        self.assertEqual(self.profile.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
