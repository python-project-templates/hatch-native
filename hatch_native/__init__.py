__version__ = "0.1.0"

from .config import ExternalLibraryConfig, LibraryValidationConfig, ValidationCommandConfig
from .external import LIBRARY_SOURCES, ExternalLibrary, LibrarySource, pkg_config_variable, resolve_external_library, resolve_library_source
from .headers import check_headers, header_symbols, prefixed_header_symbols
from .manifest import MANIFEST_VERSION, write_artifact_manifest
from .naming import shared_library_name
from .symbols import exported_symbols
from .validation import check_exports, run_validation_command
