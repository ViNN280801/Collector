from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.core.exceptions import FileOperationError, SecurityError
from src.core.file_operations import CopyStrategy, FileOperations, MoveRemoveStrategy, MoveStrategy
from src.utils.audit_logger import AuditLogger


@pytest.mark.unit
class TestCopyStrategy:
    def test_copy_strategy_executes(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test content")

        strategy = CopyStrategy()
        strategy.execute(source, target)

        assert target.exists()
        assert target.read_text() == "test content"
        assert source.exists()

    def test_copy_strategy_creates_parent_dirs(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "subdir" / "target.txt"
        source.write_text("test content")

        strategy = CopyStrategy()
        strategy.execute(source, target)

        assert target.exists()
        assert target.read_text() == "test content"


@pytest.mark.unit
class TestMoveStrategy:
    def test_move_strategy_executes(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test content")

        strategy = MoveStrategy()
        strategy.execute(source, target)

        assert target.exists()
        assert target.read_text() == "test content"
        assert not source.exists()

    def test_move_strategy_creates_parent_dirs(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "subdir" / "target.txt"
        source.write_text("test content")

        strategy = MoveStrategy()
        strategy.execute(source, target)

        assert target.exists()
        assert target.read_text() == "test content"
        assert not source.exists()


@pytest.mark.unit
class TestMoveRemoveStrategy:
    def test_move_remove_strategy_executes(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test content")

        strategy = MoveRemoveStrategy()
        strategy.execute(source, target)

        assert target.exists()
        assert target.read_text() == "test content"
        assert not source.exists()

    def test_move_remove_strategy_removes_source_if_exists(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test content")

        strategy = MoveRemoveStrategy()
        strategy.execute(source, target)

        assert not source.exists()


@pytest.mark.unit
class TestFileOperations:
    def test_file_operations_with_copy_strategy(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test content")

        operations = FileOperations(CopyStrategy())
        operations.execute_operation(source, target)

        assert target.exists()
        assert source.exists()

    def test_file_operations_with_move_strategy(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test content")

        operations = FileOperations(MoveStrategy())
        operations.execute_operation(source, target)

        assert target.exists()
        assert not source.exists()

    def test_file_operations_set_strategy(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test content")

        operations = FileOperations(CopyStrategy())
        operations.set_strategy(MoveStrategy())
        operations.execute_operation(source, target)

        assert target.exists()
        assert not source.exists()

    def test_file_operations_audit_logging(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test content")

        mock_audit_logger = MagicMock(spec=AuditLogger, autospec=True)
        operations = FileOperations(CopyStrategy(), audit_logger=mock_audit_logger)
        operations.execute_operation(source, target)

        mock_audit_logger.log_operation.assert_called_once()
        call_args = mock_audit_logger.log_operation.call_args
        assert call_args[1]["operation"] == "copy"
        assert call_args[1]["source"] == source
        assert call_args[1]["target"] == target

    def test_file_operations_audit_logging_on_error(self, temp_dir: Path) -> None:
        source = temp_dir / "nonexistent.txt"
        target = temp_dir / "target.txt"

        mock_audit_logger = MagicMock(spec=AuditLogger, autospec=True)
        operations = FileOperations(CopyStrategy(), audit_logger=mock_audit_logger)

        with pytest.raises(FileOperationError):
            operations.execute_operation(source, target)

        mock_audit_logger.log_error.assert_called_once()

    def test_file_operations_set_audit_logger(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        target = temp_dir / "target.txt"
        source.write_text("test content")

        operations = FileOperations(CopyStrategy())
        mock_audit_logger = MagicMock(spec=AuditLogger, autospec=True)
        operations.set_audit_logger(mock_audit_logger)
        operations.execute_operation(source, target)

        mock_audit_logger.log_operation.assert_called_once()

    def test_file_operations_path_security_validation(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        source.write_text("test content")

        long_path = "x" * 5000
        long_target = temp_dir / long_path / "target.txt"

        operations = FileOperations(CopyStrategy())
        with pytest.raises(SecurityError, match="Path exceeds maximum length"):
            operations.execute_operation(source, long_target)

    def test_file_operations_dangerous_chars_in_path(self, temp_dir: Path) -> None:
        source = temp_dir / "source.txt"
        source.write_text("test content")

        dangerous_target = temp_dir / "target<file>.txt"

        operations = FileOperations(CopyStrategy())
        with pytest.raises(SecurityError, match="Dangerous character"):
            operations.execute_operation(source, dangerous_target)

    def test_file_operations_error_handling(self, temp_dir: Path) -> None:
        source = temp_dir / "nonexistent.txt"
        target = temp_dir / "target.txt"

        operations = FileOperations(CopyStrategy())
        with pytest.raises(FileOperationError):
            operations.execute_operation(source, target)
