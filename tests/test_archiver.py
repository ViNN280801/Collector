from __future__ import annotations

from pathlib import Path

import pytest

from src.archive.archiver import Archiver
from src.core.exceptions import ArchiveError


@pytest.mark.unit
class TestArchiverZip:
    def test_create_zip_archive(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.zip"
        source_dir.mkdir()

        for i in range(3):
            (source_dir / f"file{i}.txt").write_text(f"content {i}")

        Archiver.create_zip_archive(source_dir, target_file)

        assert target_file.exists()
        assert target_file.stat().st_size > 0

    def test_create_zip_archive_with_progress(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.zip"
        source_dir.mkdir()

        for i in range(5):
            (source_dir / f"file{i}.txt").write_text(f"content {i}")

        callback_calls: list = []

        def progress_callback(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            callback_calls.append((percentage, current, total, current_file))

        Archiver.create_zip_archive(source_dir, target_file, progress_callback=progress_callback)

        assert len(callback_calls) == 5
        assert callback_calls[-1][1] == 5
        assert callback_calls[-1][2] == 5

    def test_create_zip_archive_nonexistent_source(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "nonexistent"
        target_file = temp_dir / "archive.zip"

        with pytest.raises(ArchiveError, match="Source directory does not exist"):
            Archiver.create_zip_archive(source_dir, target_file)

    def test_create_zip_archive_empty_directory(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.zip"
        source_dir.mkdir()

        with pytest.raises(ArchiveError, match="No files found"):
            Archiver.create_zip_archive(source_dir, target_file)


@pytest.mark.unit
class TestArchiverTar:
    def test_create_tar_archive(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.tar"
        source_dir.mkdir()

        for i in range(3):
            (source_dir / f"file{i}.txt").write_text(f"content {i}")

        Archiver.create_tar_archive(source_dir, target_file)

        assert target_file.exists()
        assert target_file.stat().st_size > 0

    def test_create_tar_archive_gzip(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.tar.gz"
        source_dir.mkdir()

        for i in range(3):
            (source_dir / f"file{i}.txt").write_text(f"content {i}")

        Archiver.create_tar_archive(source_dir, target_file, compression="gzip")

        assert target_file.exists()
        assert target_file.stat().st_size > 0

    def test_create_tar_archive_bzip2(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.tar.bz2"
        source_dir.mkdir()

        for i in range(3):
            (source_dir / f"file{i}.txt").write_text(f"content {i}")

        Archiver.create_tar_archive(source_dir, target_file, compression="bzip2")

        assert target_file.exists()
        assert target_file.stat().st_size > 0

    def test_create_tar_archive_with_progress(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.tar"
        source_dir.mkdir()

        for i in range(5):
            (source_dir / f"file{i}.txt").write_text(f"content {i}")

        callback_calls: list = []

        def progress_callback(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            callback_calls.append((percentage, current, total, current_file))

        Archiver.create_tar_archive(source_dir, target_file, progress_callback=progress_callback)

        assert len(callback_calls) == 5


@pytest.mark.unit
class TestArchiver7Z:
    def test_create_7z_archive_requires_library(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.7z"
        source_dir.mkdir()

        (source_dir / "file.txt").write_text("content")

        try:
            import py7zr  # noqa: F401
        except ImportError:
            with pytest.raises(ArchiveError, match="py7zr library"):
                Archiver.create_7z_archive(source_dir, target_file)
        else:
            Archiver.create_7z_archive(source_dir, target_file)
            assert target_file.exists()


@pytest.mark.unit
class TestArchiverCreateArchive:
    def test_create_archive_zip(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.zip"
        source_dir.mkdir()

        (source_dir / "file.txt").write_text("content")

        Archiver.create_archive(source_dir, target_file, archive_format="zip")

        assert target_file.exists()

    def test_create_archive_tar(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.tar"
        source_dir.mkdir()

        (source_dir / "file.txt").write_text("content")

        Archiver.create_archive(source_dir, target_file, archive_format="tar")

        assert target_file.exists()

    def test_create_archive_tar_gzip(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.tar.gz"
        source_dir.mkdir()

        (source_dir / "file.txt").write_text("content")

        Archiver.create_archive(source_dir, target_file, archive_format="tar", compression="gzip")

        assert target_file.exists()

    def test_create_archive_unsupported_format(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_file = temp_dir / "archive.xyz"
        source_dir.mkdir()

        (source_dir / "file.txt").write_text("content")

        with pytest.raises(ArchiveError, match="Unsupported archive format"):
            Archiver.create_archive(source_dir, target_file, archive_format="xyz")
