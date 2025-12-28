from __future__ import annotations

import tempfile
import shutil
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_data_dir(temp_dir: Path) -> Generator[Path, None, None]:
    data_dir = temp_dir / "test_data"
    data_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "file1.log").write_text("test content 1")
    (data_dir / "file2.txt").write_text("test content 2")
    (data_dir / "file3.log").write_text("test content 3")
    (data_dir / "subdir").mkdir()
    (data_dir / "subdir" / "file4.log").write_text("test content 4")

    yield data_dir


@pytest.fixture
def production_logs_source() -> Path:
    """Returns the path to the production logs directory (read-only, never modified)."""
    test_files_dir = Path(__file__).parent / "test_files"
    if not test_files_dir.exists():
        pytest.skip("Production logs directory not found")
    return test_files_dir


@pytest.fixture
def production_logs_dir(temp_dir: Path, production_logs_source: Path) -> Generator[Path, None, None]:
    """
    Copies production logs to a temporary directory for testing.
    Original files in tests/test_files are never modified or deleted.
    """
    copied_dir = temp_dir / "production_logs"
    if production_logs_source.exists():
        shutil.copytree(production_logs_source, copied_dir, dirs_exist_ok=True)
    yield copied_dir
