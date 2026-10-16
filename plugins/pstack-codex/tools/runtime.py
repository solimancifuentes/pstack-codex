#!/usr/bin/env python3
"""Optional pstack helper launcher; skills work without this Python command."""

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile


PLUGIN = Path(__file__).resolve().parents[1]
SCRIPTS = "skills/poteto-mode/scripts"
LOG = "skills/show-me-your-work/scripts/log.sh"
EFFORTS = {"inherit-parent", "auto", "none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}


class RuntimeError(Exception):
    pass


def read_json(path):
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise RuntimeError(f"Cannot read JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object: {path}")
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def merge(base, overrides):
    result = dict(base)
    for key, value in overrides.items():
        result[key] = merge(result[key], value) if isinstance(result.get(key), dict) and isinstance(value, dict) else value
    return result


def validate_profile(profile):
    def routing(value, label):
        if not isinstance(value, dict):
            raise RuntimeError(f"{label} must be an object")
        for key in ("model", "speed"):
            if key in value and (not isinstance(value[key], str) or not value[key].strip()):
                raise RuntimeError(f"{label}.{key} must be a nonempty string; host availability is checked separately")
        if "reasoning_effort" in value and (not isinstance(value["reasoning_effort"], str) or value["reasoning_effort"] not in EFFORTS):
            raise RuntimeError(f"{label}.reasoning_effort must be one of {', '.join(sorted(EFFORTS))}; model support is checked separately")

    routing(profile, "profile")
    if "schema_version" in profile and (type(profile["schema_version"]) is not int or profile["schema_version"] != 1):
        raise RuntimeError("profile.schema_version must be 1")
    roles = profile.get("roles", {})
    if not isinstance(roles, dict):
        raise RuntimeError("profile.roles must be an object")
    for role, value in roles.items():
        routing(value, f"profile.roles.{role}")
    panels = profile.get("panels", {})
    if not isinstance(panels, dict):
        raise RuntimeError("profile.panels must be an object")
    for name, seats in panels.items():
        if type(seats) is not int or seats < 1:
            raise RuntimeError(f"profile.panels.{name} must be a positive integer; actual concurrency remains host-limited")
    implicit = profile.get("implicit_invocation", {})
    if not isinstance(implicit, dict) or any(type(value) is not bool for value in implicit.values()):
        raise RuntimeError("profile.implicit_invocation must map skill names to booleans")
    if "always_apply" in profile and (not isinstance(profile["always_apply"], list) or any(not isinstance(value, str) or not value for value in profile["always_apply"])):
        raise RuntimeError("profile.always_apply must be a list of skill names")
    return profile


def plain_path(path):
    """Reject a symlink at a user-selected mutation target or its parents."""
    path = Path(path).expanduser().absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise RuntimeError(f"Symlinks are not allowed in this path: {part}")
    return path


def within(root, relative):
    relative = PurePosixPath(relative)
    if relative.is_absolute() or not relative.parts or any(part in ("..", ".") for part in relative.parts):
        raise RuntimeError(f"Unsafe package path: {relative}")
    path = root.joinpath(*relative.parts)
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise RuntimeError(f"Symlink in helper path: {parent}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise RuntimeError(f"Helper path escapes its root: {relative}")
    return path


def files_under(root):
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError(f"Missing or unsafe helper directory: {root}")
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"Symlink in helper sources: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = digest(path.read_bytes())
    return result


def helper_sources():
    manifest = read_json(within(PLUGIN, "tools/helper-sources.json"))
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), dict):
        raise RuntimeError("Invalid tools/helper-sources.json; rebuild the plugin package")
    expected = manifest["files"]
    required = {f"{SCRIPTS}/package.json", f"{SCRIPTS}/bun.lock", f"{SCRIPTS}/bootstrap.ts", f"{SCRIPTS}/orch/orch.ts", f"{SCRIPTS}/watch-pr/watch-pr", LOG}
    if not required.issubset(expected) or any(not (name.startswith(SCRIPTS + "/") or name == LOG) for name in expected):
        raise RuntimeError("Helper source manifest has missing or unsupported paths")
    actual = {f"{SCRIPTS}/{name}": value for name, value in files_under(within(PLUGIN, SCRIPTS)).items()}
    log = within(PLUGIN, LOG)
    if not log.is_file():
        raise RuntimeError(f"Missing helper: {log}")
    actual[LOG] = digest(log.read_bytes())
    if actual != expected:
        raise RuntimeError("Packaged helper sources differ from their manifest; reinstall a verified plugin release")
    return actual, digest(encoded(actual))


