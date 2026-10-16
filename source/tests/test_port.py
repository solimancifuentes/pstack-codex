import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from unittest import mock
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pstack", PROJECT / "pstack.py")
port = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(port)


def variant_release(release, destination, version, legacy=False):
    """Create a valid alternate release fixture, retaining all source integrity checks."""
    destination = Path(destination)
    shutil.copytree(release, destination)
    manifest = port.read_json(destination / "release.json")
    for relative in ("plugin/plugin.json", "plugin/.codex-plugin/plugin.json"):
        path = destination / relative
        metadata = port.read_json(path)
        metadata["version"] = version
        port.write_json(path, metadata)
    manifest["port_version"] = version
    if legacy:
        manifest.pop("profile_mode", None)
        defaults = destination / "plugin/defaults.json"
        if defaults.exists():
            defaults.rename(destination / "plugin/preferences.json")
    manifest["payload"] = port.tree(destination / "plugin")
    identity = {"source_commit": manifest["source_commit"], "source": manifest["source"],
                "payload": manifest["payload"], "adapters": manifest["adapters"],
                "manager": manifest["manager_sha256"]}
    manifest["release"] = manifest["source_commit"][:12] + "-" + port.sha(port.json_bytes(identity))[:12]
    port.write_json(destination / "release.json", manifest)
    final = destination.with_name(manifest["release"])
    destination.rename(final)
    port.verify_payload(final)
    return final


class NativeFixture(port.Installation):
    fail_add = False

    def check_native_scope(self):
        pass

    def native(self, action, marketplace_name):
        cache = self.cache(marketplace_name)
        if action == "remove":
            if cache.exists():
                shutil.rmtree(cache)
        else:
            if self.fail_add:
                raise port.PortError("fixture native install failure")
            if cache.exists():
                shutil.rmtree(cache)
            shutil.copytree(self.root / "active/plugin", cache)
        return "{}"


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        cls.build = port.build(PROJECT, output=Path(cls.scratch.name))
        cls.release = Path(cls.build["path"])

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def test_deterministic_build_and_full_coverage(self):
        second = port.build(PROJECT, output=Path(self.scratch.name))
        self.assertEqual(second["release"], self.build["release"])
        self.assertEqual(len(port.verify_payload(self.release)["skills"]), 54)
        manifest = port.read_json(self.release / "release.json")
        implicit = {row["name"] for row in manifest["skills"] if row["allow_implicit_invocation"]}
        self.assertEqual(implicit, {"setup-pstack", "unslop"})
        self.assertIn("Must always apply.", next(row["description"] for row in manifest["skills"] if row["name"] == "unslop"))

    def test_shared_build_never_embeds_supplied_user_profile(self):
        profile = {"schema_version": 1, "model": "PRIVATE_MODEL_SENTINEL_8d5e", 
                   "roles": {"judge": {"model": "PRIVATE_ROLE_SENTINEL_f09b"}},
                   "implicit_invocation": {"bro": True, "unslop": False},
                   "always_apply": [], "private-note": "PRIVATE_PROFILE_SENTINEL_5a7d"}
        supplied = json.loads(json.dumps(profile))
        customized = port.build(PROJECT, output=Path(self.scratch.name), profile=profile)
        self.assertEqual(customized["release"], self.build["release"])
        self.assertEqual(profile, supplied)
        manifest = port.verify_payload(customized["path"])
        self.assertEqual(manifest["profile_mode"], "external")
        self.assertEqual(manifest["preferences"], port.read_json(self.release / "plugin/defaults.json"))
        self.assertFalse((self.release / "plugin/preferences.json").exists())
        for path in self.release.rglob("*"):
            if path.is_file():
                data = path.read_bytes()
                self.assertNotIn(b"PRIVATE_MODEL_SENTINEL_8d5e", data, str(path))
                self.assertNotIn(b"PRIVATE_ROLE_SENTINEL_f09b", data, str(path))
                self.assertNotIn(b"PRIVATE_PROFILE_SENTINEL_5a7d", data, str(path))

    def test_mode_entrypoint_loads_complete_workflow_without_injection_overflow(self):
        mode = self.release / "plugin/skills/poteto-mode"
        entrypoint = (mode / "SKILL.md").read_text()
        self.assertLess(len(entrypoint.encode()), 1400)
        self.assertIn("[WORKFLOW.md](WORKFLOW.md)", entrypoint)
        workflow = (mode / "WORKFLOW.md").read_text()
        self.assertIn("## Principles", workflow)
        self.assertIn("## Playbooks", workflow)
        self.assertIn("## Subagents", workflow)
        self.assertGreater(len(workflow), len(entrypoint))

    def copy_project(self, temp):
        target = Path(temp) / "project"
        shutil.copytree(PROJECT, target, ignore=shutil.ignore_patterns("build", "__pycache__"))
        return target

    def test_modified_pinned_source_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            project = self.copy_project(temp)
            (project / "upstream/pstack/skills/bro/SKILL.md").write_text("changed")
            with self.assertRaisesRegex(port.PortError, "Pinned source differs"):
                port.build(project)

    def test_adapter_context_conflict_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            project = self.copy_project(temp)
            spec = port.read_json(project / "adapters/spec.json")
            spec["files"][0]["sha256"] = "0" * 64
            port.write_json(project / "adapters/spec.json", spec)
            with self.assertRaisesRegex(port.PortError, "Adapter conflict"):
                port.build(project)

    def test_unadapted_active_cursor_instruction_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            project = self.copy_project(temp)
            spec = port.read_json(project / "adapters/spec.json")
            row = next(row for row in spec["files"] if row["source"].endswith("SKILL.md"))
            with (project / "adapters" / row["overlay"]).open("a") as output:
                output.write('\nSpawn environment: "cloud" now.\n')
            with self.assertRaisesRegex(port.PortError, "Unadapted runtime instruction"):
                port.build(project)

    def test_payload_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / "release"
            shutil.copytree(self.release, copy)
            (copy / "plugin/skills/bro/SKILL.md").write_text("changed")
            with self.assertRaisesRegex(port.PortError, "Release payload changed"):
                port.verify_payload(copy)


