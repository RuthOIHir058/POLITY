"""Verify that project and packaged SQLite snapshots are byte-identical."""

from __future__ import annotations

import hashlib

from tools.validation._common import PACKAGED_DATABASE, PROJECT_DATABASE, require_database


def sha256(path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    packaged = require_database(PACKAGED_DATABASE)
    packaged_hash = sha256(packaged)
    if not PROJECT_DATABASE.is_file():
        print(f"PASS packaged database SHA-256 {packaged_hash}")
        print("Project-level snapshot is not present in this installed package.")
        return 0

    project = require_database(PROJECT_DATABASE)
    project_hash = sha256(project)
    if project_hash != packaged_hash:
        raise SystemExit(
            "FAIL: bundled databases differ: "
            f"project={project_hash}, packaged={packaged_hash}"
        )
    print(f"PASS database SHA-256 {project_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