def default_profile():
    return Path.home() / ".codex/pstack-codex/preferences.json"


def profile_show(path):
    defaults = validate_profile(read_json(within(PLUGIN, "defaults.json")))
    overrides = read_json(plain_path(path)) if path.exists() else {}
    return {"profile": str(path), "exists": path.exists(), "effective": validate_profile(merge(defaults, overrides)),
            "model_availability": "not evaluated; use the current host's supported models and effort values"}


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(encoded(value))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def profile_set(path, proposed, yes):
    path = plain_path(path)
    proposed = read_json(proposed)
    defaults = read_json(within(PLUGIN, "defaults.json"))
    current = read_json(path) if path.exists() else {}
    updated = merge(current, proposed)
    effective = validate_profile(merge(defaults, updated))
    # Store only user overrides. Unknown keys are preserved for newer adapters.
    if yes:
        atomic_json(path, updated)
    return {"written": yes, "profile": str(path), "overrides": updated, "effective": effective,
            "model_availability": "not evaluated; validation does not promise model availability"}


def state_root(value):
    path = plain_path(value)
    if path.resolve().is_relative_to(PLUGIN):
        raise RuntimeError("Mutable helper state must be outside the installed plugin")
    return path


@contextlib.contextmanager
def locked(state):
    state.mkdir(parents=True, exist_ok=True)
    path = within(state, ".setup.lock")
    with path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def runtime_paths(state, source_key):
    preparation = within(state, f"helpers/{source_key}")
    return preparation, within(preparation, "scripts")


def verify_copy(runtime, sources):
    expected = {name[len(SCRIPTS) + 1:]: value for name, value in sources.items() if name.startswith(SCRIPTS + "/")}
    actual = {}
    for path in sorted(runtime.rglob("*")):
        relative = path.relative_to(runtime).as_posix()
        if relative == "node_modules" or relative.startswith("node_modules/"):
            continue
        if path.is_symlink():
            raise RuntimeError(f"Symlink in prepared helper sources: {path}")
        if path.is_file():
            actual[relative] = digest(path.read_bytes())
    if actual != expected:
        raise RuntimeError("Prepared helper sources differ from their package; preserve local edits and remove this prepared runtime before setup")


def lock_key(runtime):
    return digest((runtime / "package.json").read_bytes() + b"\0" + (runtime / "bun.lock").read_bytes())


def dependencies_ready(runtime, key):
    marker = within(runtime, "node_modules/.poteto-mode-tools-install-key")
    commander = within(runtime, "node_modules/commander/package.json")
    return marker.is_file() and marker.read_text().strip() == key and commander.is_file()


def verify_receipt(preparation, runtime, source_key, require_dependencies=True):
    receipt = within(preparation, "setup-receipt.json")
    if not receipt.is_file():
        raise RuntimeError("Helpers are not prepared. Run python3 <plugin>/tools/runtime.py tools-setup --yes. No packages were installed.")
    record = read_json(receipt)
    key = lock_key(runtime)
    if record.get("source_key") != source_key or record.get("package_lock_key") != key:
        raise RuntimeError("Helper setup receipt does not match the package; run an explicit verified setup")
    if require_dependencies and not dependencies_ready(runtime, key):
        raise RuntimeError("Prepared dependencies are missing or have an invalid install marker; run tools-setup --yes")
    return record


def setup_tools(state):
    sources, source_key = helper_sources()
    bun = shutil.which("bun")
    if not bun:
        raise RuntimeError("Bun is not installed. Install it separately before tools-setup; no packages were installed.")
    with locked(state):
        preparation, runtime = runtime_paths(state, source_key)
        if not runtime.exists():
            preparation.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="prepare-", dir=preparation) as temporary:
                staged = Path(temporary) / "scripts"
                shutil.copytree(within(PLUGIN, SCRIPTS), staged)
                os.replace(staged, runtime)
        verify_copy(runtime, sources)
        receipt = within(preparation, "setup-receipt.json")
        if receipt.is_file():
            record = verify_receipt(preparation, runtime, source_key, require_dependencies=False)
            if dependencies_ready(runtime, record["package_lock_key"]):
                return {"prepared": True, "already_prepared": True, "runtime": str(runtime), "source_key": source_key}
        cache = within(state, "cache/bun")
        cache.mkdir(parents=True, exist_ok=True)
        environment = dict(os.environ, BUN_INSTALL_CACHE_DIR=str(cache))
        result = subprocess.run([bun, "install", "--frozen-lockfile", "--ignore-scripts"], cwd=runtime, env=environment, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f"Locked Bun setup failed ({result.returncode}): {result.stderr or result.stdout}")
        verify_copy(runtime, sources)
        commander = within(runtime, "node_modules/commander/package.json")
        if not commander.is_file():
            raise RuntimeError("Bun completed without commander; no valid setup receipt was written")
        key = lock_key(runtime)
        within(runtime, "node_modules/.poteto-mode-tools-install-key").write_text(key + "\n")
        version = subprocess.run([bun, "--version"], capture_output=True, text=True, check=True).stdout.strip()
        atomic_json(receipt, {"schema_version": 1, "source_key": source_key, "package_lock_key": key, "bun_version": version})
        verify_receipt(preparation, runtime, source_key)
        return {"prepared": True, "already_prepared": False, "runtime": str(runtime), "source_key": source_key, "bun_version": version}


