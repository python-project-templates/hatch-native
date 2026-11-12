from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = ("ExternalLibraryConfig", "LibraryValidationConfig", "ValidationCommandConfig")


class ValidationCommandConfig(BaseModel):
    """A project-specific command used to validate a built artifact."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    command: list[str] = Field(description="Validation command argv list.")
    working_directory: Path | None = Field(default=None, alias="working-directory", description="Validation command working directory.")
    env: dict[str, str] = Field(default_factory=dict, description="Additional environment variables for this validation command.")

    @field_validator("command", mode="before")
    @classmethod
    def validate_command(cls, values: Any) -> list[str]:
        if isinstance(values, str):
            raise TypeError("Validation command must be an argv list, not a shell string.")
        return [str(value) for value in values]

    @field_validator("working_directory", mode="before")
    @classmethod
    def validate_working_directory(cls, path: Path | None) -> Path | None:
        if path is None:
            return None
        if not isinstance(path, Path):
            path = Path(path)
        return path


class LibraryValidationConfig(BaseModel):
    """Header and export validation fields, named the same in every hatch native plugin.

    Each field accepts its kebab-case name in pyproject.toml and its
    snake_case name in Python.
    """

    expected_symbols: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("expected-symbols", "expected_symbols"),
        description="Exported symbols expected in a copied library.",
    )
    header_symbol_prefix: str | None = Field(
        default=None,
        validation_alias=AliasChoices("header-symbol-prefix", "header_symbol_prefix"),
        description="Expect every function in expected-headers whose name starts with this prefix to be exported.",
    )
    expected_headers: list[Path] = Field(
        default_factory=list,
        validation_alias=AliasChoices("expected-headers", "expected_headers"),
        description="Header files expected to exist after build.",
    )
    expected_abi_strings: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("expected-abi-strings", "expected_abi_strings"),
        description="ABI version strings or macros expected in the configured headers.",
    )
    validate_artifact: bool = Field(
        default=False,
        validation_alias=AliasChoices("validate", "validate_artifact"),
        description="Load the copied library with ctypes.CDLL after copy. Requires a library built for the host.",
    )
    validation_commands: list[ValidationCommandConfig] = Field(
        default_factory=list,
        validation_alias=AliasChoices("validation-commands", "validation_commands"),
        description="Project-specific validation commands to run after artifact copy.",
    )

    @field_validator("expected_symbols", "expected_abi_strings", mode="before")
    @classmethod
    def validate_validation_strings(cls, values: Any) -> list[str]:
        if values is None:
            return []
        if isinstance(values, str):
            return [values]
        return [str(value) for value in values]

    @field_validator("expected_headers", mode="before")
    @classmethod
    def validate_expected_headers(cls, values: Any) -> list[Path]:
        if values is None:
            return []
        if isinstance(values, (str, Path)):
            values = [values]
        return [value if isinstance(value, Path) else Path(value) for value in values]

    @field_validator("validation_commands", mode="before")
    @classmethod
    def validate_validation_commands(cls, values: Any) -> list[Any]:
        if values is None:
            return []
        if isinstance(values, dict):
            return [values]
        if isinstance(values, list) and values and all(not isinstance(value, dict) for value in values):
            return [{"command": values}]
        return list(values)

    @model_validator(mode="after")
    def validate_header_symbol_prefix(self):
        if self.header_symbol_prefix is not None and not self.expected_headers:
            raise ValueError(f"Artifact '{getattr(self, 'name', None)}' must set expected-headers when using header-symbol-prefix.")
        return self


class ExternalLibraryConfig(BaseModel):
    """Where to find a prebuilt library when it is not built by this project."""

    pkg_config: str | None = Field(
        default=None,
        validation_alias=AliasChoices("pkg-config", "pkg_config"),
        description="pkg-config module locating this library in external mode.",
    )
    library_root: Path | None = Field(
        default=None,
        validation_alias=AliasChoices("library-root", "library_root"),
        description="Prefix with lib/ and include/ for this library in external mode.",
    )
    python_package: str | None = Field(
        default=None,
        validation_alias=AliasChoices("python-package", "python_package"),
        description="Installed Python package shipping this library under lib/ and include/; linked from there instead of built.",
    )

    @field_validator("library_root", mode="before")
    @classmethod
    def validate_library_root(cls, path: Path | None) -> Path | None:
        if path is None:
            return None
        if not isinstance(path, Path):
            path = Path(path)
        return path
