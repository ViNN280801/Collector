from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.config import CollectionConfig, PatternConfig
from src.core.exceptions import ValidationError, PathError
from src.core.validator import validate_path, validate_disk_space, validate_config


@pytest.mark.unit
class TestValidatePath:
    def test_validate_path_existing_directory(self, temp_dir: Path) -> None:
        result = validate_path(temp_dir)

        assert result is True

    def test_validate_path_nonexistent_path_returns_false(self, temp_dir: Path) -> None:
        nonexistent = temp_dir / "nonexistent"

        result = validate_path(nonexistent)

        assert result is False

    def test_validate_path_file_exists_returns_true(self, temp_dir: Path) -> None:
        file_path = temp_dir / "test.txt"
        file_path.touch()

        result = validate_path(file_path)

        assert result is True

    def test_validate_path_empty_string_returns_false(self) -> None:
        result = validate_path(Path(""))

        assert result is False

    def test_validate_path_parent_directory_exists(self, temp_dir: Path) -> None:
        child_dir = temp_dir / "child"
        child_dir.mkdir()

        result = validate_path(child_dir)

        assert result is True

    def test_validate_path_calls_exists_method(self, temp_dir: Path) -> None:
        result = validate_path(temp_dir)

        assert result is True


@pytest.mark.unit
class TestValidateDiskSpace:
    @patch("src.core.validator.shutil.disk_usage", autospec=True)
    def test_validate_disk_space_sufficient_space(self, mock_disk_usage: MagicMock, temp_dir: Path) -> None:
        from collections import namedtuple

        DiskUsage = namedtuple("DiskUsage", "total used free")
        mock_disk_usage.return_value = DiskUsage(
            total=2000 * 1024 * 1024, used=500 * 1024 * 1024, free=1024 * 1024 * 1024
        )
        required_bytes = 100 * 1024 * 1024

        result = validate_disk_space(temp_dir, required_bytes)

        assert result is True

    @patch("src.core.validator.shutil.disk_usage", autospec=True)
    def test_validate_disk_space_insufficient_space_returns_false(
        self, mock_disk_usage: MagicMock, temp_dir: Path
    ) -> None:
        from collections import namedtuple

        DiskUsage = namedtuple("DiskUsage", "total used free")
        mock_disk_usage.return_value = DiskUsage(total=200 * 1024 * 1024, used=190 * 1024 * 1024, free=10 * 1024 * 1024)
        required_bytes = 100 * 1024 * 1024

        result = validate_disk_space(temp_dir, required_bytes)

        assert result is False

    @patch("src.core.validator.shutil.disk_usage", autospec=True)
    def test_validate_disk_space_exact_space_required(self, mock_disk_usage: MagicMock, temp_dir: Path) -> None:
        required_bytes = 1024 * 1024 * 1024
        mock_disk_usage.return_value = (10 * 1024 * 1024 * 1024, 5 * 1024 * 1024 * 1024, required_bytes)

        result = validate_disk_space(temp_dir, required_bytes)

        assert result is True

    @patch("src.core.validator.shutil.disk_usage", autospec=True)
    def test_validate_disk_space_zero_required(self, mock_disk_usage: MagicMock, temp_dir: Path) -> None:
        mock_disk_usage.return_value = (10 * 1024 * 1024 * 1024, 5 * 1024 * 1024 * 1024, 1024)

        result = validate_disk_space(temp_dir, 0)

        assert result is True

    @patch("src.core.validator.shutil.disk_usage", autospec=True)
    def test_validate_disk_space_calculates_correctly(self, mock_disk_usage: MagicMock, temp_dir: Path) -> None:
        mock_disk_usage.return_value = (10 * 1024 * 1024 * 1024, 5 * 1024 * 1024 * 1024, 1000 * 1024 * 1024)

        validate_disk_space(temp_dir, 500 * 1024 * 1024)

        mock_disk_usage.assert_called_once_with(temp_dir)

    @patch("src.core.validator.shutil.disk_usage", autospec=True)
    def test_validate_disk_space_handles_large_values(self, mock_disk_usage: MagicMock, temp_dir: Path) -> None:
        free_space = 10 * 1024 * 1024 * 1024 * 1024
        required_bytes = 5 * 1024 * 1024 * 1024 * 1024
        mock_disk_usage.return_value = (20 * 1024 * 1024 * 1024 * 1024, 10 * 1024 * 1024 * 1024 * 1024, free_space)

        result = validate_disk_space(temp_dir, required_bytes)

        assert result is True

    @patch("src.core.validator.shutil.disk_usage", autospec=True)
    def test_validate_disk_space_os_error_raises_path_error(self, mock_disk_usage: MagicMock, temp_dir: Path) -> None:
        mock_disk_usage.side_effect = OSError("Permission denied")

        with pytest.raises(PathError) as exc_info:
            validate_disk_space(temp_dir, 1000)

        assert "disk space" in str(exc_info.value).lower()


