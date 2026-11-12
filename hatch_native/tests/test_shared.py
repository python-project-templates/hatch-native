from json import loads
from pathlib import Path

import pytest
from pydantic import ValidationError

from hatch_native import (
    LibraryValidationConfig,
    check_exports,
    check_headers,
    header_symbols,
    prefixed_header_symbols,
    resolve_external_library,
    resolve_library_source,
    shared_library_name,
    write_artifact_manifest,
)

HEADER = """
#define DEMO_ABI_VERSION 1
/* demo_commented(void); */
typedef int (*demo_callback)(int);
int demo_answer(void);
void demo_free(void *ptr);
static inline int demo_inline(void) { return 1; }
"""


def test_header_symbols_skip_comments_pointers_and_inline():
    assert header_symbols(HEADER, "demo_") == ["demo_answer", "demo_free"]


def test_check_headers_resolves_and_finds_abi_string(tmp_path):
    (tmp_path / "demo.h").write_text(HEADER)
    assert check_headers([Path("demo.h")], ["DEMO_ABI_VERSION 1"], base=tmp_path, label="demo") == [(tmp_path / "demo.h").resolve()]


def test_check_headers_errors(tmp_path):
    with pytest.raises(FileNotFoundError, match="expected header does not exist"):
        check_headers([Path("missing.h")], [], base=tmp_path, label="demo")
    with pytest.raises(ValueError, match="must set expected-headers"):
        check_headers([], ["DEMO_ABI_VERSION"], base=tmp_path, label="demo")
    (tmp_path / "demo.h").write_text(HEADER)
    with pytest.raises(RuntimeError, match="ABI string was not found"):
        check_headers([Path("demo.h")], ["DEMO_ABI_VERSION 2"], base=tmp_path, label="demo")


def test_prefixed_header_symbols(tmp_path):
    header = tmp_path / "demo.h"
    header.write_text(HEADER)
    assert prefixed_header_symbols([header], None, label="demo") == []
    assert prefixed_header_symbols([header], "demo_", label="demo") == ["demo_answer", "demo_free"]
    with pytest.raises(RuntimeError, match="declare no functions starting with 'other_'"):
        prefixed_header_symbols([header], "other_", label="demo")


def test_check_exports_reports_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("hatch_native.validation.exported_symbols", lambda path: {"demo_answer"})
    check_exports(tmp_path / "libdemo.so", expected=["demo_answer"], load=False, label="demo", display_path="lib/libdemo.so")
    with pytest.raises(RuntimeError, match="expected symbol was not exported: demo_free"):
        check_exports(tmp_path / "libdemo.so", expected=["demo_answer", "demo_free"], load=False, label="demo", display_path="lib/libdemo.so")


@pytest.mark.parametrize(
    "platform,filename",
    [("linux", "libdemo.so"), ("darwin", "libdemo.dylib"), ("win32", "demo.dll"), ("emscripten", "demo.wasm")],
)
def test_shared_library_name(platform, filename):
    assert shared_library_name("demo", platform=platform) == filename


def test_resolve_library_source(monkeypatch):
    monkeypatch.delenv("DEMO_LIBRARY_SOURCE", raising=False)
    assert resolve_library_source("bundled", env_var="DEMO_LIBRARY_SOURCE") == "bundled"
    monkeypatch.setenv("DEMO_LIBRARY_SOURCE", "external")
    assert resolve_library_source("bundled", env_var="DEMO_LIBRARY_SOURCE") == "external"
    monkeypatch.setenv("DEMO_LIBRARY_SOURCE", "vendored")
    with pytest.raises(ValueError, match="Unsupported DEMO_LIBRARY_SOURCE: vendored"):
        resolve_library_source("bundled", env_var="DEMO_LIBRARY_SOURCE")


def test_resolve_external_library_from_root(tmp_path):
    (tmp_path / "lib").mkdir()
    (tmp_path / "include").mkdir()
    (tmp_path / "lib" / "libdemo.so.1").write_bytes(b"")
    external = resolve_external_library("demo", label="demo", platform="linux", root_env_var="DEMO_ROOT", root=tmp_path)
    assert external.library == tmp_path / "lib" / "libdemo.so.1"
    assert external.include_dir == tmp_path / "include"
    assert external.link_name == "demo"


def test_resolve_external_library_windows_prefers_bin_and_import_library(tmp_path):
    (tmp_path / "lib").mkdir()
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "demo.dll").write_bytes(b"")
    (tmp_path / "lib" / "demo.lib").write_bytes(b"")
    external = resolve_external_library("demo", label="demo", platform="win32", root_env_var="DEMO_ROOT", root=tmp_path)
    assert external.library == tmp_path / "bin" / "demo.dll"
    assert external.link_name == "demo"
    assert external.include_dir is None


def test_resolve_external_library_errors(monkeypatch, tmp_path):
    monkeypatch.delenv("PREFIX", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    with pytest.raises(ValueError, match="DEMO_ROOT, PREFIX, or CONDA_PREFIX"):
        resolve_external_library("demo", label="demo", platform="linux", root_env_var="DEMO_ROOT")
    with pytest.raises(FileNotFoundError, match="external library 'libdemo.so' was not found"):
        resolve_external_library("demo", label="demo", platform="linux", root_env_var="DEMO_ROOT", root=tmp_path)
    with pytest.raises(ValueError, match="package 'not_a_real_package' is not installed"):
        resolve_external_library("demo", label="demo", platform="linux", root_env_var="DEMO_ROOT", package="not_a_real_package")


def test_write_artifact_manifest(tmp_path):
    destination = tmp_path / "demo" / "lib" / "artifacts.json"
    write_artifact_manifest(destination, module="demo", records=[{"name": "demo", "role": "library"}])
    assert loads(destination.read_text()) == {"version": 1, "module": "demo", "artifacts": [{"name": "demo", "role": "library"}]}


def test_validation_config_accepts_both_spellings():
    kebab = LibraryValidationConfig.model_validate({"expected-symbols": "demo_answer", "expected-headers": "demo.h", "validate": True})
    snake = LibraryValidationConfig(expected_symbols=["demo_answer"], expected_headers=[Path("demo.h")], validate_artifact=True)
    assert kebab == snake
    assert LibraryValidationConfig.model_validate({"validation-commands": ["true"]}).validation_commands[0].command == ["true"]


def test_validation_config_requires_headers_for_prefix():
    with pytest.raises(ValidationError, match="must set expected-headers when using header-symbol-prefix"):
        LibraryValidationConfig.model_validate({"header-symbol-prefix": "demo_"})
