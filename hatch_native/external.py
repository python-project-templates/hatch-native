from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from os import environ
from pathlib import Path
from shlex import join as shell_join
from subprocess import run
from typing import Literal

from .naming import shared_library_name

__all__ = (
    "LIBRARY_SOURCES",
    "ExternalLibrary",
    "LibrarySource",
    "pkg_config_variable",
    "resolve_external_library",
    "resolve_library_source",
)

LibrarySource = Literal["bundled", "external", "static", "direct"]
LIBRARY_SOURCES: tuple[str, ...] = ("bundled", "external", "static", "direct")


@dataclass(frozen=True)
class ExternalLibrary:
    """A prebuilt C ABI library resolved outside the build."""

    name: str
    library: Path
    library_dir: Path
    include_dir: Path | None
    link_name: str
    package: str | None = None


def resolve_library_source(configured: str, *, env_var: str) -> str:
    """Return `env_var` if set, else `configured`, rejecting anything but the four library-source modes."""
    value = environ.get(env_var) or configured
    if value not in LIBRARY_SOURCES:
        raise ValueError(f"Unsupported {env_var}: {value}")
    return value


def pkg_config_variable(module: str, variable: str, *, label: str) -> Path:
    """Read one pkg-config variable, such as libdir or includedir, for `module`."""
    command = ["pkg-config", f"--variable={variable}", module]
    try:
        completed = run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as error:
        raise RuntimeError(f"Artifact '{label}' needs pkg-config on PATH to resolve '{module}'.") from error
    if completed.returncode != 0 or not completed.stdout.strip():
        raise RuntimeError(f"Artifact '{label}' pkg-config lookup failed: {shell_join(command)}: {completed.stderr.strip()}")
    return Path(completed.stdout.strip())


def resolve_external_library(
    name: str,
    *,
    label: str,
    platform: str,
    root_env_var: str,
    root: Path | None = None,
    package: str | None = None,
    pkg_config: str | None = None,
) -> ExternalLibrary:
    """Locate a prebuilt library and its headers.

    Lookup order: an explicit `root` prefix, an installed Python `package`
    shipping `lib/` and `include/`, a `pkg_config` module, then `$PREFIX` or
    `$CONDA_PREFIX` (with `Library/` on Windows). `root_env_var` only names the
    caller's override in the error message.
    """
    if root is not None:
        library_dir, include_dir = root / "lib", root / "include"
    elif package:
        spec = find_spec(package)
        if spec is None or not spec.submodule_search_locations:
            raise ValueError(f"Artifact '{label}' package '{package}' is not installed in the build environment.")
        prefix = Path(next(iter(spec.submodule_search_locations)))
        library_dir, include_dir = prefix / "lib", prefix / "include"
    elif pkg_config:
        library_dir = pkg_config_variable(pkg_config, "libdir", label=label)
        include_dir = pkg_config_variable(pkg_config, "includedir", label=label)
    else:
        conda_prefix = environ.get("PREFIX") or environ.get("CONDA_PREFIX")
        if not conda_prefix:
            raise ValueError(f"Artifact '{label}' is external but has no library-root, pkg-config, {root_env_var}, PREFIX, or CONDA_PREFIX.")
        prefix = Path(conda_prefix) / "Library" if platform == "win32" else Path(conda_prefix)
        library_dir, include_dir = prefix / "lib", prefix / "include"

    shared_library = shared_library_name(name, platform=platform)
    if platform == "win32":
        candidates = [library_dir.parent / "bin" / shared_library, library_dir / shared_library]
        link_name = name if (library_dir / f"{name}.lib").is_file() else f"{name}.dll"
    elif platform == "darwin":
        candidates = [library_dir / shared_library, *sorted(library_dir.glob(f"lib{name}.*.dylib"))]
        link_name = name
    else:
        candidates = [library_dir / shared_library, *sorted(library_dir.glob(f"{shared_library}.*"))]
        link_name = name
    library = next((candidate for candidate in candidates if candidate.is_file()), None)
    if library is None:
        searched = ", ".join(str(candidate.parent) for candidate in candidates[:2])
        raise FileNotFoundError(f"Artifact '{label}' external library '{shared_library}' was not found under {searched}.")
    return ExternalLibrary(
        name=name,
        library=library,
        library_dir=library_dir,
        include_dir=include_dir if include_dir.is_dir() else None,
        link_name=link_name,
        package=package,
    )