def run_tool(state, name, arguments):
    sources, source_key = helper_sources()
    if arguments and arguments[0] == "--":
        arguments = arguments[1:]
    if name == "log":
        command = ["bash", str(within(PLUGIN, LOG))]
    else:
        preparation, runtime = runtime_paths(state, source_key)
        if not runtime.is_dir():
            raise RuntimeError("Helpers are not prepared. Run python3 <plugin>/tools/runtime.py tools-setup --yes. No packages were installed.")
        verify_copy(runtime, sources)
        verify_receipt(preparation, runtime, source_key)
        bun = shutil.which("bun")
        if not bun:
            raise RuntimeError("Bun is not installed; no packages were installed")
        entrypoint = "orch/orch.ts" if name == "orch" else "watch-pr/watch-pr"
        command = [bun, str(within(runtime, entrypoint))]
    return subprocess.call(command + arguments)


def parser():
    root = argparse.ArgumentParser(description=__doc__, epilog="Example: python3 <plugin>/tools/runtime.py profile show")
    root.add_argument("--state-root", type=Path, default=Path(os.environ.get("PSTACK_STATE_HOME", str(Path.home() / ".local/state/pstack-codex"))), help="Mutable helper state outside the plugin (or PSTACK_STATE_HOME)")
    commands = root.add_subparsers(dest="command", required=True)
    profiles = commands.add_parser("profile", help="Inspect or explicitly update optional local overrides", epilog="Example: runtime.py profile show")
    operations = profiles.add_subparsers(dest="operation", required=True)
    show = operations.add_parser("show", help="Read effective defaults plus optional overrides without writing", epilog="Example: runtime.py profile show --profile ./preferences.json")
    show.add_argument("--profile", type=Path, default=default_profile())
    update = operations.add_parser("set", help="Deep-merge proposed overrides while preserving unknown keys", epilog="Example: runtime.py profile set --file ./choices.json --dry-run")
    update.add_argument("--profile", type=Path, default=default_profile())
    update.add_argument("--file", type=Path, required=True)
    choice = update.add_mutually_exclusive_group(required=True)
    choice.add_argument("--dry-run", action="store_true")
    choice.add_argument("--yes", action="store_true")
    setup = commands.add_parser("tools-setup", help="Explicitly prepare locked Bun dependencies outside the plugin", epilog="Example: runtime.py tools-setup --yes")
    setup.add_argument("--yes", action="store_true", required=True)
    tool = commands.add_parser("tool", help="Run a verified helper; never installs packages", epilog="Examples: runtime.py tool orch -- --help; runtime.py tool log -- decisions.tsv plan choose reason evidence result")
    helpers = tool.add_subparsers(dest="name", required=True)
    for name in ("orch", "watch-pr", "log"):
        example = "decisions.tsv plan choose reason evidence result" if name == "log" else "--help"
        helper = helpers.add_parser(name, help=f"Run the {name} helper", epilog=f"Example: runtime.py tool {name} -- {example}")
        helper.add_argument("arguments", nargs=argparse.REMAINDER)
    return root


def main():
    options = parser().parse_args()
    try:
        if options.command == "profile":
            path = options.profile.expanduser().absolute()
            result = profile_show(path) if options.operation == "show" else profile_set(path, options.file, options.yes)
        elif options.command == "tools-setup":
            result = setup_tools(state_root(options.state_root))
        else:
            return run_tool(state_root(options.state_root), options.name, options.arguments)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"pstack runtime: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
