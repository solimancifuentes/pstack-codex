#!/usr/bin/env python3
"""Export one verified pstack release as a Git marketplace and plugin-only ZIP."""

import argparse
import json
from pathlib import Path
import shutil
import stat
import tempfile
import zipfile

import pstack as port


def export_release(project, release, destination):
    project, release, destination = map(lambda value: Path(value).resolve(), (project, release, destination))
    manifest = port.verify_payload(release)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="distribution-", dir=destination.parent) as temporary:
        staged = Path(temporary) / "export"
        repository = staged / "repository"
        package = repository / "plugins" / port.PLUGIN
        shutil.copytree(release / "plugin", package)
        port.write_json(repository / ".agents/plugins/marketplace.json", {
            "name": "pstack-codex",
            "interface": {"displayName": "pstack"},
            "plugins": [{"name": port.PLUGIN,
                         "source": {"source": "local", "path": "./plugins/" + port.PLUGIN},
                         "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                         "category": "Developer Tools"}]})
        docs = project / "distribution-docs"
        if docs.exists():
            shutil.copytree(docs, repository, dirs_exist_ok=True)
        shutil.copy2(package / "LICENSE", repository / "LICENSE")
        shutil.copy2(package / "NOTICE", repository / "NOTICE")
        source = repository / "source"
        source.mkdir()
        for name in ("pstack.py", "distribution.py", "source.lock.json", "defaults.json",
                     "preferences.example.json", "publication.json", "NOTICE", "migration-baseline.json"):
            shutil.copy2(project / name, source / name)
        for name in ("runtime", "tests", "standalone-originals", "distribution-docs"):
            shutil.copytree(project / name, source / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(release / "adapters", source / "adapters")
        shutil.copytree(release / "source/pstack", source / "upstream/pstack")
        port.write_json(source / "source.lock.json", {
            "repository": manifest["repository"], "commit": manifest["source_commit"],
            "upstream_version": manifest["upstream_version"], "files": manifest["source"]})
        if port.sha((source / "pstack.py").read_bytes()) != manifest["manager_sha256"]:
            raise port.PortError("Exported manager source differs from the selected release; rebuild from the reviewed manager before exporting")
        reproduced = port.build(source, output=Path(temporary) / "reproduced")
        if reproduced["release"] != manifest["release"]:
            raise port.PortError("Export source does not reproduce the selected release. Build a new release from the reviewed source before exporting")
        port.write_json(repository / "release.json", manifest)
        archive_name = f"{port.PLUGIN}-{manifest['port_version']}.zip"
        archive = staged / archive_name
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for path in sorted(package.rglob("*")):
                if path.is_symlink():
                    raise port.PortError(f"Symlink is not distributable: {path.relative_to(package)}")
                if path.is_file():
                    entry = zipfile.ZipInfo(port.PLUGIN + "/" + path.relative_to(package).as_posix(),
                                            date_time=(2026, 1, 1, 0, 0, 0))
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    entry.create_system = 3
                    entry.external_attr = (stat.S_IFREG | 0o644) << 16
                    bundle.writestr(entry, path.read_bytes())
        with zipfile.ZipFile(archive) as bundle:
            if bundle.testzip() is not None:
                raise port.PortError("Distribution ZIP failed CRC validation")
        (staged / (archive_name + ".sha256")).write_text(port.sha(archive.read_bytes()) + "  " + archive_name + "\n")
        if destination.exists():
            if port.tree(destination) != port.tree(staged):
                raise port.PortError("Export destination differs; choose an empty output directory to preserve local changes")
        else:
            staged.rename(destination)
    return {"release": manifest["release"], "repository": str(destination / "repository"),
            "archive": str(destination / archive_name), "sha256": port.sha((destination / archive_name).read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(export_release(args.project, args.release, args.output), indent=2))
    except (port.PortError, OSError, ValueError) as error:
        parser.exit(1, json.dumps({"error": str(error)}) + "\n")


if __name__ == "__main__":
    main()