class LifecycleFixture:
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        cls.release = Path(port.build(PROJECT, output=Path(cls.scratch.name))["path"])

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.user_home = Path(self.temp.name)
        self.installation = NativeFixture(self.user_home)
        port.write_json(self.installation.marketplace, {"name": "existing-personal", "plugins": [{"name": "ponytail", "custom": "keep"}]})
        self.original = {}
        for name in port.CONSOLIDATE:
            path = self.user_home / ".agents/skills" / name
            shutil.copytree(PROJECT / "standalone-originals" / name, path)
            self.original[name] = port.tree(path)
        unrelated = self.user_home / ".agents/skills/deslop"
        unrelated.mkdir()
        (unrelated / "SKILL.md").write_text("preserve this")

    def tearDown(self):
        self.temp.cleanup()

class LifecycleTests(LifecycleFixture, unittest.TestCase):
    def test_install_is_idempotent_and_preserves_unrelated_content(self):
        self.installation.install(self.release, migrate_standalone=True)
        state = self.installation.state()
        self.assertTrue(self.installation.verify()["installed"])
        self.assertEqual((self.user_home / ".agents/skills/deslop/SKILL.md").read_text(), "preserve this")
        self.assertEqual(self.installation.catalog()["plugins"][0], {"name": "ponytail", "custom": "keep"})
        for name in port.CONSOLIDATE:
            self.assertFalse((self.user_home / ".agents/skills" / name).exists())
        self.assertTrue(self.installation.install(self.release)["already_installed"])
        self.assertEqual(self.installation.state(), state)

    def test_dry_run_has_no_mutations(self):
        before = port.tree(self.user_home)
        self.assertTrue(self.installation.install(self.release, True, migrate_standalone=True)["dry_run"])
        self.assertEqual(port.tree(self.user_home), before)

    def test_full_rollback_preserves_later_unrelated_additions(self):
        self.installation.install(self.release, migrate_standalone=True)
        catalog = self.installation.catalog()
        catalog["plugins"].append({"name": "later-plugin", "custom": 7})
        port.write_json(self.installation.marketplace, catalog)
        preferences = self.installation.root / "preferences.json"
        profile = port.read_json(preferences)
        profile["personal-note"] = "keep my later preference"
        port.write_json(preferences, profile)
        self.installation.rollback("before-install")
        self.assertEqual([row["name"] for row in self.installation.catalog()["plugins"]], ["ponytail", "later-plugin"])
        for name, hashes in self.original.items():
            self.assertEqual(port.tree(self.user_home / ".agents/skills" / name), hashes)
        self.assertEqual(port.read_json(preferences)["personal-note"], "keep my later preference")
        self.assertFalse(self.installation.verify()["installed"])

    def test_changed_owned_cache_stops_update_without_mutation(self):
        self.installation.install(self.release)
        cache = self.installation.cache(self.installation.state()["marketplace_name"])
        (cache / "skills/bro/SKILL.md").write_text("local cache edit")
        state = self.installation.state()
        with self.assertRaisesRegex(port.PortError, "cache differs"):
            self.installation.install(self.release)
        self.assertEqual(self.installation.state(), state)

    def test_rollback_refuses_new_standalone_conflict(self):
        self.installation.install(self.release, migrate_standalone=True)
        path = self.user_home / ".agents/skills/bro"
        path.mkdir()
        (path / "SKILL.md").write_text("later user work")
        before = port.tree(self.user_home)
        with self.assertRaisesRegex(port.PortError, "Rollback conflict"):
            self.installation.rollback("before-install")
        self.assertEqual(port.tree(self.user_home), before)

    def test_native_install_failure_restores_prior_layout(self):
        self.installation.fail_add = True
        with self.assertRaisesRegex(port.PortError, "native install failure"):
            self.installation.install(self.release, migrate_standalone=True)
        self.assertFalse(self.installation.state()["active"])
        self.assertEqual(self.installation.catalog()["plugins"], [{"name": "ponytail", "custom": "keep"}])
        for name, hashes in self.original.items():
            self.assertEqual(port.tree(self.user_home / ".agents/skills" / name), hashes)

    def test_helper_missing_dependencies_never_installs(self):
        self.installation.install(self.release)
        before = port.tree(self.user_home)
        with self.assertRaisesRegex(port.PortError, "No packages were installed"):
            self.installation.run_tool("orch", ["--help"])
        self.assertEqual(port.tree(self.user_home), before)

    def test_changed_preference_is_not_overwritten(self):
        self.installation.install(self.release)
        path = self.installation.root / "preferences.json"
        customized = b'{"schema_version":1, "roles":{"reviewer":{"model":"user-choice"}}, "panels":{"arena":3}}\n'
        path.write_bytes(customized)
        self.assertTrue(self.installation.install(self.release)["already_installed"])
        self.assertEqual(path.read_bytes(), customized)

    def test_ordinary_install_preserves_customized_standalone_skills(self):
        path = self.user_home / ".agents/skills/unslop/SKILL.md"
        path.write_text(path.read_text() + "\nA user customization must survive ordinary install.\n")
        before = port.tree(self.user_home / ".agents/skills")
        self.installation.install(self.release)
        self.assertEqual(port.tree(self.user_home / ".agents/skills"), before)
        self.assertEqual(self.installation.state()["migration"]["standalone"], {})
        self.installation.rollback("before-install")
        self.assertEqual(port.tree(self.user_home / ".agents/skills"), before)

    def test_existing_profile_survives_first_install_byte_for_byte(self):
        path = self.installation.root / "preferences.json"
        path.parent.mkdir(parents=True)
        customized = b'{ "schema_version":1, "model":"user-choice", "personal-note":"do not package me" }\n'
        path.write_bytes(customized)
        self.installation.install(self.release)
        self.assertEqual(path.read_bytes(), customized)
        self.assertTrue(self.installation.verify()["installed"])

    def test_late_migration_request_fails_without_mutation(self):
        self.installation.install(self.release)
        before = port.tree(self.user_home)
        with self.assertRaisesRegex(port.PortError, "before-install"):
            self.installation.install(self.release, migrate_standalone=True)
        self.assertEqual(port.tree(self.user_home), before)
        for name, expected in self.original.items():
            self.assertEqual(port.tree(self.user_home / ".agents/skills" / name), expected)

    def test_new_user_gets_shared_defaults_without_migration(self):
        self.installation.install(self.release)
        self.assertEqual(port.read_json(self.installation.root / "preferences.json"),
                         port.read_json(self.release / "plugin/defaults.json"))
        for name, expected in self.original.items():
            self.assertEqual(port.tree(self.user_home / ".agents/skills" / name), expected)




