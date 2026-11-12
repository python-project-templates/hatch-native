from __future__ import annotations

from json import dumps
from pathlib import Path

__all__ = ("MANIFEST_VERSION", "write_artifact_manifest")

MANIFEST_VERSION = 1


def write_artifact_manifest(destination: Path, *, module: str, records: list[dict[str, str]]) -> None:
    """Write the artifact manifest JSON shared by the hatch native plugins."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": MANIFEST_VERSION, "module": module, "artifacts": records}
    destination.write_text(dumps(payload, indent=2, sort_keys=True) + "\n")
