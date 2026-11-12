from __future__ import annotations

from pathlib import Path
from re import DOTALL, MULTILINE, escape, findall, sub

__all__ = ("check_headers", "header_symbols", "prefixed_header_symbols")


def header_symbols(text: str, prefix: str) -> list[str]:
    """Functions declared in a C header whose names start with `prefix`.

    Comments, preprocessor lines, `static inline` definitions, and function
    pointer declarators such as `prefix_status (*open)(...)` are skipped, since
    none of them is exported by the library. Declarations are found with
    regular expressions rather than a C parser, which works for a hand-written
    or generated ABI header.
    """
    text = sub(r"/\*.*?\*/", " ", text, flags=DOTALL)
    text = sub(r"//[^\n]*", " ", text)
    text = sub(r"^\s*#.*?(?<!\\)$", " ", text, flags=MULTILINE | DOTALL)
    text = sub(r"\bstatic\s+inline\b[^;{]*\{", "static inline {", text)
    declared = findall(rf"\b({escape(prefix)}\w*)\s*\((?!\s*\*)", text)
    inline = set(findall(rf"\bstatic\s+(?:inline\s+)?[^;{{(]*?\b({escape(prefix)}\w*)\s*\((?!\s*\*)", text))
    return sorted(set(declared) - inline)


def check_headers(headers: list[Path], abi_strings: list[str], *, base: Path, label: str) -> list[Path]:
    """Resolve expected headers against `base`, require each to be a file, and require every ABI string in one of them."""
    resolved = []
    for header in headers:
        path = Path(header)
        path = path.resolve() if path.is_absolute() else (base / path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Artifact '{label}' expected header does not exist: {header}")
        if not path.is_file():
            raise FileNotFoundError(f"Artifact '{label}' expected header is not a file: {header}")
        resolved.append(path)

    if abi_strings and not resolved:
        raise ValueError(f"Artifact '{label}' must set expected-headers when using expected-abi-strings.")

    for expected in abi_strings:
        if not any(expected in header.read_text(errors="replace") for header in resolved):
            raise RuntimeError(f"Artifact '{label}' expected ABI string was not found in headers: {expected}")
    return resolved


def prefixed_header_symbols(headers: list[Path], prefix: str | None, *, label: str) -> list[str]:
    """Functions starting with `prefix` across `headers`; an error if a prefix is set and none match."""
    if prefix is None:
        return []
    symbols = sorted({symbol for header in headers for symbol in header_symbols(header.read_text(errors="replace"), prefix)})
    if not symbols:
        raise RuntimeError(f"Artifact '{label}' expected headers declare no functions starting with '{prefix}'.")
    return symbols
