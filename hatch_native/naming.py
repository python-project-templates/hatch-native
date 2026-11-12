from __future__ import annotations

__all__ = ("shared_library_name",)


def shared_library_name(library: str, *, platform: str) -> str:
    """Render a platform-specific standalone shared-library filename."""
    if platform == "win32":
        return f"{library}.dll"
    if platform == "darwin":
        return f"lib{library}.dylib"
    if platform == "linux":
        return f"lib{library}.so"
    if platform == "emscripten":
        return f"{library}.wasm"
    raise ValueError(f"Unsupported platform: {platform}")
