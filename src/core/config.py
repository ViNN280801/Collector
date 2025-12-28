from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PatternConfig:
    pattern: str
    pattern_type: str = "glob"

    def __post_init__(self) -> None:
        if self.pattern_type not in ("regex", "glob"):
            raise ValueError(f"Invalid pattern_type: {self.pattern_type}")


@dataclass
class CollectionConfig:
    source_paths: List[Path]
    target_path: Path
    patterns: List[PatternConfig] = field(default_factory=list)
    operation_mode: str = "copy"
    create_archive: bool = False
    archive_format: str = "zip"
    archive_compression: Optional[str] = None
    send_email: bool = False
    email_config: Optional[Dict[str, Any]] = None
    collect_system_info: bool = True
    enable_audit_logging: bool = True
    audit_log_file: Optional[Path] = None

    def __post_init__(self) -> None:
        if self.operation_mode not in ("copy", "move", "move_remove"):
            raise ValueError(f"Invalid operation_mode: {self.operation_mode}")
        if self.archive_format not in ("zip", "tar", "7z"):
            raise ValueError(f"Invalid archive_format: {self.archive_format}")


class CollectionConfigBuilder:
    def __init__(self) -> None:
        self._source_paths: Optional[List[Path]] = None
        self._target_path: Optional[Path] = None
        self._patterns: List[PatternConfig] = []
        self._operation_mode: str = "copy"
        self._create_archive: bool = False
        self._archive_format: str = "zip"
        self._send_email: bool = False
        self._email_config: Optional[Dict[str, Any]] = None
        self._collect_system_info: bool = True
        self._enable_audit_logging: bool = True
        self._audit_log_file: Optional[Path] = None
        self._archive_compression: Optional[str] = None

    def with_source_paths(self, paths: List[Path]) -> CollectionConfigBuilder:
        self._source_paths = [Path(p) for p in paths]
        return self

    def with_target_path(self, path: Path) -> CollectionConfigBuilder:
        self._target_path = Path(path)
        return self

    def with_patterns(self, patterns: List[PatternConfig]) -> CollectionConfigBuilder:
        self._patterns = patterns
        return self

    def with_operation_mode(self, mode: str) -> CollectionConfigBuilder:
        if mode not in ("copy", "move", "move_remove"):
            raise ValueError(f"Invalid operation_mode: {mode}")
        self._operation_mode = mode
        return self

    def with_archive(
        self, create: bool, format: str = "zip", compression: Optional[str] = None
    ) -> CollectionConfigBuilder:
        if format not in ("zip", "tar", "7z"):
            raise ValueError(f"Invalid archive_format: {format}")
        if compression and compression not in ("gzip", "bzip2", "xz"):
            raise ValueError(f"Invalid compression: {compression}")
        self._create_archive = create
        self._archive_format = format
        self._archive_compression = compression
        return self

    def with_email(self, send: bool, config: Optional[Dict[str, Any]] = None) -> CollectionConfigBuilder:
        self._send_email = send
        self._email_config = config
        return self

    def with_system_info(self, collect: bool) -> CollectionConfigBuilder:
        self._collect_system_info = collect
        return self

    def with_audit_logging(self, enable: bool, log_file: Optional[Path] = None) -> CollectionConfigBuilder:
        self._enable_audit_logging = enable
        self._audit_log_file = log_file
        return self

    def build(self) -> CollectionConfig:
        if self._source_paths is None:
            raise ValueError("source_paths is required")
        if self._target_path is None:
            raise ValueError("target_path is required")

        return CollectionConfig(
            source_paths=self._source_paths,
            target_path=self._target_path,
            patterns=self._patterns,
            operation_mode=self._operation_mode,
            create_archive=self._create_archive,
            archive_format=self._archive_format,
            archive_compression=self._archive_compression,
            send_email=self._send_email,
            email_config=self._email_config,
            collect_system_info=self._collect_system_info,
            enable_audit_logging=self._enable_audit_logging,
            audit_log_file=self._audit_log_file,
        )
