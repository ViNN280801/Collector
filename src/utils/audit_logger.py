from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class AuditLogger:
    def __init__(self, log_file: Optional[Path] = None) -> None:
        self._logger = logging.getLogger("audit")
        self._logger.setLevel(logging.INFO)

        if log_file:
            handler = logging.FileHandler(str(log_file))
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def log_operation(
        self,
        operation: str,
        source: Path,
        target: Path,
        user: Optional[str] = None,
    ) -> None:
        timestamp = datetime.now().isoformat()
        user_info = f"user={user}" if user else "user=system"
        message = f"[{timestamp}] OPERATION: {operation} | " f"source={source} | target={target} | {user_info}"
        self._logger.info(message)

    def log_error(self, operation: str, error: Exception, context: Dict[str, Any]) -> None:
        timestamp = datetime.now().isoformat()
        message = (
            f"[{timestamp}] ERROR: {operation} | " f"error={type(error).__name__}: {error} | " f"context={context}"
        )
        self._logger.error(message)

    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        timestamp = datetime.now().isoformat()
        message = f"[{timestamp}] SECURITY: {event_type} | details={details}"
        self._logger.warning(message)
