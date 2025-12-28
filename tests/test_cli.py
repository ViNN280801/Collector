from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.cli.main import create_argument_parser, format_results, main, progress_callback_cli


@pytest.mark.integration
class TestCLIArgumentParser:
    def test_parse_source_paths(self) -> None:
        parser = create_argument_parser()
        args = parser.parse_args(["--source-paths", "/path1", "/path2", "--target-path", "/target"])

        assert args.source_paths == ["/path1", "/path2"]
        assert args.target_path == "/target"

    def test_parse_patterns(self) -> None:
        parser = create_argument_parser()
        args = parser.parse_args(
            ["--source-paths", "/source", "--target-path", "/target", "--patterns", "*.log", "*.txt"]
        )

        assert args.patterns == ["*.log", "*.txt"]
        assert args.pattern_type == "glob"

    def test_parse_pattern_type_regex(self) -> None:
        parser = create_argument_parser()
        args = parser.parse_args(["--source-paths", "/source", "--target-path", "/target", "--pattern-type", "regex"])

        assert args.pattern_type == "regex"

    def test_parse_operation_mode(self) -> None:
        parser = create_argument_parser()
        args = parser.parse_args(["--source-paths", "/source", "--target-path", "/target", "--operation-mode", "move"])

        assert args.operation_mode == "move"

    def test_parse_create_archive(self) -> None:
        parser = create_argument_parser()
        args = parser.parse_args(["--source-paths", "/source", "--target-path", "/target", "--create-archive"])

        assert args.create_archive is True

    def test_parse_collect_system_info_default(self) -> None:
        parser = create_argument_parser()
        args = parser.parse_args(["--source-paths", "/source", "--target-path", "/target"])

        assert args.collect_system_info is True

    def test_parse_no_collect_system_info(self) -> None:
        parser = create_argument_parser()
        args = parser.parse_args(["--source-paths", "/source", "--target-path", "/target", "--no-collect-system-info"])

        assert args.collect_system_info is False

    def test_parse_locale(self) -> None:
        parser = create_argument_parser()
        args = parser.parse_args(["--source-paths", "/source", "--target-path", "/target", "--locale", "ru"])

        assert args.locale == "ru"

    def test_parse_missing_required_args(self) -> None:
        parser = create_argument_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--target-path", "/target"])


@pytest.mark.integration
class TestCLIExecution:
    def test_cli_execution_success(self, temp_dir: Path, capsys) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        for i in range(3):
            (source_dir / f"file{i}.log").write_text(f"content {i}")

        test_args = [
            "log-collector-cli",
            "--source-paths",
            str(source_dir),
            "--target-path",
            str(target_dir),
            "--patterns",
            "*.log",
            "--operation-mode",
            "copy",
            "--no-collect-system-info",
        ]

        with patch.object(sys, "argv", test_args):
            exit_code = main()

        assert exit_code == 0

        for i in range(3):
            target_file = target_dir / f"file{i}.log"
            assert target_file.exists()
            assert target_file.read_text() == f"content {i}"

    def test_cli_execution_validation_error(self, temp_dir: Path) -> None:
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        nonexistent = temp_dir / "nonexistent"

        test_args = [
            "log-collector-cli",
            "--source-paths",
            str(nonexistent),
            "--target-path",
            str(target_dir),
            "--no-collect-system-info",
        ]

        with patch.object(sys, "argv", test_args):
            exit_code = main()

        assert exit_code == 1

    def test_cli_progress_callback(self, capsys) -> None:
        progress_callback_cli(50.0, 5, 10, "/path/to/file.log")

        captured = capsys.readouterr()
        assert "Progress: 50.0%" in captured.out
        assert "5/10" in captured.out
        assert "Current file: /path/to/file.log" in captured.out

    def test_cli_format_results(self) -> None:
        results = {
            "total_files": 10,
            "processed_files": 8,
            "failed_files": 2,
            "target_path": "/tmp/target",
        }

        output = format_results(results)

        assert "Total files: 10" in output
        assert "Processed files: 8" in output
        assert "Failed files: 2" in output
        assert "target_path" in output or "/tmp/target" in output