class SimulatedCrash(BaseException):
    pass


class RecoveryTests(LifecycleFixture, unittest.TestCase):
    def crash_at(self, point):
        def crash(name):
            if name == point:
                raise SimulatedCrash(name)
        self.installation.checkpoint = crash

    def test_interrupted_install_restores_every_standalone_and_can_retry(self):
        self.crash_at("consolidated:bro")
        with self.assertRaises(SimulatedCrash):
            self.installation.install(self.release, migrate_standalone=True)
        self.assertTrue(self.installation.transaction_path.exists())
        self.assertFalse((self.user_home / ".agents/skills/bro").exists())
        resumed = NativeFixture(self.user_home)
        self.assertEqual(resumed.recover()["outcome"], "previous-installation-restored")
        for name, hashes in self.original.items():
            self.assertEqual(port.tree(self.user_home / ".agents/skills" / name), hashes)
        self.assertFalse(resumed.recover()["pending"])
        self.assertTrue(resumed.install(self.release, migrate_standalone=True)["installed"])

    def test_interrupted_rollback_finishes_and_preserves_unrelated_additions(self):
        self.installation.install(self.release, migrate_standalone=True)
        self.crash_at("restored:bro")
        with self.assertRaises(SimulatedCrash):
            self.installation.rollback("before-install")
        catalog = self.installation.catalog()
        catalog["plugins"].append({"name": "later", "value": 99})
        port.write_json(self.installation.marketplace, catalog)
        resumed = NativeFixture(self.user_home)
        self.assertEqual(resumed.recover()["outcome"], "before-install-restored")
        for name, hashes in self.original.items():
            self.assertEqual(port.tree(self.user_home / ".agents/skills" / name), hashes)
        self.assertEqual(resumed.catalog()["plugins"][-1], {"name": "later", "value": 99})
        self.assertFalse(resumed.verify()["installed"])
        self.assertFalse(resumed.recover()["pending"])

    def test_failed_restore_copy_can_be_recovered(self):
        self.installation.install(self.release, migrate_standalone=True)
        with mock.patch.object(port.shutil, "copytree", side_effect=OSError("disk copy failed")):
            with self.assertRaisesRegex(port.PortError, "recover --yes"):
                self.installation.rollback("before-install")
        self.assertTrue(self.installation.transaction_path.exists())
        self.assertEqual(self.installation.recover()["outcome"], "before-install-restored")
        for name, hashes in self.original.items():
            self.assertEqual(port.tree(self.user_home / ".agents/skills" / name), hashes)

    def test_recovery_rejects_changed_user_skill_without_overwriting(self):
        self.crash_at("consolidated:bro")
        with self.assertRaises(SimulatedCrash):
            self.installation.install(self.release, migrate_standalone=True)
        changed = self.user_home / ".agents/skills/bro"
        changed.mkdir()
        (changed / "SKILL.md").write_text("new local work")
        with self.assertRaisesRegex(port.PortError, "Recovery conflict"):
            NativeFixture(self.user_home).recover()
        self.assertEqual((changed / "SKILL.md").read_text(), "new local work")
        self.assertTrue(self.installation.transaction_path.exists())

    def test_committed_install_recovery_finishes_without_reverting(self):
        self.crash_at("state-committed")
        with self.assertRaises(SimulatedCrash):
            self.installation.install(self.release)
        resumed = NativeFixture(self.user_home)
        self.assertEqual(resumed.recover()["outcome"], "installation-completed")
        self.assertTrue(resumed.verify()["installed"])

    def test_interrupted_update_recovers_previous_cache_and_state(self):
        self.installation.install(self.release)
        original_state = self.installation.state()
        candidate_root = self.user_home / "candidate"
        candidate_source = candidate_root / "pstack"
        shutil.copytree(PROJECT / "upstream/pstack", candidate_source)
        (candidate_source / "README.md").write_text("Updated source archive documentation")
        commit = "a" * 40
        port.write_json(candidate_root / "snapshot.json", {"repository": port.REPOSITORY, "commit": commit, "files": port.tree(candidate_source)})
        candidate = port.build(PROJECT, candidate_source, commit, self.user_home / "build")
        self.crash_at("native-installed")
        with self.assertRaises(SimulatedCrash):
            self.installation.install(candidate["path"])
        resumed = NativeFixture(self.user_home)
        self.assertEqual(resumed.recover()["outcome"], "previous-installation-restored")
        self.assertEqual(resumed.state(), original_state)
        self.assertTrue(resumed.verify()["installed"])

    def test_interrupted_version_change_recovers_previous_profile_and_migration(self):
        legacy = variant_release(self.release, self.user_home / "legacy", version="0.1.0", legacy=True)
        self.installation.install(legacy, migrate_standalone=True)
        previous = self.installation.state()
        preferences = self.installation.root / "preferences.json"
        customized = b'{"schema_version":1,"personal-note":"keep during interruption","panels":{"arena":3}}\n'
        preferences.write_bytes(customized)
        self.crash_at("native-installed")
        with self.assertRaises(SimulatedCrash):
            self.installation.install(self.release)
        catalog = self.installation.catalog()
        catalog["plugins"].append({"name": "added-during-operation", "custom": "keep"})
        port.write_json(self.installation.marketplace, catalog)
        resumed = NativeFixture(self.user_home)
        self.assertTrue(resumed.recover(dry_run=True)["dry_run"])
        self.assertEqual(resumed.recover()["outcome"], "previous-installation-restored")
        self.assertEqual(resumed.state(), previous)
        self.assertEqual(preferences.read_bytes(), customized)
        self.assertEqual([entry for entry in resumed.catalog()["plugins"] if entry["name"] != port.PLUGIN],
                         [{"name": "ponytail", "custom": "keep"}, {"name": "added-during-operation", "custom": "keep"}])
        self.assertTrue(resumed.verify()["installed"])

    def test_recovery_rejects_tamper_in_previous_version_cache(self):
        legacy = variant_release(self.release, self.user_home / "legacy", version="0.1.0", legacy=True)
        self.installation.install(legacy)
        self.crash_at("native-installed")
        with self.assertRaises(SimulatedCrash):
            self.installation.install(self.release)
        old_cache = self.installation.cache(self.installation.state()["marketplace_name"], "0.1.0")
        (old_cache / "skills/bro/SKILL.md").write_text("unowned change in previous version cache")
        before = port.tree(self.user_home)
        with self.assertRaisesRegex(port.PortError, "cache changed|cache differs"):
            NativeFixture(self.user_home).recover()
        self.assertEqual(port.tree(self.user_home), before)
        self.assertTrue(self.installation.transaction_path.exists())

    def test_dead_process_does_not_leave_stale_operation_lock(self):
        self.installation.root.mkdir(parents=True)
        lockfile = self.installation.root / ".operation.lock"
        code = "import fcntl, os, sys; f=open(sys.argv[1], 'a+'); fcntl.flock(f, fcntl.LOCK_EX); os._exit(0)"
        subprocess.run([sys.executable, "-c", code, str(lockfile)], check=True)
        with self.installation.locked():
            self.assertTrue(lockfile.exists())

    def test_customized_standalone_is_rejected_before_any_mutation(self):
        path = self.user_home / ".agents/skills/unslop/SKILL.md"
        path.write_text(path.read_text() + "\nA later user preference.\n")
        before = port.tree(self.user_home)
        with self.assertRaisesRegex(port.PortError, "audited migration baseline"):
            self.installation.install(self.release, migrate_standalone=True)
        self.assertEqual(port.tree(self.user_home), before)

    def test_adapter_archive_mutation_is_rejected(self):
        copy = self.user_home / "candidate-release"
        shutil.copytree(self.release, copy)
        (copy / "adapters/CODEX.md").write_text("modified archived adapter")
        with self.assertRaisesRegex(port.PortError, "adapter archive changed"):
            port.verify_payload(copy)

    def test_source_archive_mutation_rejected_before_install(self):
        copy = self.user_home / "candidate-release"
        shutil.copytree(self.release, copy)
        (copy / "source/pstack/README.md").write_text("changed archived source")
        before = port.tree(self.user_home)
        with self.assertRaisesRegex(port.PortError, "source archive changed"):
            self.installation.install(copy)
        self.assertEqual(port.tree(self.user_home), before)

    def prepare_runtime_fixture(self):
        self.installation.install(self.release)
        runtime, scripts = self.installation.runtime()
        shutil.copytree(scripts, runtime)
        key = port.sha((scripts / "package.json").read_bytes() + b"\0" + (scripts / "bun.lock").read_bytes())
        port.write_json(runtime / "setup-receipt.json", {"source_release": runtime.name, "package_lock_key": key, "bun_version": "fixture"})
        return runtime, scripts

    def test_changed_helper_code_is_rejected_by_execution_setup_and_verify(self):
        runtime, _ = self.prepare_runtime_fixture()
        (runtime / "orch/orch.ts").write_text("modified helper")
        with mock.patch.object(port.subprocess, "call") as execute, mock.patch.object(port.subprocess, "run") as setup:
            for operation in (lambda: self.installation.run_tool("orch", ["--help"]), self.installation.setup_tools, self.installation.verify):
                with self.assertRaisesRegex(port.PortError, "Helper runtime source differs"):
                    operation()
            execute.assert_not_called()
            setup.assert_not_called()

    def test_modified_helper_dependencies_do_not_change_source_integrity(self):
        runtime, _ = self.prepare_runtime_fixture()
        dependency = runtime / "node_modules/fixture/index.js"
        dependency.parent.mkdir(parents=True)
        dependency.write_text("dependency contents are outside the helper source manifest")
        self.assertEqual(self.installation.verify()["integrity"], "PASS")

    def test_customized_profile_survives_update_and_rollback(self):
        self.installation.install(self.release, migrate_standalone=True)
        original_migration = self.installation.state()["migration"]
        preferences = self.installation.root / "preferences.json"
        customized = b'{"schema_version":1,"roles":{"judge":{"model":"user-choice"}},"panels":{"arena":4},"personal-note":"retain"}\n'
        preferences.write_bytes(customized)
        candidate = variant_release(self.release, self.user_home / "candidate", version="0.2.1")
        self.installation.install(candidate)
        self.assertEqual(preferences.read_bytes(), customized)
        self.assertEqual(self.installation.state()["migration"], original_migration)
        self.installation.rollback(self.release.name)
        self.assertEqual(preferences.read_bytes(), customized)
        self.assertEqual(self.installation.state()["migration"], original_migration)
        self.assertTrue(self.installation.verify()["installed"])

    def test_legacy_rollback_retains_embedded_profile_conflict_protection(self):
        legacy = variant_release(self.release, self.user_home / "legacy", version="0.1.0", legacy=True)
        self.installation.install(legacy, migrate_standalone=True)
        preferences = self.installation.root / "preferences.json"
        original = preferences.read_bytes()
        customized = b'{"schema_version":1,"model":"user-choice","personal-note":"retain"}\n'
        preferences.write_bytes(customized)
        self.installation.install(self.release)
        before = port.tree(self.user_home)
        with self.assertRaisesRegex(port.PortError, "profile|preferences"):
            self.installation.rollback(legacy.name)
        self.assertEqual(port.tree(self.user_home), before)
        self.assertEqual(preferences.read_bytes(), customized)
        preferences.write_bytes(original)
        self.installation.rollback(legacy.name)
        self.assertEqual(preferences.read_bytes(), original)
        self.assertTrue(self.installation.verify()["installed"])


