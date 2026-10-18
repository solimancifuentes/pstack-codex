#!/usr/bin/env python3
"""Build, install, inspect, update and roll back a pinned pstack Codex port."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
import urllib.parse
import zipfile

PLUGIN = "pstack-codex"
VERSION = "0.2.0"
REPOSITORY = "https://github.com/cursor/plugins"
CONSOLIDATE = ("bro", "correct", "principle-model-the-domain", "tdd", "technical-writing", "unslop")


class PortError(Exception):
    pass


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temp, path)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tree(root):
    root = Path(root)
    if not root.exists():
        return {}
    rows = {}
    for path in sorted(root.rglob("*")):
        key = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows[key] = "symlink:" + os.readlink(path)
        elif path.is_file():
            rows[key] = sha(path.read_bytes())
    return rows


def inside(root, relative):
    part = PurePosixPath(relative)
    if part.is_absolute() or ".." in part.parts:
        raise PortError(f"Unsafe package path: {relative}")
    path = Path(root) / Path(*part.parts)
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise PortError(f"Path escapes package: {relative}")
    return path


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def source_metadata(source):
    return read_json(Path(source) / "plugin.json")


def frontmatter(text):
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise PortError("Missing skill frontmatter")
    data = dict(re.findall(r"^([\w-]+):\s*(.*)$", match[1], re.M))
    return data, text[match.end():]


def normalize_skill(path, profile):
    text = path.read_text()
    data, body = frontmatter(text)
    slug = path.parent.name
    description = data.get("description", "").strip()
    # Pinned frontmatter uses single-line scalars; double quotes use the JSON
    # subset of YAML escapes. Reject other quoted syntax rather than corrupt it.
    if description.startswith('"'):
        try:
            description = json.loads(description)
        except ValueError as error:
            raise PortError(f"Unsupported quoted description in {path}: {error}") from error
    elif description.startswith("'"):
        if not re.fullmatch(r"'(?:[^']|'')*'", description):
            raise PortError(f"Invalid single-quoted description in {path}")
        description = description[1:-1].replace("''", "'")
    if not description or len(description) > 1024:
        raise PortError(f"Invalid description in {path}")
    implicit = data.get("disable-model-invocation") != "true"
    implicit = profile.get("implicit_invocation", {}).get(slug, implicit)
    if slug == "unslop" and slug in profile.get("always_apply", []):
        if "Must always apply." not in description:
            description += " Must always apply."
    if "CODEX.md" not in body:
        body = "Read [the shared runtime router](../../CODEX.md) before using runtime tools.\n\n" + body
    path.write_text(f"---\nname: {slug}\ndescription: {json.dumps(description)}\n---\n\n" + body.lstrip())
    policy = path.parent / "agents/openai.yaml"
    policy.parent.mkdir(exist_ok=True)
    policy.write_text("policy:\n  allow_implicit_invocation: " + str(implicit).lower() + "\n")
    return {"name": slug, "description": description, "allow_implicit_invocation": implicit}


def disclose_mode_progressively(plugin):
    entrypoint = plugin / "skills/poteto-mode/SKILL.md"
    text = entrypoint.read_text()
    _, workflow = frontmatter(text)
    (entrypoint.parent / "WORKFLOW.md").write_text(workflow)
    header = text[:text.index("\n---\n", 4) + len("\n---\n")]
    entrypoint.write_text(header + '''
# Poteto mode

Read [WORKFLOW.md](WORKFLOW.md) in full before choosing or running a playbook.
It contains the complete adapted mode, its principles index, and routing rules.
Read [the shared runtime router](../../CODEX.md) and select the active host adapter.
The separate workflow file avoids truncation of this skill's injected entrypoint.
Follow the user's requested scope and endpoint, including requests to inspect or
plan without implementation. Do not treat invocation as an extra authority grant.
''')


def verify_payload(release):
    release = Path(release)
    manifest = read_json(release / "release.json")
    actual = tree(release / "plugin")
    if actual != manifest["payload"]:
        changed = sorted(key for key in set(actual) | set(manifest["payload"])
                         if actual.get(key) != manifest["payload"].get(key))
        raise PortError("Release payload changed: " + ", ".join(changed[:10]))
    if tree(release / "source/pstack") != manifest["source"]:
        raise PortError("Release source archive changed")
    if tree(release / "adapters") != manifest["adapters"]:
        raise PortError("Release adapter archive changed")
    identity = {"source_commit": manifest["source_commit"], "source": manifest["source"],
                "payload": manifest["payload"], "adapters": manifest["adapters"],
                "manager": manifest["manager_sha256"]}
    expected = manifest["source_commit"][:12] + "-" + sha(json_bytes(identity))[:12]
    if not re.fullmatch(r"[0-9a-f]{12}-[0-9a-f]{12}", manifest["release"]) or manifest["release"] != expected:
        raise PortError("Release identity does not match its provenance manifest")
    return manifest


def patch_bootstrap(plugin):
    path = plugin / "skills/poteto-mode/scripts/bootstrap.ts"
    if not path.exists():
        raise PortError("Missing upstream helper bootstrap")
    original = path.read_bytes()
    path.write_text('''import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";

export function ensureDependenciesInstalled(): void {
  const scriptsDirectory = import.meta.dir;
  const key = createHash("sha256")
    .update(readFileSync(join(scriptsDirectory, "package.json")))
    .update("\\0")
    .update(readFileSync(join(scriptsDirectory, "bun.lock")))
    .digest("hex");
  const marker = join(scriptsDirectory, "node_modules/.poteto-mode-tools-install-key");
  if (!existsSync(join(scriptsDirectory, "node_modules/commander/package.json")) ||
      !existsSync(marker) || readFileSync(marker, "utf8").trim() !== key) {
    throw new Error("pstack helpers are not prepared. Use the packaged tools/runtime.py tools-setup --yes launcher. No packages were installed.");
  }
}
''')
    return {"source": "skills/poteto-mode/scripts/bootstrap.ts", "sha256": sha(original),
            "reason": "Dependency setup is explicit and mutable runtime stays outside plugin cache"}


def validate_active(plugin, expected_names):
    entries = sorted((plugin / "skills").glob("*/SKILL.md"))
    names = [path.parent.name for path in entries]
    if names != sorted(expected_names):
        raise PortError("Skill coverage changed; review and classify every added or removed skill")
    issues = []
    for path in entries:
        data, _ = frontmatter(path.read_text())
        if data.get("name") != path.parent.name or not re.fullmatch(r"[a-z0-9-]{1,64}", data["name"]):
            issues.append(f"Invalid skill name: {path}")
    for path in plugin.rglob("*.md"):
        if not path.relative_to(plugin).parts[0] in ("skills", "agents"):
            continue
        text = path.read_text()
        for line_no, line in enumerate(text.splitlines(), 1):
            if re.search(r"subagent_type\s*[:=]|environment:\s*[\"']cloud|~?/\.cursor/|grok-4\.7-|claude-opus-5-5-", line):
                issues.append(f"Unadapted runtime instruction: {path.relative_to(plugin)}:{line_no}")
        for link in re.findall(r"\]\(([^\s)]+)\)", text):
            if re.match(r"[a-zA-Z][\w+.-]*:", link) or link.startswith(("#", "/")):
                continue
            target = link.split("#", 1)[0]
            if target not in ("", "url") and not (path.parent / target).exists():
                issues.append(f"Missing reference: {path.relative_to(plugin)} -> {target}")
    if issues:
        raise PortError("\n".join(issues[:35]))


def build(project, source=None, commit=None, output=None, profile=None):
    project = Path(project).resolve()
    lock = read_json(project / "source.lock.json")
    source = Path(source or project / "upstream/pstack").resolve()
    commit = commit or lock["commit"]
    profile = read_json(project / "defaults.json")
    actual_source = tree(source)
    if commit == lock["commit"] and actual_source != lock["files"]:
        raise PortError("Pinned source differs from source.lock.json; restore the source or review a new snapshot")
    if commit != lock["commit"]:
        provenance = source.parent / "snapshot.json"
        if not provenance.is_file():
            raise PortError("New source needs snapshot.json from a checked original-repository download")
        snapshot = read_json(provenance)
        if snapshot.get("commit") != commit or snapshot.get("repository") != REPOSITORY or snapshot.get("files") != actual_source:
            raise PortError("Candidate source provenance differs from the downloaded snapshot")
    spec = read_json(project / "adapters/spec.json")
    conflicts = []
    for row in spec["files"]:
        path = inside(source, row["source"])
        if not path.is_file() or sha(path.read_bytes()) != row["sha256"]:
            conflicts.append(row["source"])
    if conflicts:
        raise PortError("Adapter conflict; review changed source and update the overlay before promotion: " + ", ".join(conflicts))
    bootstrap = "skills/poteto-mode/scripts/bootstrap.ts"
    if actual_source.get(bootstrap) != lock["files"].get(bootstrap):
        raise PortError("Adapter conflict: review changed helper bootstrap before replacing it")
    output = Path(output or project / "build").resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pstack-build-", dir=output) as temp_dir:
        staged = Path(temp_dir)
        plugin = staged / "plugin"
        plugin.mkdir()
        for name in ("skills", "agents", "assets"):
            shutil.copytree(source / name, plugin / name)
        shutil.copy2(source / "LICENSE", plugin / "LICENSE")
        for row in spec["files"]:
            target = inside(plugin, row["source"])
            overlay = inside(project / "adapters", row["overlay"])
            if not overlay.is_file():
                raise PortError(f"Missing overlay: {overlay}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(overlay, target)
        for row in spec.get("additional_files", []):
            target = inside(plugin, row["target"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(inside(project / "adapters", row["source"]), target)
        (plugin / "assets/logo.png").unlink(missing_ok=True)
        bootstrap_patch = patch_bootstrap(plugin)
        publication = read_json(project / "publication.json")
        metadata = {"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                    "name": PLUGIN, "version": VERSION,
                    "description": "Engineering workflows for planning, implementation, review, and verification.",
                    "author": publication["author"],
                    "repository": publication["repository"], "license": "MIT",
                    "extensions": {"com.openai": {
                        "requires_local_executor": True,
                        "onboardingSkill": "./skills/setup-pstack/SKILL.md",
                        "interface": publication["interface"],
                        "publication": {"release_notes": publication["release_notes"],
                                        **({"countries": publication["countries"]} if "countries" in publication else {})},
                        "review": {"commerce": False}
                    }}}
        write_json(plugin / "plugin.json", metadata)
        write_json(plugin / ".codex-plugin/plugin.json", {
            "name": PLUGIN, "version": VERSION, "description": metadata["description"],
            "skills": "./skills/", "requires_local_executor": True,
            "interface": publication["interface"]})
        shutil.copy2(project / "NOTICE", plugin / "NOTICE")
        shutil.copy2(project / "distribution-docs/PRIVACY.md", plugin / "PRIVACY.md")
        (plugin / "tools").mkdir(exist_ok=True)
        shutil.copy2(project / "runtime/runtime.py", plugin / "tools/runtime.py")
        helpers = {path.relative_to(plugin).as_posix(): sha(path.read_bytes())
                   for path in sorted((plugin / "skills/poteto-mode/scripts").rglob("*")) if path.is_file()}
        log_script = plugin / "skills/show-me-your-work/scripts/log.sh"
        helpers[log_script.relative_to(plugin).as_posix()] = sha(log_script.read_bytes())
        write_json(plugin / "tools/helper-sources.json", {"schema_version": 1, "files": helpers})
        entries = [normalize_skill(path, profile) for path in sorted((plugin / "skills").glob("*/SKILL.md"))]
        disclose_mode_progressively(plugin)
        expected_names = sorted(path.parent.name for path in (project / "upstream/pstack/skills").glob("*/SKILL.md"))
        validate_active(plugin, expected_names)
        write_json(plugin / "defaults.json", profile)
        write_json(plugin / "provenance.json", {"repository": REPOSITORY, "commit": commit,
                   "upstream_version": source_metadata(source)["version"],
                   "source_files": actual_source})
        payload = tree(plugin)
        identity = {"source_commit": commit, "source": actual_source, "payload": payload,
                    "adapters": tree(project / "adapters"), "manager": sha(Path(__file__).read_bytes())}
        release_id = commit[:12] + "-" + sha(json_bytes(identity))[:12]
        manifest = {"schema_version": 1, "release": release_id, "port_version": VERSION,
                    "repository": REPOSITORY, "source_commit": commit,
                    "upstream_version": source_metadata(source)["version"],
                    "source": actual_source, "payload": payload, "skills": entries,
                    "preferences": profile, "profile_mode": "external", "adapters": identity["adapters"],
                    "manager_sha256": identity["manager"],
                    "helper_patch": bootstrap_patch}
        write_json(staged / "release.json", manifest)
        shutil.copytree(source, staged / "source/pstack")
        shutil.copytree(project / "adapters", staged / "adapters")
        destination = output / release_id
        if destination.exists():
            if read_json(destination / "release.json") != manifest:
                raise PortError(f"Release identity collision at {destination}")
            verify_payload(destination)
        else:
            os.replace(staged, destination)
        return {"release": release_id, "path": str(destination), "skills": len(entries),
                "payload_files": len(payload), "source_commit": commit}


def request(url):
    req = urllib.request.Request(url, headers={"User-Agent": "pstack-codex/" + VERSION})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def fetch_snapshot(ref, destination):
    destination = Path(destination)
    info = json.loads(request("https://api.github.com/repos/cursor/plugins/commits/" + urllib.parse.quote(ref, safe="")))
    commit = info["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise PortError("GitHub returned an invalid commit")
    root = destination / commit
    if root.exists():
        snapshot = read_json(root / "snapshot.json")
        if tree(root / "pstack") != snapshot["files"]:
            raise PortError("Cached candidate source changed")
        return root, snapshot
    payload = request(f"https://codeload.github.com/cursor/plugins/zip/{commit}")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fetch-", dir=destination) as temporary:
        scratch = Path(temporary)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            if archive.testzip() is not None:
                raise PortError("Archive CRC failed")
            for entry in archive.infolist():
                parts = PurePosixPath(entry.filename).parts
                if len(parts) < 2 or parts[1] != "pstack" or entry.is_dir():
                    continue
                if ((entry.external_attr >> 16) & 0o170000) == 0o120000:
                    raise PortError("Unexpected symlink in source archive")
                target = inside(scratch, PurePosixPath(*parts[1:]).as_posix())
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(entry))
                target.chmod((entry.external_attr >> 16) & 0o777 or 0o644)
        files = tree(scratch / "pstack")
        snapshot = {"commit": commit, "repository": REPOSITORY,
                    "archive_sha256": sha(payload), "files": files}
        write_json(scratch / "snapshot.json", snapshot)
        os.replace(scratch, root)
    return root, snapshot


def difference(before, after):
    return {"added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after)),
            "changed": sorted(key for key in set(before) & set(after) if before[key] != after[key])}


class Installation:
    def __init__(self, user_home, codex="codex", project=None):
        self.user_home = Path(user_home).resolve()
        self.root = self.user_home / ".codex/pstack-codex"
        self.marketplace = self.user_home / ".agents/plugins/marketplace.json"
        self.codex = codex
        self.project = Path(project or Path(__file__).resolve().parent)

    @property
    def state_path(self):
        return self.root / "state.json"

    @property
    def transaction_path(self):
        return self.root / "pending-operation.json"

    def state(self):
        return read_json(self.state_path) if self.state_path.exists() else {"active": None, "history": []}

    @contextlib.contextmanager
    def locked(self):
        self.root.mkdir(parents=True, exist_ok=True)
        # The kernel releases this lock even if the process is killed. Keep the
        # inode in place: unlinking a flock file permits two independent locks.
        with (self.root / ".operation.lock").open("a+") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise PortError("Another pstack operation is running; retry when it finishes")
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def checkpoint(self, name):
        """Fault-injection boundary used by lifecycle tests."""

    def require_no_transaction(self):
        if self.transaction_path.exists():
            raise PortError("An interrupted operation needs recovery. Run pstack-codex recover --dry-run, then recover --yes")

    def check_native_scope(self):
        if self.user_home != Path.home().resolve():
            raise PortError("Native plugin mutations require the current user home; --user-home cannot sandbox Codex")
        configured = os.environ.get("CODEX_HOME")
        if configured and Path(configured).expanduser().resolve() != self.user_home / ".codex":
            raise PortError("Custom CODEX_HOME is not supported for native plugin mutations; no environment variables were changed")

    def entry(self):
        return {"name": PLUGIN, "source": {"source": "local", "path": "./.codex/pstack-codex/active/plugin"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools"}

    def catalog(self):
        return read_json(self.marketplace) if self.marketplace.exists() else {"name": "personal", "plugins": []}

    def native(self, action, marketplace_name):
        self.check_native_scope()
        command = [self.codex, "plugin", action, PLUGIN + "@" + marketplace_name, "--json"]
        result = subprocess.run(command, text=True, capture_output=True, timeout=120)
        if result.returncode:
            detail = result.stderr.strip() or result.stdout.strip()
            if action == "remove" and re.search(r"not installed|not found|does not exist|not enabled", detail, re.I):
                config_path = self.user_home / ".codex/config.toml"
                config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
                registration = config.get("plugins", {}).get(PLUGIN + "@" + marketplace_name)
                disabled = registration is None or registration.get("enabled") is False
                if disabled and not self.cache(marketplace_name).exists():
                    return result.stdout
            raise PortError(f"Codex plugin {action} failed: {detail}")
        return result.stdout

    def cache(self, marketplace_name, version=None):
        if version is None:
            metadata = self.root / "active/plugin/plugin.json"
            version = read_json(metadata)["version"] if metadata.is_file() else VERSION
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", version):
            raise PortError("Invalid plugin cache version")
        return self.user_home / ".codex/plugins/cache" / marketplace_name / PLUGIN / version

    def verify_cache(self, manifest, marketplace_name):
        actual = tree(self.cache(marketplace_name, manifest["port_version"]))
        if actual != manifest["payload"]:
            changes = difference(manifest["payload"], actual)
            raise PortError("Native installed cache differs from release: " + json.dumps({key: value[:10] for key, value in changes.items()}))

    def select(self, release):
        active = self.root / "active"
        temporary = self.root / ".next-active"
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(Path("releases") / release, target_is_directory=True)
        os.replace(temporary, active)

    def assert_owned_state(self, state, catalog):
        entries = [row for row in catalog.get("plugins", []) if row.get("name") == PLUGIN]
        if state.get("active"):
            if entries != [state["owned_entry"]] or catalog.get("name") != state["marketplace_name"]:
                raise PortError("The owned marketplace entry changed; refusing to replace local edits")
            if not (self.root / "active").is_symlink() or os.readlink(self.root / "active") != "releases/" + state["active"]:
                raise PortError("The active release link changed; inspect before updating")
            self.verify_cache(verify_payload(self.root / "releases" / state["active"]), state["marketplace_name"])
        elif entries:
            raise PortError("An existing pstack-codex marketplace entry is not owned by this installation")

    def write_owned_entry(self, entry, marketplace_name):
        catalog = self.catalog()
        entries = [row for row in catalog.get("plugins", []) if row.get("name") == PLUGIN]
        if catalog.get("name") != marketplace_name or entries not in ([], [self.entry()]):
            raise PortError("Marketplace ownership changed during operation; preserving local edits")
        catalog["plugins"] = [row for row in catalog.get("plugins", []) if row.get("name") != PLUGIN]
        if entry is not None:
            catalog["plugins"].append(entry)
        write_json(self.marketplace, catalog)

    def check_recovery_state(self, transaction):
        state = self.state()
        if state not in (transaction["previous_state"], transaction["next_state"]):
            raise PortError("Installation state changed during interrupted operation; inspect before recovery")
        active = self.root / "active"
        allowed = {"releases/" + value for value in (transaction["previous_state"].get("active"),
                                                     transaction["next_state"].get("active")) if value}
        if active.exists() or active.is_symlink():
            if not active.is_symlink() or os.readlink(active) not in allowed:
                raise PortError("Active link changed during interrupted operation; preserving local edits")
        catalog = self.catalog()
        entries = [row for row in catalog.get("plugins", []) if row.get("name") == PLUGIN]
        if catalog.get("name") != transaction["marketplace_name"] or entries not in ([], [self.entry()]):
            raise PortError("Marketplace entry changed during interrupted operation; preserving local edits")
        allowed_by_version = {}
        for release in (transaction["previous_state"].get("active"), transaction["next_state"].get("active")):
            if release:
                manifest = verify_payload(self.root / "releases" / release)
                allowed_by_version.setdefault(manifest["port_version"], []).append(manifest["payload"])
        for version, allowed in allowed_by_version.items():
            actual = tree(self.cache(transaction["marketplace_name"], version))
            if any(not any(payload.get(key) == value for payload in allowed) for key, value in actual.items()):
                raise PortError("Native cache changed during interrupted operation; inspect before recovery")

    def restore_standalone(self, migration, allow_unmoved=False):
        for name, expected in migration["standalone"].items():
            path = self.user_home / ".agents/skills" / name
            backup = self.root / "backups" / migration["id"] / "standalone" / name
            if path.exists() or path.is_symlink():
                if tree(path) != expected:
                    raise PortError(f"Recovery conflict: standalone skill changed: {path}")
                if not allow_unmoved and tree(backup) != expected:
                    raise PortError(f"Rollback backup changed: {backup}")
                continue
            if tree(backup) != expected:
                raise PortError(f"Rollback backup changed or missing: {backup}")
            staged = self.root / "restore-staging" / migration["id"] / name
            if staged.exists():
                shutil.rmtree(staged)
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(backup, staged, symlinks=True)
            if tree(staged) != expected:
                raise PortError(f"Staged restoration differs from backup: {name}")
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() or path.is_symlink():
                raise PortError(f"Recovery conflict: standalone destination appeared: {path}")
            os.rename(staged, path)
            self.checkpoint("restored:" + name)

    def recover_locked(self):
        transaction = read_json(self.transaction_path)
        self.check_recovery_state(transaction)
        previous = transaction["previous_state"]
        market = transaction["marketplace_name"]
        if transaction["kind"] == "install" and self.state() == transaction["next_state"]:
            self.assert_owned_state(self.state(), self.catalog())
            self.transaction_path.unlink()
            return {"recovered": True, "outcome": "installation-completed"}
        if transaction["kind"] == "install":
            if previous.get("active"):
                self.write_owned_entry(previous["owned_entry"], market)
                self.select(previous["active"])
                self.native("remove", market)
                self.native("add", market)
                self.verify_cache(verify_payload(self.root / "releases" / previous["active"]), market)
            else:
                self.native("remove", market)
                self.write_owned_entry(None, market)
                (self.root / "active").unlink(missing_ok=True)
            if transaction["first_migration"]:
                self.restore_standalone(transaction["migration"], allow_unmoved=True)
            write_json(self.state_path, previous)
            outcome = "previous-installation-restored"
        elif transaction["kind"] == "rollback":
            self.native("remove", market)
            self.write_owned_entry(None, market)
            self.restore_standalone(transaction["migration"])
            (self.root / "active").unlink(missing_ok=True)
            write_json(self.state_path, transaction["next_state"])
            outcome = "before-install-restored"
        else:
            raise PortError("Unknown pending operation kind")
        self.transaction_path.unlink()
        return {"recovered": True, "outcome": outcome}

    def recover(self, dry_run=False):
        if not self.transaction_path.exists():
            return {"recovered": False, "pending": False}
        transaction = read_json(self.transaction_path)
        if dry_run:
            self.check_recovery_state(transaction)
            return {"dry_run": True, "kind": transaction["kind"],
                    "previous": transaction["previous_state"].get("active"),
                    "candidate": transaction["next_state"].get("active")}
        self.check_native_scope()
        with self.locked():
            if not self.transaction_path.exists():
                return {"recovered": False, "pending": False}
            return self.recover_locked()

    def install(self, release, dry_run=False, migrate_standalone=False):
        self.require_no_transaction()
        release = Path(release).resolve()
        manifest = verify_payload(release)
        state = self.state()
        catalog = self.catalog()
        self.assert_owned_state(state, catalog)
        preferences = self.root / "preferences.json"
        embedded_profile = manifest.get("profile_mode") != "external"
        if embedded_profile and preferences.is_file() and read_json(preferences) != manifest["preferences"]:
            raise PortError("This legacy release embeds different preferences. The current profile was preserved. Select a release with an external runtime profile or review a compatible legacy package before rollback")
        plan = {"release": manifest["release"], "previous": state.get("active"),
                "marketplace": str(self.marketplace), "entry": self.entry(),
                "consolidate": [name for name in CONSOLIDATE if migrate_standalone and
                                ((self.user_home / ".agents/skills" / name).exists() or
                                 (self.user_home / ".agents/skills" / name).is_symlink())]}
        first = not state.get("migration")
        if migrate_standalone and state.get("active") and plan["consolidate"]:
            raise PortError("Standalone migration is only supported during the first managed install. Run rollback --to before-install, then install --migrate-standalone after reviewing the original skills")
        migration = state.get("migration", {"id": now(), "standalone": {}, "marketplace_existed": self.marketplace.exists()})
        if first and plan["consolidate"]:
            baseline = read_json(self.project / "migration-baseline.json")
            for name in plan["consolidate"]:
                path = self.user_home / ".agents/skills" / name
                if path.is_symlink() or tree(path) != baseline.get(name):
                    raise PortError(f"Standalone skill differs from audited migration baseline: {name}. Preserve or review its local customization before consolidation")
                migration["standalone"][name] = baseline[name]
        if dry_run:
            return {"dry_run": True, **plan}
        if state.get("active") == manifest["release"]:
            return {"already_installed": True, **plan}
        self.check_native_scope()
        with self.locked():
            self.require_no_transaction()
            if self.state() != state or self.catalog() != catalog:
                raise PortError("Installation state changed while preparing; retry")
            self.assert_owned_state(state, catalog)
            target = self.root / "releases" / manifest["release"]
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix="release-", dir=target.parent) as temporary:
                    staged = Path(temporary) / "release"
                    shutil.copytree(release, staged)
                    verify_payload(staged)
                    os.replace(staged, target)
            if verify_payload(target) != manifest:
                raise PortError("Existing release manifest differs from the candidate")
            market = catalog["name"]
            new_state = {"schema_version": 1, "active": manifest["release"], "marketplace_name": market,
                         "owned_entry": self.entry(), "migration": migration,
                         "history": state.get("history", []) + [{"from": state.get("active"), "to": manifest["release"], "at": now()}]}
            transaction = {"kind": "install", "previous_state": state, "next_state": new_state,
                           "marketplace_name": market, "migration": migration, "first_migration": first}
            write_json(self.transaction_path, transaction)
            try:
                self.write_owned_entry(self.entry(), market)
                self.select(manifest["release"])
                self.native("add", market)
                try:
                    self.verify_cache(manifest, market)
                except PortError:
                    self.native("remove", market)
                    self.native("add", market)
                    self.verify_cache(manifest, market)
                self.checkpoint("native-installed")
                if first:
                    for name, hashes in migration["standalone"].items():
                        path = self.user_home / ".agents/skills" / name
                        if tree(path) != hashes:
                            raise PortError(f"Standalone skill changed during install: {name}")
                        backup = self.root / "backups" / migration["id"] / "standalone" / name
                        backup.parent.mkdir(parents=True, exist_ok=True)
                        if backup.exists():
                            raise PortError(f"Backup destination already exists: {backup}")
                        os.rename(path, backup)
                        self.checkpoint("consolidated:" + name)
                if not preferences.exists():
                    write_json(preferences, manifest["preferences"])
                elif embedded_profile and read_json(preferences) != manifest["preferences"]:
                    raise PortError("Local preferences changed during installation; preserving them")
                write_json(self.state_path, new_state)
                self.checkpoint("state-committed")
                self.transaction_path.unlink()
            except Exception as original:
                try:
                    self.recover_locked()
                except Exception as recovery_error:
                    raise PortError(f"Install failed: {original}. Recovery is pending: {recovery_error}. Run pstack-codex recover --yes") from original
                raise
            return {"installed": True, "cache": str(self.cache(market)), **plan}

    def rollback(self, target, dry_run=False):
        self.require_no_transaction()
        state = self.state()
        if not state.get("active"):
            raise PortError("No active installation to roll back")
        if target != "before-install":
            if not re.fullmatch(r"[0-9a-f]{12}-[0-9a-f]{12}", target):
                raise PortError("Rollback target must be a release ID or before-install")
            return self.install(self.root / "releases" / target, dry_run)
        catalog = self.catalog()
        self.assert_owned_state(state, catalog)
        migration = state["migration"]
        restore = []
        for name, expected in migration["standalone"].items():
            path = self.user_home / ".agents/skills" / name
            backup = self.root / "backups" / migration["id"] / "standalone" / name
            if path.exists() or path.is_symlink():
                raise PortError(f"Rollback conflict: standalone destination now exists: {path}")
            if tree(backup) != expected:
                raise PortError(f"Rollback backup changed: {backup}")
            restore.append(path)
        if dry_run:
            return {"dry_run": True, "target": target, "restore": [str(path) for path in restore]}
        self.check_native_scope()
        with self.locked():
            self.require_no_transaction()
            if self.state() != state or self.catalog() != catalog:
                raise PortError("Installation state changed while preparing rollback; retry")
            self.assert_owned_state(state, catalog)
            for path in restore:
                if path.exists() or path.is_symlink():
                    raise PortError(f"Rollback conflict: standalone destination appeared: {path}")
            next_state = {"active": None, "history": state["history"] + [{"from": state["active"], "to": None, "at": now()}]}
            write_json(self.transaction_path, {"kind": "rollback", "previous_state": state, "next_state": next_state,
                       "marketplace_name": state["marketplace_name"], "migration": migration})
            try:
                self.recover_locked()
            except Exception as error:
                raise PortError(f"Rollback is incomplete: {error}. Run pstack-codex recover --yes") from error
        return {"rolled_back": True, "target": target, "restored": [path.name for path in restore]}

    def verify(self):
        self.require_no_transaction()
        state = self.state()
        if not state.get("active"):
            return {"installed": False}
        self.assert_owned_state(state, self.catalog())
        manifest = verify_payload(self.root / "releases" / state["active"])
        runtime, scripts = self.runtime()
        if runtime.exists():
            self.verify_runtime(runtime, scripts)
        return {"installed": True, "release": state["active"], "skills": len(manifest["skills"]),
                "cache": str(self.cache(state["marketplace_name"])), "integrity": "PASS",
                "fresh_discovery": "requires separate Codex process/session proof"}

    def runtime(self):
        self.require_no_transaction()
        state = self.state()
        if not state.get("active"):
            raise PortError("Install a release before preparing helper tools")
        return self.root / "tools" / state["active"], self.root / "releases" / state["active"] / "plugin/skills/poteto-mode/scripts"

    def verify_runtime(self, runtime, scripts):
        expected = tree(scripts)
        actual = {key: value for key, value in tree(runtime).items()
                  if not key.startswith("node_modules/") and key not in ("node_modules", "setup-receipt.json")}
        if actual != expected:
            raise PortError("Helper runtime source differs from its release; preserve local changes and recreate the runtime before use")
        receipt = runtime / "setup-receipt.json"
        if receipt.exists():
            record = read_json(receipt)
            key = sha((scripts / "package.json").read_bytes() + b"\0" + (scripts / "bun.lock").read_bytes())
            if record.get("source_release") != runtime.name or record.get("package_lock_key") != key:
                raise PortError("Helper setup receipt does not match its release")

    def setup_tools(self):
        with self.locked():
            runtime, scripts = self.runtime()
            verify_payload(self.root / "releases" / self.state()["active"])
            if not runtime.exists():
                runtime.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix="tools-", dir=runtime.parent) as temporary:
                    staged = Path(temporary) / "scripts"
                    shutil.copytree(scripts, staged)
                    os.replace(staged, runtime)
            self.verify_runtime(runtime, scripts)
            if not shutil.which("bun"):
                raise PortError("Bun is not installed. Install it separately before tools-setup")
            environment = dict(os.environ, BUN_INSTALL_CACHE_DIR=str(self.root / "cache/bun"))
            result = subprocess.run(["bun", "install", "--frozen-lockfile", "--ignore-scripts"], cwd=runtime, env=environment, capture_output=True, text=True)
            if result.returncode:
                raise PortError(result.stderr or result.stdout)
            self.verify_runtime(runtime, scripts)
            key = sha((runtime / "package.json").read_bytes() + b"\0" + (runtime / "bun.lock").read_bytes())
            (runtime / "node_modules/.poteto-mode-tools-install-key").write_text(key + "\n")
            write_json(runtime / "setup-receipt.json", {"package_lock_key": key, "source_release": self.state()["active"],
                        "bun_version": subprocess.check_output(["bun", "--version"], text=True).strip()})
            return {"prepared": True, "runtime": str(runtime), "package_lock_key": key}

    def run_tool(self, name, args):
        runtime, scripts = self.runtime()
        verify_payload(self.root / "releases" / self.state()["active"])
        if name in ("orch", "watch-pr"):
            if not (runtime / "setup-receipt.json").is_file():
                raise PortError("Helpers are not prepared. Run pstack-codex tools-setup --yes. No packages were installed.")
            self.verify_runtime(runtime, scripts)
            command = ["bun", str(runtime / ("orch/orch.ts" if name == "orch" else "watch-pr/watch-pr"))]
        elif name == "log":
            command = ["bash", str(self.root / "releases" / self.state()["active"] / "plugin/skills/show-me-your-work/scripts/log.sh")]
        else:
            raise PortError("Supported helpers: orch, watch-pr, log. Cursor check-plan/worktree-audit remain source-only.")
        return subprocess.call(command + args)

def parser():
    root = argparse.ArgumentParser(description=__doc__, epilog="Examples: pstack-codex status; pstack-codex check; pstack-codex rollback --to before-install --dry-run")
    root.add_argument("--project", type=Path, default=Path(__file__).resolve().parent)
    root.add_argument("--user-home", type=Path, default=Path.home())
    root.add_argument("--codex", default="codex")
    sub = root.add_subparsers(dest="command", required=True)
    for name, description in (("status", "Show active release and operation history"), ("verify", "Compare owned registration and installed bytes")):
        sub.add_parser(name, help=description, epilog=f"Example: pstack-codex {name}")
    build_parser = sub.add_parser("build", help="Build a deterministic release without installing", epilog="Example: pstack-codex build")
    build_parser.add_argument("--source", type=Path)
    build_parser.add_argument("--ref")
    build_parser.add_argument("--output", type=Path)
    build_parser.add_argument("--preferences", type=Path, help="Build with this local preference profile")
    for name in ("check", "update"):
        cmd = sub.add_parser(name, help="Check upstream" if name == "check" else "Build and install an adapter-compatible upstream commit", epilog=f"Example: pstack-codex {name} --ref main" + (" --yes" if name == "update" else ""))
        cmd.add_argument("--ref", default="main")
        if name == "update":
            cmd.add_argument("--yes", action="store_true")
            cmd.add_argument("--dry-run", action="store_true")
    install = sub.add_parser("install", help="Install one verified release through native Codex plugin commands", epilog="Example: pstack-codex install --release ./build/RELEASE --yes")
    install.add_argument("--release", type=Path, required=True)
    install.add_argument("--yes", action="store_true")
    install.add_argument("--dry-run", action="store_true")
    install.add_argument("--migrate-standalone", action="store_true", help="Explicitly consolidate only the six audited standalone originals")
    rollback = sub.add_parser("rollback", help="Select an older release or restore the pre-install skill layout", epilog="Example: pstack-codex rollback --to before-install --dry-run")
    rollback.add_argument("--to", required=True)
    rollback.add_argument("--yes", action="store_true")
    rollback.add_argument("--dry-run", action="store_true")
    recover = sub.add_parser("recover", help="Recover an interrupted install or rollback", epilog="Example: pstack-codex recover --dry-run")
    recover.add_argument("--yes", action="store_true")
    recover.add_argument("--dry-run", action="store_true")
    tools = sub.add_parser("tools-setup", help="Explicitly install locked helper dependencies into mutable runtime", epilog="Example: pstack-codex tools-setup --yes")
    tools.add_argument("--yes", action="store_true")
    tool = sub.add_parser("tool", help="Run an explicitly prepared helper", epilog="Example: pstack-codex tool orch -- --help")
    tool.add_argument("name", choices=("orch", "watch-pr", "log"))
    tool.add_argument("args", nargs=argparse.REMAINDER)
    return root


def main(argv=None):
    options = parser().parse_args(argv)
    installation = Installation(options.user_home, options.codex, options.project)
    try:
        command = options.command
        if command == "build":
            if options.preferences:
                raise PortError("Shared packages do not embed user profiles. Keep preferences in the separate runtime profile; omit --preferences")
            result = build(options.project, options.source, options.ref, options.output)
        elif command == "status":
            result = installation.state()
        elif command == "verify":
            result = installation.verify()
        elif command in ("check", "update"):
            candidate, snapshot = fetch_snapshot(options.ref, installation.root / "candidates")
            active = installation.state().get("active")
            baseline = read_json(installation.root / "releases" / active / "release.json") if active else read_json(options.project / "source.lock.json")
            changes = difference(baseline.get("source", baseline.get("files")), snapshot["files"])
            result = {"candidate": snapshot["commit"], "source": str(candidate / "pstack"), **changes,
                      "active_installation_changed": False}
            if command == "update":
                if not options.yes and not options.dry_run:
                    raise PortError("Use --dry-run to review, or --yes to apply an adapter-compatible update")
                built = build(options.project, candidate / "pstack", snapshot["commit"], installation.root / "build")
                result["installation"] = installation.install(built["path"], options.dry_run)
                result["active_installation_changed"] = not options.dry_run and installation.state().get("active") != active
        elif command in ("install", "rollback"):
            if not options.yes and not options.dry_run:
                raise PortError("Use --dry-run to review, or --yes to apply this scoped operation")
            result = installation.install(options.release, options.dry_run, options.migrate_standalone) if command == "install" else installation.rollback(options.to, options.dry_run)
        elif command == "recover":
            if not options.yes and not options.dry_run:
                raise PortError("Use --dry-run to inspect recovery, or --yes to recover the interrupted operation")
            result = installation.recover(options.dry_run)
        elif command == "tools-setup":
            if not options.yes:
                raise PortError("tools-setup installs packages. Run pstack-codex tools-setup --yes")
            result = installation.setup_tools()
        else:
            return installation.run_tool(options.name, options.args[1:] if options.args[:1] == ["--"] else options.args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (PortError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
