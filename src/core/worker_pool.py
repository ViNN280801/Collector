from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import List, Optional

from ..utils.exception_wrapper import exception_wrapper
from .file_operations import FileOperations
from .progress_tracker import ProgressTracker

MAX_WORKERS = 32


class WorkerPool:
    def __init__(self) -> None:
        self._num_workers: int = 0
        self._workers: List[threading.Thread] = []
        self._progress_tracker: Optional[ProgressTracker] = None
        self._file_operations: Optional[FileOperations] = None
        self._stop_event: threading.Event = threading.Event()
        self._lock: threading.Lock = threading.Lock()

    def _calculate_optimal_workers(self, total_files: int) -> int:
        return min(
            os.cpu_count() or 4,
            max(1, total_files // 100),
            MAX_WORKERS,
        )

    def _create_batches(self, filepaths: List[Path], num_workers: int) -> List[List[Path]]:
        if not filepaths or num_workers == 0:
            return []

        batch_size = max(1, len(filepaths) // num_workers)
        batches: List[List[Path]] = []

        for i in range(0, len(filepaths), batch_size):
            batch = filepaths[i : i + batch_size]
            if batch:
                batches.append(batch)

        if not batches and filepaths:
            batches = [filepaths]

        return batches

    def _worker_loop(
        self,
        worker_id: int,
        batch: List[Path],
        source_base: Path,
        target_base: Path,
    ) -> None:
        if not self._file_operations or not self._progress_tracker:
            return

        for filepath in batch:
            if self._stop_event.is_set():
                break

            try:
                try:
                    relative_path: Path = filepath.resolve().relative_to(source_base.resolve())
                except ValueError:
                    relative_path = Path(filepath.name)

                target_path = target_base / relative_path

                self._file_operations.execute_operation(filepath, target_path)

                self._progress_tracker.increment(current_file=str(filepath))

            except Exception:
                self._progress_tracker.increment(current_file=str(filepath))
                continue

        # CRITICAL: Flush thread-local counters from THIS worker thread before exit
        # threading.local() is thread-specific, so flush must be called from each worker thread
        # This ensures all counters are flushed to shared counter before thread terminates
        if self._progress_tracker:
            self._progress_tracker.flush()

    @exception_wrapper()
    def execute(
        self,
        filepaths: List[Path],
        source_base: Path,
        target_base: Path,
        progress_tracker: ProgressTracker,
        file_operations: FileOperations,
    ) -> None:
        self._stop_event.clear()

        num_workers = self._calculate_optimal_workers(len(filepaths))
        batches = self._create_batches(filepaths, num_workers)

        if not batches:
            return

        self._progress_tracker = progress_tracker
        self._file_operations = file_operations
        self._num_workers = min(len(batches), num_workers)

        progress_tracker.set_total(len(filepaths))

        self._workers = []
        for worker_id, batch in enumerate(batches):
            if worker_id >= self._num_workers:
                break

            thread = threading.Thread(
                target=self._worker_loop,
                args=(worker_id, batch, source_base, target_base),
                daemon=True,
            )
            self._workers.append(thread)
            thread.start()

        for thread in self._workers:
            thread.join()

        # NOTE: Flush is called from each worker thread before exit (in _worker_loop)
        # This is necessary because threading.local() is thread-specific - main thread
        # cannot access worker thread's local storage. Each worker flushes its own
        # counters, which is safe because _flush_updates() checks if counter > 0.

        self._workers.clear()

    def stop(self) -> None:
        self._stop_event.set()
        for thread in self._workers:
            if thread.is_alive():
                thread.join(timeout=1.0)
