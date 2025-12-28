from __future__ import annotations

import pytest
from pathlib import Path

from src.core.exceptions import SecurityError
from src.core.path_sanitizer import sanitize_path, validate_path_traversal, resolve_path


@pytest.mark.unit
@pytest.mark.security
class TestSanitizePath:
    def test_sanitize_path_normal_path(self, temp_dir: Path) -> None:
        path = temp_dir / "subdir" / "file.txt"

        result = sanitize_path(str(path))

        assert result.resolve() == path.resolve()

    def test_sanitize_path_removes_dots(self, temp_dir: Path) -> None:
        path = temp_dir / "subdir" / "." / "file.txt"

        result = sanitize_path(str(path))

        assert ".." not in str(result)
        assert "." not in str(result).split("/")[-2:]

    def test_sanitize_path_resolves_absolute_path(self, temp_dir: Path) -> None:
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        path = subdir / "file.txt"

        result = sanitize_path(str(path.resolve()))

        assert result == path.resolve()

    def test_sanitize_path_handles_windows_paths(self, temp_dir: Path) -> None:
        path = temp_dir / "subdir" / "file.txt"

        windows_path = str(path).replace("/", "\\")
        result = sanitize_path(windows_path)

        assert result is not None

    def test_sanitize_path_handles_mixed_separators(self, temp_dir: Path) -> None:
        mixed_path = str(temp_dir).replace("\\", "/") + "\\subdir/file.txt"

        result = sanitize_path(mixed_path)

        assert result is not None

    def test_sanitize_path_handles_unicode_characters(self, temp_dir: Path) -> None:
        unicode_path = temp_dir / "тест" / "файл.txt"

        result = sanitize_path(str(unicode_path))

        assert result.resolve() == unicode_path.resolve()

    def test_sanitize_path_handles_empty_string(self, temp_dir: Path) -> None:
        result = sanitize_path("")

        assert result is not None


@pytest.mark.unit
@pytest.mark.security
class TestValidatePathTraversal:
    def test_validate_path_traversal_normal_path_passes(self, temp_dir: Path) -> None:
        base = temp_dir
        path = temp_dir / "subdir" / "file.txt"

        result = validate_path_traversal(path, base)

        assert result is True

    def test_validate_path_traversal_double_dot_returns_false(self, temp_dir: Path) -> None:
        base = temp_dir
        malicious = base.resolve().parent / "etc" / "passwd"

        result = validate_path_traversal(malicious, base)

        assert result is False

    def test_validate_path_traversal_windows_double_backslash_returns_false(self, temp_dir: Path) -> None:
        base = temp_dir
        malicious = base.resolve().parent / "windows" / "system32"

        result = validate_path_traversal(malicious, base)

        assert result is False

    def test_validate_path_traversal_encoded_dots_returns_false(self, temp_dir: Path) -> None:
        base = temp_dir
        malicious = base.resolve().parent / "secret"

        result = validate_path_traversal(malicious, base)

        assert result is False

    def test_validate_path_traversal_nested_dots_returns_false(self, temp_dir: Path) -> None:
        base = temp_dir
        malicious = temp_dir / "subdir" / ".." / ".." / "root"

        result = validate_path_traversal(malicious, base)

        assert result is False

    def test_validate_path_traversal_allows_subdirectories(self, temp_dir: Path) -> None:
        base = temp_dir
        subdir = temp_dir / "subdir" / "nested" / "deep"
        subdir.mkdir(parents=True, exist_ok=True)

        validate_path_traversal(subdir, base)

    def test_validate_path_traversal_same_path_allowed(self, temp_dir: Path) -> None:
        base = temp_dir

        validate_path_traversal(base, base)

    @pytest.mark.parametrize(
        "malicious_part",
        ["..", "..\\", "../"],
    )
    def test_validate_path_traversal_various_encodings_return_false(self, temp_dir: Path, malicious_part: str) -> None:
        base = temp_dir
        malicious = base.resolve().parent / "secret"

        result = validate_path_traversal(malicious, base)

        assert result is False


@pytest.mark.unit
@pytest.mark.security
class TestResolvePath:
    def test_resolve_path_normal_resolution(self, temp_dir: Path) -> None:
        base = temp_dir
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        relative = "subdir/file.txt"

        result = resolve_path(base, relative)

        assert result == (base / relative).resolve()

    def test_resolve_path_raises_error_on_traversal_attempt(self, temp_dir: Path) -> None:
        base = temp_dir
        malicious = "../etc/passwd"

        with pytest.raises(SecurityError) as exc_info:
            resolve_path(base, malicious)

        assert "path traversal" in str(exc_info.value).lower() or "security" in str(exc_info.value).lower()

    def test_resolve_path_creates_missing_base_directory(self, temp_dir: Path) -> None:
        base = temp_dir / "new_base"
        relative = "file.txt"

        result = resolve_path(base, relative)

        assert result is not None

    def test_resolve_path_handles_absolute_paths(self, temp_dir: Path) -> None:
        base = temp_dir
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        relative = "subdir/file.txt"

        result = resolve_path(base, relative)

        assert result == (base / relative).resolve()

    def test_resolve_path_handles_relative_paths(self, temp_dir: Path) -> None:
        base = temp_dir
        relative_path = "subdir/file.txt"

        result = resolve_path(base, relative_path)

        assert result is not None
        # is_relative_to is available in Python 3.9+, use try/except for compatibility
        try:
            # Python 3.9+
            is_relative = result.resolve().is_relative_to(base.resolve())
            assert is_relative
        except AttributeError:
            # Python 3.7-3.8 fallback
            import os

            result_str = str(result.resolve())
            base_str = str(base.resolve())
            try:
                common = os.path.commonpath([result_str, base_str])
                assert os.path.commonpath([common, base_str]) == base_str
            except ValueError:
                # Paths don't share common path, so not relative
                assert False, f"{result_str} is not relative to {base_str}"

    def test_resolve_path_normalizes_path_separators(self, temp_dir: Path) -> None:
        base = temp_dir
        relative = "subdir/file.txt"

        result = resolve_path(base, relative)

        assert result is not None

    def test_resolve_path_preserves_file_extension(self, temp_dir: Path) -> None:
        base = temp_dir
        relative = "file.log"

        result = resolve_path(base, relative)

        assert result.suffix == ".log"

    def test_resolve_path_handles_empty_path_string(self, temp_dir: Path) -> None:
        base = temp_dir

        result = resolve_path(base, "")

        assert result == base.resolve()