class MainUpdateTests(LifecycleFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.installation.install(self.release)

    def snapshot(self, changed=True):
        candidate = self.user_home / "candidate"
        source = candidate / "pstack"
        shutil.copytree(PROJECT / "upstream/pstack", source)
        commit = port.read_json(PROJECT / "source.lock.json")["commit"]
        if changed:
            (source / "README.md").write_text("Updated upstream documentation")
            commit = "a" * 40
        snapshot = {"repository": port.REPOSITORY, "commit": commit, "files": port.tree(source)}
        port.write_json(candidate / "snapshot.json", snapshot)
        return candidate, snapshot

    def run_command(self, command, snapshot, *arguments):
        stdout = io.StringIO()
        with mock.patch.object(port, "Installation", return_value=self.installation), \
                mock.patch.object(port, "fetch_snapshot", return_value=snapshot), \
                contextlib.redirect_stdout(stdout):
            result = port.main([command, "--ref", snapshot[1]["commit"], *arguments])
        self.assertEqual(result, 0)
        return json.loads(stdout.getvalue())

    def test_update_reports_actual_active_release_change(self):
        previous = self.installation.state()["active"]
        result = self.run_command("update", self.snapshot(), "--yes")
        self.assertNotEqual(self.installation.state()["active"], previous)
        self.assertTrue(result["active_installation_changed"])
        self.assertTrue(self.installation.verify()["installed"])

    def test_update_noop_reports_no_change_and_preserves_state(self):
        previous = self.installation.state()
        result = self.run_command("update", self.snapshot(changed=False), "--yes")
        self.assertFalse(result["active_installation_changed"])
        self.assertTrue(result["installation"]["already_installed"])
        self.assertEqual(self.installation.state(), previous)

    def test_update_dry_run_reports_no_active_or_cache_change(self):
        previous = self.installation.state()
        cache = port.tree(self.installation.cache(previous["marketplace_name"]))
        catalog = self.installation.catalog()
        result = self.run_command("update", self.snapshot(), "--dry-run")
        self.assertFalse(result["active_installation_changed"])
        self.assertTrue(result["installation"]["dry_run"])
        self.assertEqual(self.installation.state(), previous)
        self.assertEqual(self.installation.catalog(), catalog)
        self.assertEqual(port.tree(self.installation.cache(previous["marketplace_name"])), cache)

    def test_check_reports_no_change_without_building_or_installing(self):
        previous = self.installation.state()
        cache = port.tree(self.installation.cache(previous["marketplace_name"]))
        with mock.patch.object(port, "build") as build, \
                mock.patch.object(self.installation, "install") as install:
            result = self.run_command("check", self.snapshot())
        self.assertFalse(result["active_installation_changed"])
        self.assertNotIn("installation", result)
        self.assertEqual(self.installation.state(), previous)
        self.assertEqual(port.tree(self.installation.cache(previous["marketplace_name"])), cache)
        build.assert_not_called()
        install.assert_not_called()


class NativeScopeTests(unittest.TestCase):
    def test_alternate_home_never_runs_native_subprocess(self):
        with tempfile.TemporaryDirectory() as temporary:
            installation = port.Installation(temporary)
            with mock.patch.object(port.subprocess, "run") as run:
                with self.assertRaisesRegex(port.PortError, "cannot sandbox Codex"):
                    installation.native("add", "personal")
                run.assert_not_called()

    def test_custom_codex_home_never_runs_native_subprocess(self):
        with tempfile.TemporaryDirectory() as temporary:
            installation = port.Installation(Path.home())
            with mock.patch.dict(os.environ, {"CODEX_HOME": temporary}), mock.patch.object(port.subprocess, "run") as run:
                with self.assertRaisesRegex(port.PortError, "Custom CODEX_HOME"):
                    installation.native("add", "personal")
                run.assert_not_called()

    def test_missing_native_registration_needs_both_config_and_cache_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            installation = port.Installation(temporary)
            missing = subprocess.CompletedProcess([], 1, "", "Plugin not installed")
            config = installation.user_home / ".codex/config.toml"
            config.parent.mkdir(parents=True)
            config.write_text('[plugins."pstack-codex@personal"]\nenabled = true\n')
            with mock.patch.object(installation, "check_native_scope"), mock.patch.object(port.subprocess, "run", return_value=missing):
                with self.assertRaises(port.PortError):
                    installation.native("remove", "personal")
                config.write_text('[plugins."pstack-codex@personal"]\nenabled = false\n')
                installation.native("remove", "personal")
                installation.cache("personal").mkdir(parents=True)
                with self.assertRaises(port.PortError):
                    installation.native("remove", "personal")


if __name__ == "__main__":
    unittest.main()