@pytest.mark.unit
class TestValidateConfig:
    def test_validate_config_valid_config(self, temp_dir: Path) -> None:
        config = CollectionConfig(
            source_paths=[temp_dir],
            target_path=temp_dir / "target",
            patterns=[PatternConfig(pattern="*.log", pattern_type="glob")],
            operation_mode="copy",
        )

        result = validate_config(config)

        assert result is True

    def test_validate_config_empty_source_paths_raises_error(self, temp_dir: Path) -> None:
        config = CollectionConfig(
            source_paths=[],
            target_path=temp_dir / "target",
            operation_mode="copy",
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_config(config)

        assert "source_paths" in str(exc_info.value).lower()

    def test_validate_config_invalid_operation_mode_raises_error(self, temp_dir: Path) -> None:
        with pytest.raises(ValueError) as exc_info:
            CollectionConfig(
                source_paths=[temp_dir],
                target_path=temp_dir / "target",
                operation_mode="invalid_mode",
            )

        assert "operation_mode" in str(exc_info.value).lower()

    def test_validate_config_invalid_pattern_type_raises_error(self, temp_dir: Path) -> None:
        with pytest.raises(ValueError) as exc_info:
            PatternConfig(pattern="*.log", pattern_type="invalid")

        assert "pattern_type" in str(exc_info.value).lower()

    def test_validate_config_validates_each_source_path(self, temp_dir: Path) -> None:
        nonexistent = temp_dir / "nonexistent"
        config = CollectionConfig(
            source_paths=[nonexistent],
            target_path=temp_dir / "target",
            operation_mode="copy",
        )

        with pytest.raises(ValidationError):
            validate_config(config)

    def test_validate_config_validates_target_path(self, temp_dir: Path) -> None:
        nonexistent_parent = temp_dir / "nonexistent" / "target"
        config = CollectionConfig(
            source_paths=[temp_dir],
            target_path=nonexistent_parent,
            operation_mode="copy",
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_config(config)

        assert "parent" in str(exc_info.value).lower() or "target" in str(exc_info.value).lower()

    @patch("src.core.validator.validate_path", autospec=True)
    def test_validate_config_calls_validate_path_for_sources(self, mock_validate: MagicMock, temp_dir: Path) -> None:
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        mock_validate.return_value = True
        config = CollectionConfig(
            source_paths=[temp_dir, subdir],
            target_path=temp_dir / "target",
            operation_mode="copy",
        )

        validate_config(config)

        assert mock_validate.call_count >= 2

    def test_validate_config_multiple_valid_patterns(self, temp_dir: Path) -> None:
        config = CollectionConfig(
            source_paths=[temp_dir],
            target_path=temp_dir / "target",
            patterns=[
                PatternConfig(pattern="*.log", pattern_type="glob"),
                PatternConfig(pattern=r".*\.txt$", pattern_type="regex"),
            ],
            operation_mode="copy",
        )

        result = validate_config(config)

        assert result is True

    def test_validate_config_empty_patterns_allowed(self, temp_dir: Path) -> None:
        config = CollectionConfig(
            source_paths=[temp_dir],
            target_path=temp_dir / "target",
            patterns=[],
            operation_mode="copy",
        )

        result = validate_config(config)

        assert result is True
