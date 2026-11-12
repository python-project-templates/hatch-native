from __future__ import annotations

from ctypes import CDLL
from pathlib import Path
from shlex import join as shell_join
from subprocess import run

from .symbols import exported_symbols

__all__ = ("check_exports", "run_validation_command")


def check_exports(library: Path, *, expected: list[str], load: bool, label: str, display_path: str) -> None:
    """Require `expected` symbols in the export table of `library`, then optionally load it with ctypes."""
    if expected:
        try:
            exported = exported_symbols(library)
        except (OSError, ValueError) as error:
            raise RuntimeError(f"Artifact '{label}' could not read exported symbols from '{display_path}': {error}") from error
        missing = [symbol for symbol in expected if symbol not in exported]
        if missing:
            raise RuntimeError(f"Artifact '{label}' expected symbol was not exported: {', '.join(missing)}")

    if load:
        try:
            CDLL(str(library))
        except OSError as error:
            raise RuntimeError(f"Artifact '{label}' failed validation load check for '{display_path}': {error}") from error


def run_validation_command(command: list[str], *, cwd: Path, env: dict[str, str], label: str) -> None:
    """Run one validation command argv, raising with the artifact label on a missing executable or non-zero exit."""
    try:
        completed = run(command, cwd=cwd, env=env, check=False)
    except FileNotFoundError as error:
        raise RuntimeError(f"Artifact '{label}' validation command was not found: {command[0]}") from error
    if completed.returncode != 0:
        raise RuntimeError(f"Artifact '{label}' validation command failed with exit code {completed.returncode}: {shell_join(command)}")
