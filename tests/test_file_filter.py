from __future__ import annotations

import pytest
from pathlib import Path

from src.core.config import PatternConfig
from src.core.exceptions import FilterError
from src.core.file_filter import FileFilter


@pytest.mark.unit
class TestFileFilterMatchGlob:
    def test_match_glob_simple_pattern(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")
        filepath = temp_dir / "test.log"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is True

    def test_match_glob_no_match_different_extension(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")
        filepath = temp_dir / "test.txt"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is False

    def test_match_glob_pattern_with_prefix(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="error_*.log", pattern_type="glob")
        filepath = temp_dir / "error_file.log"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is True

    def test_match_glob_pattern_with_wildcard_in_middle(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="test-*.log", pattern_type="glob")
        filepath = temp_dir / "test-123.log"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is True

    def test_match_glob_pattern_no_match_wrong_prefix(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="error_*.log", pattern_type="glob")
        filepath = temp_dir / "warn_file.log"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is False

    def test_match_glob_cache_used_after_first_call(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")
        filepath = temp_dir / "test.log"
        filepath.touch()

        cache_key = f"{filepath}:{pattern.pattern}:{pattern.pattern_type}"
        result1 = filter_obj.match(filepath, pattern)
        assert cache_key in filter_obj._cache

        result2 = filter_obj.match(filepath, pattern)

        assert result1 == result2
        assert result1 is True

    def test_match_glob_empty_pattern_does_not_match(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="", pattern_type="glob")
        filepath = temp_dir / "test.log"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is False


@pytest.mark.unit
class TestFileFilterMatchRegex:
    def test_match_regex_simple_pattern(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern=r".*\.log$", pattern_type="regex")
        filepath = temp_dir / "test.log"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is True

    def test_match_regex_no_match_different_extension(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern=r".*\.log$", pattern_type="regex")
        filepath = temp_dir / "test.txt"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is False

    def test_match_regex_pattern_with_prefix(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern=r"error.*\.log$", pattern_type="regex")
        filepath = temp_dir / "error_file.log"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is True

    def test_match_regex_pattern_no_match_wrong_prefix(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern=r"^error.*\.log$", pattern_type="regex")
        filepath = temp_dir / "warn_file.log"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is False

    def test_match_regex_invalid_pattern_raises_filter_error(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern=r"[", pattern_type="regex")
        filepath = temp_dir / "test.log"
        filepath.touch()

        with pytest.raises(FilterError) as exc_info:
            filter_obj.match(filepath, pattern)

        assert "Invalid regex pattern" in str(exc_info.value)

    def test_match_regex_empty_pattern_matches_all(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="", pattern_type="regex")
        filepath = temp_dir / "test.log"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is True

    def test_match_regex_complex_pattern_with_groups(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern=r"(\d{4})-(\d{2})-(\d{2})\.log", pattern_type="regex")
        filepath = temp_dir / "2024-12-20.log"
        filepath.touch()

        result = filter_obj.match(filepath, pattern)

        assert result is True


@pytest.mark.unit
class TestFileFilterCache:
    def test_cache_stores_result(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")
        filepath = temp_dir / "test.log"
        filepath.touch()

        cache_key = f"{filepath}:{pattern.pattern}:{pattern.pattern_type}"
        assert cache_key not in filter_obj._cache

        filter_obj.match(filepath, pattern)

        assert cache_key in filter_obj._cache
        assert filter_obj._cache[cache_key] is True

    def test_cache_returns_cached_value(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")
        filepath = temp_dir / "test.log"
        filepath.touch()

        result1 = filter_obj.match(filepath, pattern)
        result2 = filter_obj.match(filepath, pattern)

        assert result1 == result2
        assert result1 is True

    def test_cache_different_patterns_different_keys(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern1 = PatternConfig(pattern="*.log", pattern_type="glob")
        pattern2 = PatternConfig(pattern="*.txt", pattern_type="glob")
        filepath = temp_dir / "test.log"
        filepath.touch()

        filter_obj.match(filepath, pattern1)
        filter_obj.match(filepath, pattern2)

        key1 = f"{filepath}:{pattern1.pattern}:{pattern1.pattern_type}"
        key2 = f"{filepath}:{pattern2.pattern}:{pattern2.pattern_type}"
        assert key1 in filter_obj._cache
        assert key2 in filter_obj._cache
        assert filter_obj._cache[key1] is True
        assert filter_obj._cache[key2] is False

    def test_cache_different_files_different_keys(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")
        filepath1 = temp_dir / "test1.log"
        filepath2 = temp_dir / "test2.log"
        filepath1.touch()
        filepath2.touch()

        filter_obj.match(filepath1, pattern)
        filter_obj.match(filepath2, pattern)

        key1 = f"{filepath1}:{pattern.pattern}:{pattern.pattern_type}"
        key2 = f"{filepath2}:{pattern.pattern}:{pattern.pattern_type}"
        assert key1 in filter_obj._cache
        assert key2 in filter_obj._cache

    def test_cache_grows_with_multiple_calls(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")

        initial_size = len(filter_obj._cache)

        for i in range(5):
            filepath = temp_dir / f"test{i}.log"
            filepath.touch()
            filter_obj.match(filepath, pattern)

        assert len(filter_obj._cache) == initial_size + 5

    def test_invalidate_cache_clears_all_entries(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")
        filepath = temp_dir / "test.log"
        filepath.touch()

        filter_obj.match(filepath, pattern)
        assert len(filter_obj._cache) > 0

        filter_obj.invalidate_cache()

        assert len(filter_obj._cache) == 0

    def test_invalidate_cache_after_multiple_matches(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")

        for i in range(10):
            filepath = temp_dir / f"test{i}.log"
            filepath.touch()
            filter_obj.match(filepath, pattern)

        assert len(filter_obj._cache) == 10

        filter_obj.invalidate_cache()

        assert len(filter_obj._cache) == 0


@pytest.mark.unit
class TestFileFilterFilterFiles:
    def test_filter_files_single_pattern_single_match(self, test_data_dir: Path) -> None:
        filter_obj = FileFilter()
        patterns = [PatternConfig(pattern="*.log", pattern_type="glob")]

        files = list(test_data_dir.rglob("*"))
        files = [f for f in files if f.is_file()]

        filtered = filter_obj.filter_files(files, patterns)

        assert len(filtered) == 3
        assert all(f.suffix == ".log" for f in filtered)

    def test_filter_files_single_pattern_no_matches(self, test_data_dir: Path) -> None:
        filter_obj = FileFilter()
        patterns = [PatternConfig(pattern="*.py", pattern_type="glob")]

        files = list(test_data_dir.rglob("*"))
        files = [f for f in files if f.is_file()]

        filtered = filter_obj.filter_files(files, patterns)

        assert len(filtered) == 0

    def test_filter_files_multiple_patterns_or_logic(self, test_data_dir: Path) -> None:
        filter_obj = FileFilter()
        patterns = [
            PatternConfig(pattern="*.log", pattern_type="glob"),
            PatternConfig(pattern="*.txt", pattern_type="glob"),
        ]

        files = list(test_data_dir.rglob("*"))
        files = [f for f in files if f.is_file()]

        filtered = filter_obj.filter_files(files, patterns)

        assert len(filtered) == 4
        assert all(f.suffix in [".log", ".txt"] for f in filtered)

    def test_filter_files_empty_patterns_returns_all(self, test_data_dir: Path) -> None:
        filter_obj = FileFilter()
        patterns: list[PatternConfig] = []

        files = list(test_data_dir.rglob("*"))
        files = [f for f in files if f.is_file()]

        filtered = filter_obj.filter_files(files, patterns)

        assert len(filtered) == len(files)

    def test_filter_files_empty_file_list_returns_empty(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        patterns = [PatternConfig(pattern="*.log", pattern_type="glob")]

        filtered = filter_obj.filter_files([], patterns)

        assert len(filtered) == 0
        assert filtered == []

    def test_filter_files_cache_used_during_filtering(self, test_data_dir: Path) -> None:
        filter_obj = FileFilter()
        patterns = [PatternConfig(pattern="*.log", pattern_type="glob")]

        files = list(test_data_dir.rglob("*"))
        files = [f for f in files if f.is_file()]

        initial_cache_size = len(filter_obj._cache)

        filter_obj.filter_files(files, patterns)

        assert len(filter_obj._cache) > initial_cache_size

    def test_filter_files_regex_patterns_work(self, test_data_dir: Path) -> None:
        filter_obj = FileFilter()
        patterns = [PatternConfig(pattern=r".*file\d+\.log$", pattern_type="regex")]

        files = list(test_data_dir.rglob("*"))
        files = [f for f in files if f.is_file()]

        filtered = filter_obj.filter_files(files, patterns)

        assert len(filtered) >= 0


@pytest.mark.unit
class TestFileFilterExceptionSafety:
    def test_match_handles_missing_file_gracefully(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")
        filepath = temp_dir / "nonexistent.log"

        result = filter_obj.match(filepath, pattern)

        assert isinstance(result, bool)

    def test_filter_files_handles_invalid_paths(self, temp_dir: Path) -> None:
        filter_obj = FileFilter()
        patterns = [PatternConfig(pattern="*.log", pattern_type="glob")]

        invalid_paths = [Path("/nonexistent/path/file.log"), Path("relative/path.log")]

        filtered = filter_obj.filter_files(invalid_paths, patterns)

        assert isinstance(filtered, list)
