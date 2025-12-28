from __future__ import annotations

import os
from pathlib import Path

from .exceptions import SecurityError
from .security_constants import (
    MAX_PATH_LENGTH,
    get_dangerous_chars,
    get_reserved_names,
    is_windows,
)


def sanitize_path(path: str) -> Path:
    if len(path) > MAX_PATH_LENGTH:
        raise SecurityError(f"Path exceeds maximum length ({MAX_PATH_LENGTH}): {len(path)} characters")

    dangerous_chars = get_dangerous_chars()
    path_parts = Path(path).parts
    for part in path_parts:
        for char in dangerous_chars:
            if char in part:
                raise SecurityError(f"Dangerous character detected in path component: {repr(char)}")

    reserved_names = get_reserved_names()
    if reserved_names:
        for part in path_parts:
            if is_windows():
                name_without_ext = part.split(".")[0].upper()
                if name_without_ext in reserved_names:
                    raise SecurityError(f"Reserved name detected: {part}")
            else:
                if part in reserved_names:
                    raise SecurityError(f"Reserved name detected: {part}")

    normalized = os.path.normpath(path)
    absolute = os.path.abspath(normalized)
    return Path(absolute)


def validate_path_traversal(path: Path, base_dir: Path) -> bool:
    path_resolved = path.resolve()
    base_resolved = base_dir.resolve()

    try:
        if hasattr(path_resolved, "is_relative_to"):
            return bool(path_resolved.is_relative_to(base_resolved))
    except (ValueError, AttributeError):
        pass

    try:
        common = os.path.commonpath([str(path_resolved), str(base_resolved)])
        return bool(os.path.commonpath([common, str(base_resolved)]) == str(base_resolved))
    except (ValueError, OSError):
        return False


def resolve_path(base: Path, relative: str) -> Path:
    base_normalized = sanitize_path(str(base))

    if os.path.isabs(relative):
        raise SecurityError(f"Absolute paths are not allowed: {relative}")

    # Detect backslash-based path traversal patterns (Windows-style) BEFORE Path operations
    # On Linux, Path treats backslashes as literal characters, so we need to check the string directly
    # Check for patterns like "..\\", "..\..\", etc. that attempt path traversal
    if "\\" in relative:
        # Normalize backslashes to forward slashes to detect traversal patterns
        normalized_for_check = relative.replace("\\", "/")
        # Check if the normalized path contains traversal patterns
        if ".." in normalized_for_check:
            # Verify this would actually result in traversal by checking the normalized path
            if not validate_path_traversal(base_normalized / normalized_for_check, base_normalized):
                raise SecurityError(f"Path traversal detected: {relative}")
            # If backslashes are present and we've already checked the normalized version,
            # skip the forward-slash check below to avoid redundant validation
            relative_has_backslashes_checked = True
        else:
            relative_has_backslashes_checked = False
    else:
        relative_has_backslashes_checked = False

    # Check for forward-slash based traversal patterns (only if not already checked above)
    if not relative_has_backslashes_checked and ".." in relative:
        if not validate_path_traversal(base_normalized / relative, base_normalized):
            raise SecurityError(f"Path traversal detected: {relative}")

    resolved = (base_normalized / relative).resolve()

    if not validate_path_traversal(resolved, base_normalized):
        raise SecurityError(f"Resolved path is outside base directory: {resolved}")

    return resolved
