from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core import CollectionConfigBuilder, CollectionService, PatternConfig
from src.core.exceptions import ValidationError


@pytest.mark.integration
class TestCollectionServiceFullCycle:
    def test_collect_files_copy_mode(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        for i in range(5):
            (source_dir / f"file{i}.log").write_text(f"content {i}")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["total_files"] == 5
        assert result["processed_files"] == 5
        assert result["failed_files"] == 0

        for i in range(5):
            target_file = target_dir / f"file{i}.log"
            source_file = source_dir / f"file{i}.log"
            assert target_file.exists()
            assert target_file.read_text() == f"content {i}"
            assert source_file.exists()

    def test_collect_files_move_mode(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        for i in range(3):
            (source_dir / f"file{i}.txt").write_text(f"content {i}")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.txt", pattern_type="glob")])
            .with_operation_mode("move")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["total_files"] == 3
        assert result["processed_files"] == 3

        for i in range(3):
            target_file = target_dir / f"file{i}.txt"
            source_file = source_dir / f"file{i}.txt"
            assert target_file.exists()
            assert not source_file.exists()

    def test_collect_files_with_regex_pattern(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / "error.log").write_text("error")
        (source_dir / "warn.log").write_text("warn")
        (source_dir / "info.txt").write_text("info")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="error.*\\.log$", pattern_type="regex")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["total_files"] == 1
        assert (target_dir / "error.log").exists()
        assert not (target_dir / "warn.log").exists()
        assert not (target_dir / "info.txt").exists()

    def test_collect_files_empty_result(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / "file.txt").write_text("content")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["total_files"] == 0
        assert result["processed_files"] == 0
        assert result["failed_files"] == 0

    def test_collect_files_progress_tracking(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        for i in range(10):
            (source_dir / f"file{i}.log").write_text(f"content {i}")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        tracker = service.get_progress_tracker()
        callback_calls: list = []

        def progress_callback(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            callback_calls.append((percentage, current, total, current_file))

        tracker.subscribe(progress_callback)
        result = service.collect()

        assert result["processed_files"] == 10
        assert len(callback_calls) >= 10
        assert callback_calls[-1][1] == 10
        assert callback_calls[-1][2] == 10


@pytest.mark.integration
class TestCollectionServicePCInfoCollector:
    def test_collect_with_system_info(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / "file.log").write_text("content")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(True)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["pc_info_collected"] is True
        assert "pc_info_path" in result
        pc_info_path = Path(result["pc_info_path"])
        assert pc_info_path.exists()
        assert pc_info_path.name == "pc_info.json"

    def test_collect_without_system_info(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / "file.log").write_text("content")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert "pc_info_collected" not in result
        assert not (target_dir / "pc_info.json").exists()

    def test_collect_system_info_handles_errors(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / "file.log").write_text("content")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(True)
            .build()
        )

        with patch("src.core.collection_service.PCInfoCollector", autospec=True) as mock_collector:
            mock_instance = MagicMock(spec=["collect_all"])
            mock_instance.collect_all.side_effect = Exception("PC info error")
            mock_collector.return_value = mock_instance

            service = CollectionService(config)
            result = service.collect()

            assert result["pc_info_collected"] is False


@pytest.mark.integration
class TestCollectionServiceValidation:
    def test_collect_invalid_source_path(self, temp_dir: Path) -> None:
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        nonexistent = temp_dir / "nonexistent"

        with pytest.raises(ValidationError, match="Source path does not exist"):
            config = CollectionConfigBuilder().with_source_paths([nonexistent]).with_target_path(target_dir).build()

            service = CollectionService(config)
            service.collect()

    def test_collect_with_archive_zip(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        for i in range(3):
            (source_dir / f"file{i}.log").write_text(f"content {i}")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .with_archive(True, format="zip")
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["archive_created"] is True
        assert "archive_path" in result
        archive_path = Path(result["archive_path"])
        assert archive_path.exists()
        assert archive_path.suffix == ".zip"

    def test_collect_with_archive_tar_gzip(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        for i in range(3):
            (source_dir / f"file{i}.log").write_text(f"content {i}")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .with_archive(True, format="tar", compression="gzip")
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["archive_created"] is True
        assert "archive_path" in result
        archive_path = Path(result["archive_path"])
        assert archive_path.exists()
        assert archive_path.suffixes == [".tar", ".gz"]

    def test_collect_invalid_target_path(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        target_parent = temp_dir / "nonexistent" / "target"

        with pytest.raises(ValidationError, match="Target path parent does not exist"):
            config = CollectionConfigBuilder().with_source_paths([source_dir]).with_target_path(target_parent).build()

            service = CollectionService(config)
            service.collect()

    def test_collect_with_audit_logging_disabled(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / "file.log").write_text("content")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .with_audit_logging(False)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["processed_files"] == 1
        assert service._file_operations._audit_logger is None

    def test_collect_with_audit_logging_enabled(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        audit_log = temp_dir / "audit.log"
        source_dir.mkdir()
        target_dir.mkdir()

        (source_dir / "file.log").write_text("content")

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .with_audit_logging(True, log_file=audit_log)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["processed_files"] == 1
        assert service._file_operations._audit_logger is not None
        assert audit_log.exists()
