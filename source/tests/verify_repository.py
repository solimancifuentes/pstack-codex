#!/usr/bin/env python3
import json
from pathlib import Path
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import pstack as port
sys.path.pop(0)

repository = PROJECT.parent
with tempfile.TemporaryDirectory(prefix="pstack-verify-") as temporary:
    built = port.build(PROJECT, output=Path(temporary))
    manifest = port.verify_payload(built["path"])
    if port.read_json(repository / "release.json") != manifest:
        raise SystemExit("Tracked release.json differs from the reproducible build")
    if port.tree(repository / "plugins" / port.PLUGIN) != manifest["payload"]:
        raise SystemExit("Tracked plugin differs from the reproducible build")
    for relative, digest in port.tree(PROJECT / "distribution-docs").items():
        path = repository / relative
        if not path.is_file() or port.sha(path.read_bytes()) != digest:
            raise SystemExit("Distribution document differs: " + relative)
    print(json.dumps({"verified": True, "source_commit": manifest["source_commit"],
                      "upstream_version": manifest["upstream_version"],
                      "port_version": manifest["port_version"],
                      "release": manifest["release"], "skills": len(manifest["skills"]),
                      "payload_files": len(manifest["payload"])}, indent=2))
