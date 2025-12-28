from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.exceptions import CollectorException


class HistoryError(CollectorException):
    pass


class CollectionHistory:
    def __init__(self, history_file: Optional[Path] = None) -> None:
        if history_file is None:
            history_file = Path.home() / ".collector" / "history.json"
        self._history_file = Path(history_file)
        self._history_file.parent.mkdir(parents=True, exist_ok=True)
        self._history: List[Dict[str, Any]] = []
        self._load_history()

    def _load_history(self) -> None:
        if self._history_file.exists():
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    self._history = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                raise HistoryError(f"Failed to load history: {e}") from e
        else:
            self._history = []

    def _save_history(self) -> None:
        try:
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False, default=str)
        except IOError as e:
            raise HistoryError(f"Failed to save history: {e}") from e

    def add_entry(
        self,
        source_paths: List[str],
        target_path: str,
        results: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "source_paths": source_paths,
            "target_path": target_path,
            "results": results,
            "config": config or {},
        }
        self._history.append(entry)
        self._save_history()

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        history = self._history.copy()
        history.reverse()
        if limit:
            return history[:limit]
        return history

    def clear_history(self) -> None:
        self._history = []
        self._save_history()

    def get_entry(self, index: int) -> Optional[Dict[str, Any]]:
        if 0 <= index < len(self._history):
            return self._history[-(index + 1)]
        return None
