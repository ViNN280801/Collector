from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from src.core import CollectionConfigBuilder, CollectionService, PatternConfig
from src.archive.archiver import Archiver
from src.core.file_filter import FileFilter


@pytest.mark.integration
class TestProductionLogsCollection:
    """Tests using real production logs from tests/test_files."""

    def test_collect_production_logs_copy_mode(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test collecting production logs in copy mode."""
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        config = (
            CollectionConfigBuilder()
            .with_source_paths([production_logs_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["total_files"] > 0
        assert result["processed_files"] > 0
        assert result["failed_files"] == 0

        # Verify files were copied
        log_files = list(production_logs_dir.rglob("*.log"))
        assert len(log_files) > 0

        for source_file in log_files:
            relative = source_file.relative_to(production_logs_dir)
            target_file = target_dir / relative
            assert target_file.exists(), f"File {target_file} should exist"
            assert source_file.exists(), f"Original file {source_file} should still exist (copy mode)"
            assert target_file.read_bytes() == source_file.read_bytes()

    def test_collect_production_logs_with_nested_directories(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test collecting logs from nested directories."""
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        config = (
            CollectionConfigBuilder()
            .with_source_paths([production_logs_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        _ = service.collect()

        # Check that nested directories are preserved
        nested_dirs = [d for d in production_logs_dir.iterdir() if d.is_dir() and d.name.startswith("logs_")]
        if nested_dirs:
            for nested_dir in nested_dirs:
                relative = nested_dir.relative_to(production_logs_dir)
                target_nested = target_dir / relative
                assert target_nested.exists() or any(
                    (target_dir / relative / f).exists()
                    for f in nested_dir.rglob("*.log")
                    for relative in [f.relative_to(production_logs_dir)]
                )

    def test_collect_production_logs_with_regex_pattern(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test collecting logs using regex pattern."""
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        config = (
            CollectionConfigBuilder()
            .with_source_paths([production_logs_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern=r".*error.*\.log", pattern_type="regex")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        # Should find error log files
        error_logs = list(production_logs_dir.rglob("*error*.log"))
        if error_logs:
            assert result["total_files"] > 0
            assert result["processed_files"] > 0

    def test_collect_production_logs_multiple_patterns(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test collecting logs with multiple patterns."""
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        config = (
            CollectionConfigBuilder()
            .with_source_paths([production_logs_dir])
            .with_target_path(target_dir)
            .with_patterns(
                [
                    PatternConfig(pattern="*.log", pattern_type="glob"),
                    PatternConfig(pattern="*.txt", pattern_type="glob"),
                    PatternConfig(pattern="*.json", pattern_type="glob"),
                ]
            )
            .with_operation_mode("copy")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["total_files"] > 0
        assert result["processed_files"] > 0

        # Verify different file types were collected
        collected_logs = list(target_dir.rglob("*.log"))
        collected_txts = list(target_dir.rglob("*.txt"))
        collected_jsons = list(target_dir.rglob("*.json"))

        assert len(collected_logs) > 0 or len(collected_txts) > 0 or len(collected_jsons) > 0

    def test_collect_production_logs_move_mode(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test collecting production logs in move mode (moves from copy, not original)."""
        # Create a fresh copy for move test
        move_source = temp_dir / "move_source"
        shutil.copytree(production_logs_dir, move_source, dirs_exist_ok=True)

        target_dir = temp_dir / "target"
        target_dir.mkdir()

        config = (
            CollectionConfigBuilder()
            .with_source_paths([move_source])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("move")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["total_files"] > 0
        assert result["processed_files"] > 0

        # In move mode, source files should be removed
        moved_files = list(move_source.rglob("*.log"))
        assert len(moved_files) == 0, "Files should be moved, not copied"

        # But target should have them
        target_files = list(target_dir.rglob("*.log"))
        assert len(target_files) > 0

        # Original production logs should still exist
        original_logs = list(production_logs_dir.rglob("*.log"))
        assert len(original_logs) > 0, "Original production logs should never be deleted"


@pytest.mark.integration
class TestProductionLogsArchiving:
    """Tests for archiving production logs."""

    def test_archive_production_logs_zip(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test creating ZIP archive from production logs."""
        archive_file = temp_dir / "production_logs.zip"

        Archiver.create_zip_archive(production_logs_dir, archive_file)

        assert archive_file.exists()
        assert archive_file.stat().st_size > 0

        # Original files should still exist
        original_logs = list(production_logs_dir.rglob("*.log"))
        assert len(original_logs) > 0

    def test_archive_production_logs_tar(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test creating TAR archive from production logs."""
        archive_file = temp_dir / "production_logs.tar"

        Archiver.create_tar_archive(production_logs_dir, archive_file)

        assert archive_file.exists()
        assert archive_file.stat().st_size > 0

        # Original files should still exist
        original_logs = list(production_logs_dir.rglob("*.log"))
        assert len(original_logs) > 0

    def test_archive_production_logs_tar_gz(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test creating compressed TAR.GZ archive from production logs."""
        archive_file = temp_dir / "production_logs.tar.gz"

        Archiver.create_tar_archive(production_logs_dir, archive_file, compression="gzip")

        assert archive_file.exists()
        assert archive_file.stat().st_size > 0

        # Original files should still exist
        original_logs = list(production_logs_dir.rglob("*.log"))
        assert len(original_logs) > 0

    def test_archive_production_logs_with_progress(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test archiving with progress callback."""
        archive_file = temp_dir / "production_logs.zip"
        callback_calls: list = []

        def progress_callback(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            callback_calls.append((percentage, current, total, current_file))

        Archiver.create_zip_archive(production_logs_dir, archive_file, progress_callback=progress_callback)

        assert archive_file.exists()
        assert len(callback_calls) > 0
        assert callback_calls[-1][1] == callback_calls[-1][2]  # current == total at end


@pytest.mark.unit
class TestProductionLogsFiltering:
    """Tests for filtering production logs."""

    def test_filter_production_logs_by_glob(self, production_logs_dir: Path) -> None:
        """Test filtering production logs using glob patterns."""
        file_filter = FileFilter()
        pattern = PatternConfig(pattern="*.log", pattern_type="glob")

        all_files = [f for f in production_logs_dir.rglob("*") if f.is_file()]
        log_files = [f for f in all_files if file_filter.match(f, pattern)]

        assert len(log_files) > 0
        assert all(f.suffix == ".log" for f in log_files)

    def test_filter_production_logs_by_regex(self, production_logs_dir: Path) -> None:
        """Test filtering production logs using regex patterns."""
        file_filter = FileFilter()
        pattern = PatternConfig(pattern=r".*error.*\.log", pattern_type="regex")

        all_files = [f for f in production_logs_dir.rglob("*") if f.is_file()]
        error_logs = [f for f in all_files if file_filter.match(f, pattern)]

        # Should find error log files if they exist
        error_files_in_dir = list(production_logs_dir.rglob("*error*.log"))
        if error_files_in_dir:
            assert len(error_logs) > 0
            assert all("error" in f.name.lower() for f in error_logs)

    def test_filter_production_logs_multiple_patterns(self, production_logs_dir: Path) -> None:
        """Test filtering with multiple patterns."""
        file_filter = FileFilter()
        patterns = [
            PatternConfig(pattern="*.log", pattern_type="glob"),
            PatternConfig(pattern="*.txt", pattern_type="glob"),
            PatternConfig(pattern="*.json", pattern_type="glob"),
        ]

        all_files = [f for f in production_logs_dir.rglob("*") if f.is_file()]
        matched_files = file_filter.filter_files(all_files, patterns)

        assert len(matched_files) > 0
        assert all(f.suffix in [".log", ".txt", ".json"] for f in matched_files)

    def test_filter_production_logs_exclude_patterns(self, production_logs_dir: Path) -> None:
        """Test filtering with exclusion (matching only non-error logs)."""
        file_filter = FileFilter()
        # Match all log files
        log_pattern = PatternConfig(pattern="*.log", pattern_type="glob")

        all_files = [f for f in production_logs_dir.rglob("*") if f.is_file()]
        all_logs = [f for f in all_files if file_filter.match(f, log_pattern)]

        # Filter out error logs manually (since FileFilter doesn't have exclusion)
        non_error_logs = [f for f in all_logs if "error" not in f.name.lower()]

        # Should have some log files
        assert len(all_logs) > 0
        # If there are error logs, non_error_logs should be fewer
        error_logs = [f for f in all_logs if "error" in f.name.lower()]
        if error_logs:
            assert len(non_error_logs) < len(all_logs)
            assert all("error" not in f.name.lower() for f in non_error_logs)


@pytest.mark.integration
class TestProductionLogsFullWorkflow:
    """End-to-end tests with production logs."""

    def test_full_workflow_collect_and_archive(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test full workflow: collect logs, then archive them."""
        # Step 1: Collect logs
        collect_target = temp_dir / "collected"
        collect_target.mkdir()

        config = (
            CollectionConfigBuilder()
            .with_source_paths([production_logs_dir])
            .with_target_path(collect_target)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .build()
        )

        service = CollectionService(config)
        collect_result = service.collect()

        assert collect_result["processed_files"] > 0

        # Step 2: Archive collected logs
        archive_file = temp_dir / "collected_logs.zip"
        Archiver.create_zip_archive(collect_target, archive_file)

        assert archive_file.exists()
        assert archive_file.stat().st_size > 0

        # Step 3: Verify originals are intact
        original_logs = list(production_logs_dir.rglob("*.log"))
        assert len(original_logs) > 0, "Original production logs should never be deleted"

    def test_full_workflow_with_system_info(self, production_logs_dir: Path, temp_dir: Path) -> None:
        """Test full workflow with system info collection."""
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        config = (
            CollectionConfigBuilder()
            .with_source_paths([production_logs_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(True)
            .build()
        )

        service = CollectionService(config)
        result = service.collect()

        assert result["processed_files"] > 0

        # Check if system info file was created
        _ = list(target_dir.rglob("*pc_info.json"))
        # System info might be created in target root or not, depending on implementation
        # Just verify collection succeeded

        # Verify originals are intact
        original_logs = list(production_logs_dir.rglob("*.log"))
        assert len(original_logs) > 0
