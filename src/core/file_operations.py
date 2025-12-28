from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import shutil

from ..utils.audit_logger import AuditLogger
from ..utils.exception_wrapper import exception_wrapper
from .exceptions import FileOperationError, SecurityError
from .security_constants import MAX_PATH_LENGTH, get_dangerous_chars


class FileOperationStrategy(ABC):
    @abstractmethod
    def execute(self, source: Path, target: Path) -> None:
        pass


class CopyStrategy(FileOperationStrategy):
    @exception_wrapper()
    def execute(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


class MoveStrategy(FileOperationStrategy):
    @exception_wrapper()
    def execute(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))


class MoveRemoveStrategy(FileOperationStrategy):
    @exception_wrapper()
    def execute(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        if source.exists():
            source.unlink()


class FileOperations:
    def __init__(self, strategy: FileOperationStrategy, audit_logger: Optional[AuditLogger] = None) -> None:
        self._strategy = strategy
        self._audit_logger = audit_logger

    def set_strategy(self, strategy: FileOperationStrategy) -> None:
        self._strategy = strategy

    def set_audit_logger(self, audit_logger: Optional[AuditLogger]) -> None:
        self._audit_logger = audit_logger

    def _validate_path_security(self, path: Path) -> None:
        path_str = str(path)
        if len(path_str) > MAX_PATH_LENGTH:
            raise SecurityError(f"Path exceeds maximum length ({MAX_PATH_LENGTH}): {len(path_str)} characters")

        dangerous_chars = get_dangerous_chars()
        path_parts = path.parts
        for part in path_parts:
            for char in dangerous_chars:
                if char in part:
                    raise SecurityError(f"Dangerous character detected in path component: {repr(char)}")

    @exception_wrapper()
    def execute_operation(self, source: Path, target: Path) -> None:
        self._validate_path_security(source)
        self._validate_path_security(target)

        operation_name = type(self._strategy).__name__.replace("Strategy", "").lower()
        try:
            self._strategy.execute(source, target)
            if self._audit_logger:
                self._audit_logger.log_operation(operation=operation_name, source=source, target=target)
        except Exception as e:
            if self._audit_logger:
                self._audit_logger.log_error(
                    operation=operation_name, error=e, context={"source": str(source), "target": str(target)}
                )
            raise FileOperationError(f"Failed to execute operation: {e}") from e
