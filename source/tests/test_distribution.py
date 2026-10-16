import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import unittest
import zipfile


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
try:
    import pstack as port
    import distribution
finally:
    sys.path.pop(0)


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        cls.root = Path(cls.scratch.name)
        cls.release = Path(port.build(PROJECT, output=cls.root / "build")["path"])
        cls.original_release = port.tree(cls.release)
        cls.destination = cls.root / "export"
        distribution.export_release(PROJECT, cls.release, cls.destination)
        cls.repository = cls.destination / "repository"
        cls.plugin = cls.repository / "plugins" / port.PLUGIN
        cls.archive = cls.destination / f"{port.PLUGIN}-{port.VERSION}.zip"

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def zip_payload(self):
        with zipfile.ZipFile(self.archive) as archive:
            files = [entry for entry in archive.infolist() if not entry.is_dir()]
            names = [entry.filename for entry in files]
            self.assertEqual(len(names), len(set(names)), "duplicate ZIP members")
            self.assertEqual(archive.testzip(), None)
            direct = "plugin.json" in names
            prefix = "" if direct else port.PLUGIN + "/"
            payload = {}
            for entry in files:
                path = PurePosixPath(entry.filename)
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
                self.assertTrue(entry.filename.startswith(prefix))
                self.assertFalse(stat.S_ISLNK(entry.external_attr >> 16), entry.filename)
                payload[entry.filename[len(prefix):]] = archive.read(entry)
            return payload

    def test_export_preserves_release_and_copies_the_verified_payload(self):
        self.assertEqual(port.tree(self.release), self.original_release)
        self.assertEqual(port.tree(self.plugin), port.verify_payload(self.release)["payload"])
        self.assertEqual((self.plugin / "LICENSE").read_bytes(),
                         (PROJECT / "upstream/pstack/LICENSE").read_bytes())

    def test_marketplace_points_to_one_portable_shared_plugin(self):
        catalog = port.read_json(self.repository / ".agents/plugins/marketplace.json")
        self.assertTrue(catalog["name"])
        self.assertEqual(len(catalog["plugins"]), 1)
        entry = catalog["plugins"][0]
        self.assertEqual(entry["name"], port.PLUGIN)
        source = entry["source"]
        self.assertEqual(source["source"], "local")
        relative = PurePosixPath(source["path"])
        self.assertFalse(relative.is_absolute())
        self.assertNotIn("..", relative.parts)
        self.assertEqual((self.repository / source["path"]).resolve(), self.plugin.resolve())

    def test_zip_is_exactly_one_plugin_without_private_installation_state(self):
        payload = self.zip_payload()
        self.assertEqual({key: port.sha(data) for key, data in payload.items()},
                         port.verify_payload(self.release)["payload"])
        forbidden = {"preferences.json", "state.json", "pending-operation.json", "migration-baseline.json",
                     "source.lock.json", ".app.json", "marketplace.json"}
        for key in payload:
            parts = PurePosixPath(key).parts
            self.assertTrue(forbidden.isdisjoint(parts), key)
            self.assertTrue({"node_modules", "standalone-originals", "backups", "verification", ".git", "__pycache__"}.isdisjoint(parts), key)
        self.assertIn("defaults.json", payload)
        self.assertIn("LICENSE", payload)
        self.assertEqual(len([key for key in payload if re.fullmatch(r"skills/[^/]+/SKILL.md", key)]), 54)

    def test_root_and_compatibility_metadata_match(self):
        payload = self.zip_payload()
        metadata = json.loads(payload["plugin.json"])
        compat = json.loads(payload[".codex-plugin/plugin.json"])
        self.assertEqual(metadata["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual(metadata["name"], port.PLUGIN)
        self.assertEqual(metadata["version"], port.VERSION)
        self.assertRegex(metadata["version"], r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
        for key in ("name", "version", "description"):
            self.assertEqual(compat[key], metadata[key])
        self.assertTrue({"skills", "mcpServers", "apps", "interface"}.isdisjoint(metadata))
        openai = metadata["extensions"]["com.openai"]
        self.assertNotIn("apps", openai)
        interface = openai["interface"]
        self.assertTrue(interface["displayName"].strip())
        self.assertTrue(interface["shortDescription"].strip())
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertEqual(compat["interface"]["displayName"], interface["displayName"])
        self.assertEqual(compat["interface"]["shortDescription"], interface["shortDescription"])
        for key in ("logo", "composerIcon", "logoDark", "composerIconDark"):
            if key in interface:
                path = PurePosixPath(interface[key])
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
                self.assertIn(str(path).removeprefix("./"), payload)

    def test_all_local_markdown_references_are_contained_and_present(self):
        payload = self.zip_payload()
        for name, data in payload.items():
            if not name.endswith(".md"):
                continue
            for target in re.findall(r"\]\(([^\s)]+)\)", data.decode()):
                if re.match(r"[a-zA-Z][\w+.-]*:", target) or target.startswith(("#", "/")):
                    continue
                relative = target.split("#", 1)[0]
                if relative in ("", "url"):
                    continue
                path = PurePosixPath(name).parent / relative
                resolved = []
                for part in path.parts:
                    if part == "..":
                        self.assertTrue(resolved, f"{name} escapes plugin via {target}")
                        resolved.pop()
                    elif part != ".":
                        resolved.append(part)
                key = "/".join(resolved)
                self.assertTrue(key in payload or any(item.startswith(key.rstrip("/") + "/") for item in payload),
                                f"{name} references missing {target}")

    def test_export_rejects_defaults_changed_after_selected_release(self):
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            root = Path(temporary)
            project = root / "project"
            shutil.copytree(self.repository / "source", project)
            defaults = port.read_json(project / "defaults.json")
            defaults["model"] = "different-default-after-build"
            port.write_json(project / "defaults.json", defaults)
            before = port.tree(project)
            destination = root / "should-not-be-published"
            with self.assertRaisesRegex(port.PortError, "does not reproduce"):
                distribution.export_release(project, self.release, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(port.tree(project), before)
            self.assertEqual(port.tree(self.release), self.original_release)

    def test_export_rejects_copied_manager_changed_after_selected_release(self):
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            root = Path(temporary)
            project = root / "project"
            shutil.copytree(self.repository / "source", project)
            manager = project / "pstack.py"
            manager.write_text(manager.read_text() + "\nraise RuntimeError('different copied manager')\n")
            self.assertNotEqual(port.sha(manager.read_bytes()), port.verify_payload(self.release)["manager_sha256"])
            before = port.tree(project)
            destination = root / "should-not-be-published"
            with self.assertRaisesRegex(port.PortError, "manager source differs"):
                distribution.export_release(project, self.release, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(port.tree(project), before)
            self.assertEqual(port.tree(self.release), self.original_release)

    def test_export_rejects_runtime_changed_after_selected_release(self):
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            root = Path(temporary)
            project = root / "project"
            shutil.copytree(self.repository / "source", project)
            runtime = project / "runtime/runtime.py"
            runtime.write_text(runtime.read_text() + "\nraise RuntimeError('unreviewed post-build change')\n")
            before = port.tree(project)
            destination = root / "should-not-be-published"
            with self.assertRaisesRegex(port.PortError, "does not reproduce"):
                distribution.export_release(project, self.release, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(port.tree(project), before)
            self.assertEqual(port.tree(self.release), self.original_release)

    def test_export_rejects_privacy_terms_changed_after_selected_release(self):
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            root = Path(temporary)
            project = root / "project"
            shutil.copytree(self.repository / "source", project)
            policy = project / "distribution-docs/PRIVACY.md"
            policy.write_text(policy.read_text() + "\nUnreviewed retention commitment.\n")
            before = port.tree(project)
            destination = root / "should-not-be-published"
            with self.assertRaisesRegex(port.PortError, "does not reproduce"):
                distribution.export_release(project, self.release, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(port.tree(project), before)
            self.assertEqual(port.tree(self.release), self.original_release)

    def test_fetched_snapshot_export_rebuilds_archived_source_and_adapters(self):
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            root = Path(temporary)
            project = root / "project"
            shutil.copytree(self.repository / "source", project)
            candidate = root / "fetched-snapshot/pstack"
            shutil.copytree(project / "upstream/pstack", candidate)
            readme = candidate / "README.md"
            readme.write_text(readme.read_text() + "\nSynthetic fetched upstream documentation change.\n")
            commit = "a" * 40
            port.write_json(candidate.parent / "snapshot.json", {
                "repository": port.REPOSITORY, "commit": commit, "files": port.tree(candidate)})
            release = Path(port.build(project, source=candidate, commit=commit, output=root / "build")["path"])
            (project / "upstream/pstack/README.md").write_text("Working tree differs from selected snapshot")
            (project / "adapters/CODEX.md").write_text("Working adapter differs from selected snapshot")
            destination = root / "export"
            distribution.export_release(project, release, destination)
            exported = destination / "repository/source"
            lock = port.read_json(exported / "source.lock.json")
            self.assertEqual(lock["commit"], commit)
            self.assertEqual(lock["files"], port.tree(candidate))
            self.assertEqual(port.tree(exported / "upstream/pstack"), port.tree(release / "source/pstack"))
            self.assertEqual(port.tree(exported / "adapters"), port.tree(release / "adapters"))
            reproduced = port.build(exported, output=root / "rebuild")
            self.assertEqual(reproduced["release"], release.name)

    def test_export_is_deterministic(self):
        second = self.root / "second-export"
        distribution.export_release(PROJECT, self.release, second)
        self.assertEqual(port.tree(self.repository), port.tree(second / "repository"))
        self.assertEqual(self.archive.read_bytes(), (second / self.archive.name).read_bytes())


if __name__ == "__main__":
    unittest.main()
