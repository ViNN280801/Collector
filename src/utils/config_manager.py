from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.exceptions import CollectorException


class ConfigManagerError(CollectorException):
    pass


class ConfigManager:
    def __init__(self, config_dir: Optional[Path] = None) -> None:
        if config_dir is None:
            config_dir = Path.home() / ".collector" / "configs"
        self._config_dir = Path(config_dir)
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def save_config(self, name: str, config: Dict[str, Any]) -> None:
        if not name or not name.strip():
            raise ConfigManagerError("Config name cannot be empty")

        sanitized_name = self._sanitize_name(name)
        config_file = self._config_dir / f"{sanitized_name}.json"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)
        except IOError as e:
            raise ConfigManagerError(f"Failed to save config: {e}") from e

    def load_config(self, name: str) -> Optional[Dict[str, Any]]:
        sanitized_name = self._sanitize_name(name)
        config_file = self._config_dir / f"{sanitized_name}.json"

        if not config_file.exists():
            return None

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data: Optional[Dict[str, Any]] = json.load(f)
                return data
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigManagerError(f"Failed to load config: {e}") from e

    def list_configs(self) -> List[str]:
        configs: List[str] = []
        for config_file in self._config_dir.glob("*.json"):
            name = config_file.stem
            configs.append(name)
        return sorted(configs)

    def delete_config(self, name: str) -> None:
        sanitized_name = self._sanitize_name(name)
        config_file = self._config_dir / f"{sanitized_name}.json"

        if not config_file.exists():
            raise ConfigManagerError(f"Config '{name}' does not exist")

        try:
            config_file.unlink()
        except IOError as e:
            raise ConfigManagerError(f"Failed to delete config: {e}") from e

    def _sanitize_name(self, name: str) -> str:
        sanitized = "".join(c for c in name if c.isalnum() or c in ("_", "-", " "))
        sanitized = sanitized.replace(" ", "_")
        if not sanitized:
            sanitized = "config"
        return sanitized[:100]
