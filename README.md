# hatch native

Shared native-build helpers for hatch plugins

[![Build Status](https://github.com/python-project-templates/hatch-native/actions/workflows/build.yaml/badge.svg?branch=main&event=push)](https://github.com/python-project-templates/hatch-native/actions/workflows/build.yaml)
[![codecov](https://codecov.io/gh/python-project-templates/hatch-native/branch/main/graph/badge.svg)](https://codecov.io/gh/python-project-templates/hatch-native)
[![License](https://img.shields.io/github/license/python-project-templates/hatch-native)](https://github.com/python-project-templates/hatch-native)
[![PyPI](https://img.shields.io/pypi/v/hatch-native.svg)](https://pypi.python.org/pypi/hatch-native)

## Overview

Helpers shared by the hatch native build plugins ([hatch-rs](https://github.com/python-project-templates/hatch-rs), [hatch-cpp](https://github.com/python-project-templates/hatch-cpp)) for wheels that ship a C ABI library next to a Python extension. It is a library for plugin authors, not a hatch plugin, and has no configuration of its own.

| Module       | Provides                                                                                                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `symbols`    | `exported_symbols(path)`: the export table of an ELF, Mach-O (including fat), PE, or WebAssembly binary, read without loading it                                                     |
| `headers`    | `header_symbols(text, prefix)`, `check_headers(...)` for expected headers and ABI strings, `prefixed_header_symbols(...)`                                                            |
| `validation` | `check_exports(...)` for expected symbols plus an optional `ctypes` load, `run_validation_command(...)`                                                                              |
| `config`     | pydantic models `LibraryValidationConfig`, `ExternalLibraryConfig`, `ValidationCommandConfig`, so every plugin uses the same field names                                             |
| `external`   | `resolve_library_source(...)` for `bundled`, `external`, `static`, `direct`; `resolve_external_library(...)` from a root, a Python package, pkg-config, or `$PREFIX`/`$CONDA_PREFIX` |
| `manifest`   | `write_artifact_manifest(...)`: `{"version": 1, "module": ..., "artifacts": [...]}`                                                                                                  |
| `naming`     | `shared_library_name(name, platform=...)`: `libfoo.so`, `libfoo.dylib`, `foo.dll`, `foo.wasm`                                                                                        |

Plugins mix the config models into their own artifact models, so a project writes the same keys whichever plugin builds the library:

```toml
expected-headers = ["include/foo/foo.h"]
header-symbol-prefix = "foo_"
expected-abi-strings = ["FOO_ABI_VERSION 1"]
validate = false
```

Each key also accepts its snake_case spelling.

> [!NOTE]
> This library was generated using [copier](https://copier.readthedocs.io/en/stable/) from the [Base Python Project Template repository](https://github.com/python-project-templates/base).
