from __future__ import annotations

import re
import fnmatch
from pathlib import Path
from typing import Dict, List

from ..utils.exception_wrapper import exception_wrapper
from .config import PatternConfig
from .exceptions import FilterError


class FileFilter:
    def __init__(self) -> None:
        self._cache: Dict[str, bool] = {}

    def _match_regex(self, pattern: str, filepath: Path) -> bool:
        try:
            compiled = re.compile(pattern)
            return bool(compiled.search(str(filepath)))
        except re.error as e:
            raise FilterError(f"Invalid regex pattern: '{pattern}'. Error: {e}") from e

    def _match_glob(self, pattern: str, filepath: Path) -> bool:
        return fnmatch.fnmatch(filepath.name, pattern)

    @exception_wrapper()
    def match(self, filepath: Path, pattern_config: PatternConfig) -> bool:
        cache_key = f"{filepath}:{pattern_config.pattern}:{pattern_config.pattern_type}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        if pattern_config.pattern_type == "regex":
            result = self._match_regex(pattern_config.pattern, filepath)
        else:
            result = self._match_glob(pattern_config.pattern, filepath)

        self._cache[cache_key] = result
        return result

    @exception_wrapper()
    def filter_files(self, filepaths: List[Path], patterns: List[PatternConfig]) -> List[Path]:
        if not patterns:
            return filepaths

        filtered = []
        for filepath in filepaths:
            for pattern_config in patterns:
                if self.match(filepath, pattern_config):
                    filtered.append(filepath)
                    break

        return filtered

    def invalidate_cache(self) -> None:
        self._cache.clear()
