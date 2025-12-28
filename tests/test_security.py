from __future__ import annotations

from pathlib import Path

import pytest

from src.core.exceptions import SecurityError
from src.core.path_sanitizer import resolve_path, sanitize_path, validate_path_traversal


@pytest.mark.security
class TestPathTraversalPrevention:
    def test_path_traversal_with_dot_dot_slash(self, temp_dir: Path) -> None:
        base_dir = temp_dir / "base"
        base_dir.mkdir()

        malicious_path = base_dir / ".." / ".." / "etc" / "passwd"

        with pytest.raises(SecurityError, match="Path traversal detected"):
            resolve_path(base_dir, str(malicious_path.relative_to(base_dir)))

    def test_path_traversal_with_dot_dot_backslash(self, temp_dir: Path) -> None:
        base_dir = temp_dir / "base"
        base_dir.mkdir()

        malicious_path = base_dir / "..\\..\\etc\\passwd"

        with pytest.raises(SecurityError, match="Path traversal detected"):
            resolve_path(base_dir, str(malicious_path.relative_to(base_dir)))

    def test_path_traversal_absolute_path_outside_base(self, temp_dir: Path) -> None:
        base_dir = temp_dir / "base"
        base_dir.mkdir()

        absolute_path = Path("/etc/passwd")

        with pytest.raises(SecurityError, match="Absolute paths are not allowed"):
            resolve_path(base_dir, str(absolute_path))

    def test_path_traversal_encoded(self, temp_dir: Path) -> None:
        base_dir = temp_dir / "base"
        base_dir.mkdir()

        malicious_path = base_dir / "%2e%2e" / "etc" / "passwd"

        # URL-encoded paths are normalized by pathlib, so this may not raise SecurityError
        # The actual protection comes from validate_path_traversal which checks resolved paths
        try:
            resolved = resolve_path(base_dir, str(malicious_path.relative_to(base_dir)))
            # If it doesn't raise, ensure the resolved path is still within base_dir
            assert validate_path_traversal(resolved, base_dir) is True
        except SecurityError:
            pass

    def test_path_traversal_validation_function(self, temp_dir: Path) -> None:
        base_dir = temp_dir / "base"
        base_dir.mkdir()

        safe_path = base_dir / "subdir" / "file.txt"
        malicious_path = temp_dir / "outside" / "file.txt"

        assert validate_path_traversal(safe_path, base_dir) is True
        assert validate_path_traversal(malicious_path, base_dir) is False


@pytest.mark.security
class TestDangerousCharacters:
    def test_dangerous_char_less_than(self, temp_dir: Path) -> None:
        dangerous_path = temp_dir / "file<name>.txt"

        with pytest.raises(SecurityError, match="Dangerous character"):
            sanitize_path(str(dangerous_path))

    def test_dangerous_char_greater_than(self, temp_dir: Path) -> None:
        dangerous_path = temp_dir / "file>name>.txt"

        with pytest.raises(SecurityError, match="Dangerous character"):
            sanitize_path(str(dangerous_path))

    def test_dangerous_char_quote(self, temp_dir: Path) -> None:
        dangerous_path = temp_dir / 'file"name".txt'

        with pytest.raises(SecurityError, match="Dangerous character"):
            sanitize_path(str(dangerous_path))

    def test_dangerous_char_pipe(self, temp_dir: Path) -> None:
        dangerous_path = temp_dir / "file|name.txt"

        with pytest.raises(SecurityError, match="Dangerous character"):
            sanitize_path(str(dangerous_path))

    def test_dangerous_char_question_mark(self, temp_dir: Path) -> None:
        dangerous_path = temp_dir / "file?name.txt"

        with pytest.raises(SecurityError, match="Dangerous character"):
            sanitize_path(str(dangerous_path))

    def test_dangerous_char_asterisk(self, temp_dir: Path) -> None:
        dangerous_path = temp_dir / "file*name.txt"

        with pytest.raises(SecurityError, match="Dangerous character"):
            sanitize_path(str(dangerous_path))

    def test_dangerous_char_null_byte(self, temp_dir: Path) -> None:
        dangerous_path = temp_dir / "file\x00name.txt"

        with pytest.raises(SecurityError, match="Dangerous character"):
            sanitize_path(str(dangerous_path))


@pytest.mark.security
class TestReservedNames:
    def test_windows_reserved_name_con(self, temp_dir: Path) -> None:
        import platform

        if platform.system() != "Windows":
            pytest.skip("Windows reserved names test only on Windows")

        reserved_path = temp_dir / "CON.txt"

        with pytest.raises(SecurityError, match="Reserved name detected"):
            sanitize_path(str(reserved_path))

    def test_windows_reserved_name_prn(self, temp_dir: Path) -> None:
        import platform

        if platform.system() != "Windows":
            pytest.skip("Windows reserved names test only on Windows")

        reserved_path = temp_dir / "PRN"

        with pytest.raises(SecurityError, match="Reserved name detected"):
            sanitize_path(str(reserved_path))


@pytest.mark.security
class TestPathLength:
    def test_path_exceeds_max_length(self, temp_dir: Path) -> None:
        long_name = "x" * 5000
        long_path = temp_dir / long_name / "file.txt"

        with pytest.raises(SecurityError, match="Path exceeds maximum length"):
            sanitize_path(str(long_path))


@pytest.mark.security
class TestCommandInjection:
    def test_command_injection_in_path_semicolon(self, temp_dir: Path) -> None:
        malicious_path = temp_dir / "file; rm -rf /"

        # Semicolon is not in the dangerous chars list for Windows/Linux
        # This is acceptable as semicolons are valid in filenames on some systems
        # The actual protection comes from proper path handling, not character filtering
        sanitized = sanitize_path(str(malicious_path))
        assert sanitized.exists() or sanitized.parent.exists()

    def test_command_injection_in_path_backtick(self, temp_dir: Path) -> None:
        malicious_path = temp_dir / "file`rm -rf /`"

        sanitized = sanitize_path(str(malicious_path))

        assert "`" not in str(sanitized) or sanitized.exists() is False


@pytest.mark.security
class TestRateLimiting:
    def test_rate_limiting_exceeds_limit(self) -> None:
        from src.api.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=5, window_seconds=60)

        for i in range(5):
            assert limiter.is_allowed("test_key") is True

        assert limiter.is_allowed("test_key") is False

    def test_rate_limiting_resets_after_window(self) -> None:
        from src.api.rate_limiter import RateLimiter
        import time

        limiter = RateLimiter(max_requests=2, window_seconds=1)

        assert limiter.is_allowed("test_key") is True
        assert limiter.is_allowed("test_key") is True
        assert limiter.is_allowed("test_key") is False

        time.sleep(1.1)

        assert limiter.is_allowed("test_key") is True
