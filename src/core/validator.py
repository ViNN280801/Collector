from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from .exceptions import PathError, ValidationError
from .security_constants import MAX_PATTERN_LENGTH, MAX_PATH_LENGTH, MAX_SOURCE_PATHS

if TYPE_CHECKING:
    from .config import CollectionConfig


def validate_path(path: Path) -> bool:
    path_str = str(path)
    if not path_str or path_str == "" or path_str == ".":
        return False
    return path.exists()


def validate_disk_space(path: Path, required_bytes: int) -> bool:
    if not path.exists():
        return False

    try:
        check_path = path
        if check_path.is_file():
            check_path = check_path.parent
        if not check_path.exists():
            return False
        usage = shutil.disk_usage(check_path)
        total, used, free = usage
        return free >= required_bytes
    except OSError:
        raise PathError(f"Cannot check disk space for path: {path}") from None


def _check_redos_pattern(pattern: str) -> bool:
    dangerous_patterns = [
        r"\(.*\+.*\)\+",
        r"\(.*\*.*\)\*",
        r"\(.*\?.*\)\?",
        r"\(.*\{.*,.*\}.*\)\+",
        r"\(.*\{.*,.*\}.*\)\*",
    ]
    for dangerous in dangerous_patterns:
        if re.search(dangerous, pattern):
            return True
    return False


def validate_config(config: CollectionConfig) -> bool:
    if not config.source_paths:
        raise ValidationError("source_paths cannot be empty")

    if len(config.source_paths) > MAX_SOURCE_PATHS:
        raise ValidationError(f"Too many source paths: {len(config.source_paths)} (max: {MAX_SOURCE_PATHS})")

    for source_path in config.source_paths:
        path_str = str(source_path)
        if len(path_str) > MAX_PATH_LENGTH:
            raise ValidationError(f"Source path too long: {len(path_str)} characters (max: {MAX_PATH_LENGTH})")
        if not validate_path(source_path):
            raise ValidationError(f"Source path does not exist: {source_path}")
        if not source_path.is_dir():
            raise ValidationError(f"Source path is not a directory: {source_path}")

    target_path_str = str(config.target_path)
    if len(target_path_str) > MAX_PATH_LENGTH:
        raise ValidationError(f"Target path too long: {len(target_path_str)} characters (max: {MAX_PATH_LENGTH})")

    target_parent = config.target_path.parent
    if target_parent and not validate_path(target_parent):
        raise ValidationError(f"Target path parent does not exist: {target_parent}")

    if config.target_path.exists() and not config.target_path.is_dir():
        raise ValidationError(f"Target path exists but is not a directory: {config.target_path}")

    for pattern_config in config.patterns:
        if len(pattern_config.pattern) > MAX_PATTERN_LENGTH:
            raise ValidationError(
                f"Pattern too long: {len(pattern_config.pattern)} characters (max: {MAX_PATTERN_LENGTH})"
            )
        if pattern_config.pattern_type == "regex":
            if _check_redos_pattern(pattern_config.pattern):
                raise ValidationError(f"Potentially dangerous regex pattern detected (ReDoS): {pattern_config.pattern}")

    return True
