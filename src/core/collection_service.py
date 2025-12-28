from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from ..utils.audit_logger import AuditLogger
from ..utils.exception_wrapper import exception_wrapper
from ..utils.pc_info_collector import PCInfoCollector
from .config import CollectionConfig
from .exceptions import FileOperationError
from .file_filter import FileFilter
from .file_operations import (
    CopyStrategy,
    FileOperations,
    MoveRemoveStrategy,
    MoveStrategy,
)
from .progress_tracker import ProgressTracker
from .validator import validate_config
from .worker_pool import WorkerPool


def _collect_all_files(paths: List[Path]) -> List[Path]:
    all_files: List[Path] = []
    for source_path in paths:
        if source_path.is_file():
            all_files.append(source_path)
        elif source_path.is_dir():
            for filepath in source_path.rglob("*"):
                if filepath.is_file():
                    all_files.append(filepath)
    return all_files


def _find_common_base(filepaths: List[Path], source_paths: List[Path]) -> Path:
    if not filepaths:
        return Path(source_paths[0]).resolve().parent

    resolved_paths = [Path(p).resolve() for p in source_paths]
    common_parts = None

    for filepath in filepaths[:10]:
        try:
            resolved = filepath.resolve()
            for src_path in resolved_paths:
                src_resolved = Path(src_path).resolve()
                if src_resolved.is_file():
                    src_resolved = src_resolved.parent

                try:
                    if src_resolved in resolved.parents or resolved.parent == src_resolved:
                        relative = resolved.relative_to(src_resolved)
                        parts = relative.parts
                        parts_len = len(parts)
                        if common_parts is None:
                            common_parts = parts_len
                        else:
                            # Type narrowing: common_parts is guaranteed to be int here
                            # This can execute on subsequent loop iterations
                            common_parts = min(cast(int, common_parts), parts_len)
                        break
                except ValueError:
                    continue
        except Exception:
            continue

    if len(resolved_paths) == 1:
        base = resolved_paths[0]
        if base.is_file():
            base = base.parent
        return base

    return resolved_paths[0].parent if resolved_paths[0].is_file() else resolved_paths[0]


class CollectionService:
    def __init__(self, config: CollectionConfig) -> None:
        validate_config(config)
        self._config = config
        self._worker_pool = WorkerPool()
        self._file_filter = FileFilter()
        self._progress_tracker = ProgressTracker()

        from .file_operations import FileOperationStrategy

        if config.operation_mode == "copy":
            strategy: FileOperationStrategy = CopyStrategy()
        elif config.operation_mode == "move":
            strategy = MoveStrategy()
        elif config.operation_mode == "move_remove":
            strategy = MoveRemoveStrategy()
        else:
            strategy = CopyStrategy()

        audit_logger = None
        if config.enable_audit_logging:
            audit_logger = AuditLogger(log_file=config.audit_log_file)

        self._file_operations = FileOperations(strategy, audit_logger=audit_logger)

    def get_progress_tracker(self) -> ProgressTracker:
        return self._progress_tracker

    @exception_wrapper()
    def collect(self) -> Dict[str, Any]:
        all_files = _collect_all_files([Path(p) for p in self._config.source_paths])

        filtered_files = self._file_filter.filter_files(all_files, self._config.patterns)

        if not filtered_files:
            return {
                "total_files": 0,
                "processed_files": 0,
                "failed_files": 0,
                "target_path": str(self._config.target_path),
            }

        source_base = _find_common_base(filtered_files, self._config.source_paths)
        target_base = Path(self._config.target_path).resolve()

        self._progress_tracker.set_total(len(filtered_files))

        try:
            self._worker_pool.execute(
                filtered_files,
                source_base,
                target_base,
                self._progress_tracker,
                self._file_operations,
            )
        except Exception as e:
            raise FileOperationError(f"Collection failed: {e}") from e

        # NOTE: Flush is called from each worker thread before exit (in worker_pool._worker_loop)
        # This is necessary because threading.local() is thread-specific - each worker must
        # flush its own counters. The flush in worker_pool.execute() after join() cannot
        # access worker thread's local storage.
        # Use flush=False for performance - workers already flushed their counters
        processed_count = self._progress_tracker.get_current(flush=False)

        result: Dict[str, Any] = {
            "total_files": len(filtered_files),
            "processed_files": processed_count,
            "failed_files": len(filtered_files) - processed_count,
            "target_path": str(target_base),
        }

        if self._config.collect_system_info:
            try:
                pc_collector = PCInfoCollector()
                pc_collector.collect_all()
                pc_info_path = target_base / "pc_info.json"
                pc_collector.save_to_file(str(pc_info_path), format="json")
                result["pc_info_collected"] = True
                result["pc_info_path"] = str(pc_info_path)
            except Exception:
                result["pc_info_collected"] = False

        if self._config.create_archive:
            try:
                from ..archive.archiver import Archiver

                archive_name = f"archive.{self._config.archive_format}"
                if self._config.archive_format == "tar" and self._config.archive_compression:
                    if self._config.archive_compression == "gzip":
                        archive_name = "archive.tar.gz"
                    elif self._config.archive_compression == "bzip2":
                        archive_name = "archive.tar.bz2"
                    elif self._config.archive_compression == "xz":
                        archive_name = "archive.tar.xz"
                elif self._config.archive_format == "7z":
                    archive_name = "archive.7z"

                archive_path = target_base.parent / archive_name

                def archive_progress_callback(
                    percentage: float, current: int, total: int, current_file: Optional[str] = None
                ) -> None:
                    self._progress_tracker.increment()

                Archiver.create_archive(
                    source_dir=target_base,
                    target_file=archive_path,
                    archive_format=self._config.archive_format,
                    compression=self._config.archive_compression,
                    progress_callback=archive_progress_callback,
                )
                result["archive_created"] = True
                result["archive_path"] = str(archive_path)
            except Exception as e:
                result["archive_created"] = False
                result["archive_error"] = str(e)

        return result
