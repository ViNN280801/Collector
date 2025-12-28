from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path
from typing import Literal, Optional

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Protocol
else:
    try:
        from typing import Protocol
    except ImportError:
        from typing_extensions import Protocol

from ..core.exceptions import ArchiveError
from ..utils.exception_wrapper import exception_wrapper


class ProgressCallback(Protocol):
    def __call__(
        self,
        percentage: float,
        current: int,
        total: int,
        current_file: Optional[str] = None,
    ) -> None:
        pass


class Archiver:
    @staticmethod
    def _get_total_files(source_dir: Path) -> int:
        count = 0
        for filepath in source_dir.rglob("*"):
            if filepath.is_file():
                count += 1
        return count

    @staticmethod
    @exception_wrapper()
    def create_zip_archive(
        source_dir: Path,
        target_file: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        source_dir = Path(source_dir).resolve()
        target_file = Path(target_file).resolve()

        if not source_dir.exists() or not source_dir.is_dir():
            raise ArchiveError(f"Source directory does not exist: {source_dir}")

        target_file.parent.mkdir(parents=True, exist_ok=True)

        total_files = Archiver._get_total_files(source_dir)

        if total_files == 0:
            raise ArchiveError(f"No files found in source directory: {source_dir}")

        current_file_index = 0

        try:
            with zipfile.ZipFile(target_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                for filepath in source_dir.rglob("*"):
                    if filepath.is_file():
                        arcname = filepath.relative_to(source_dir)
                        zipf.write(filepath, arcname)

                        current_file_index += 1

                        if progress_callback:
                            percentage = (current_file_index / total_files) * 100.0
                            progress_callback(
                                percentage,
                                current_file_index,
                                total_files,
                                str(filepath),
                            )

        except zipfile.BadZipFile as e:
            raise ArchiveError(f"Failed to create ZIP archive: {e}") from e
        except PermissionError as e:
            raise ArchiveError(f"Permission denied creating archive {target_file}: {e}") from e
        except OSError as e:
            raise ArchiveError(f"OS error creating archive: {e}") from e

    @staticmethod
    @exception_wrapper()
    def create_tar_archive(
        source_dir: Path,
        target_file: Path,
        compression: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        source_dir = Path(source_dir).resolve()
        target_file = Path(target_file).resolve()

        if not source_dir.exists() or not source_dir.is_dir():
            raise ArchiveError(f"Source directory does not exist: {source_dir}")

        target_file.parent.mkdir(parents=True, exist_ok=True)

        total_files = Archiver._get_total_files(source_dir)

        if total_files == 0:
            raise ArchiveError(f"No files found in source directory: {source_dir}")

        current_file_index = 0

        mode: Literal["w", "w:gz", "w:bz2", "w:xz"] = "w"
        if compression == "gzip":
            mode = "w:gz"
        elif compression == "bzip2":
            mode = "w:bz2"
        elif compression == "xz":
            mode = "w:xz"

        try:
            with tarfile.open(str(target_file), mode=mode) as tarf:
                for filepath in source_dir.rglob("*"):
                    if filepath.is_file():
                        arcname = filepath.relative_to(source_dir)
                        tarf.add(filepath, arcname=arcname, recursive=False)

                        current_file_index += 1

                        if progress_callback:
                            percentage = (current_file_index / total_files) * 100.0
                            progress_callback(
                                percentage,
                                current_file_index,
                                total_files,
                                str(filepath),
                            )

        except tarfile.TarError as e:
            raise ArchiveError(f"Failed to create TAR archive: {e}") from e
        except PermissionError as e:
            raise ArchiveError(f"Permission denied creating archive {target_file}: {e}") from e
        except OSError as e:
            raise ArchiveError(f"OS error creating archive: {e}") from e

    @staticmethod
    @exception_wrapper()
    def create_7z_archive(
        source_dir: Path,
        target_file: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        try:
            import py7zr
        except ImportError:
            raise ArchiveError("7Z format requires py7zr library. Install it with: pip install py7zr")

        source_dir = Path(source_dir).resolve()
        target_file = Path(target_file).resolve()

        if not source_dir.exists() or not source_dir.is_dir():
            raise ArchiveError(f"Source directory does not exist: {source_dir}")

        target_file.parent.mkdir(parents=True, exist_ok=True)

        total_files = Archiver._get_total_files(source_dir)

        if total_files == 0:
            raise ArchiveError(f"No files found in source directory: {source_dir}")

        current_file_index = 0

        try:
            with py7zr.SevenZipFile(target_file, "w") as archive:
                for filepath in source_dir.rglob("*"):
                    if filepath.is_file():
                        arcname = str(filepath.relative_to(source_dir))
                        archive.write(filepath, arcname=arcname)

                        current_file_index += 1

                        if progress_callback:
                            percentage = (current_file_index / total_files) * 100.0
                            progress_callback(
                                percentage,
                                current_file_index,
                                total_files,
                                str(filepath),
                            )

        except Exception as e:
            raise ArchiveError(f"Failed to create 7Z archive: {e}") from e

    @staticmethod
    @exception_wrapper()
    def create_archive(
        source_dir: Path,
        target_file: Path,
        archive_format: str = "zip",
        compression: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        if archive_format == "zip":
            Archiver.create_zip_archive(source_dir, target_file, progress_callback)
        elif archive_format == "tar":
            Archiver.create_tar_archive(source_dir, target_file, compression, progress_callback)
        elif archive_format == "7z":
            Archiver.create_7z_archive(source_dir, target_file, progress_callback)
        else:
            raise ArchiveError(f"Unsupported archive format: {archive_format}")
