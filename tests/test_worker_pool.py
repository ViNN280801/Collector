from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from src.core.file_operations import CopyStrategy, FileOperations
from src.core.progress_tracker import ProgressTracker
from src.core.worker_pool import MAX_WORKERS, WorkerPool


@pytest.mark.unit
class TestWorkerPoolCalculateOptimalWorkers:
    def test_calculate_optimal_workers_small_number(self) -> None:
        pool = WorkerPool()
        result = pool._calculate_optimal_workers(50)

        assert result == 1

    def test_calculate_optimal_workers_medium_number(self) -> None:
        pool = WorkerPool()
        result = pool._calculate_optimal_workers(500)

        assert result == min(5, os.cpu_count() or 4, MAX_WORKERS)

    def test_calculate_optimal_workers_large_number(self) -> None:
        pool = WorkerPool()
        result = pool._calculate_optimal_workers(10000)

        assert result == min(100, os.cpu_count() or 4, MAX_WORKERS)

    def test_calculate_optimal_workers_respects_max(self) -> None:
        pool = WorkerPool()
        result = pool._calculate_optimal_workers(100000)

        assert result <= MAX_WORKERS

    def test_calculate_optimal_workers_respects_cpu_count(self) -> None:
        pool = WorkerPool()
        cpu_count = os.cpu_count() or 4
        result = pool._calculate_optimal_workers(1000)

        assert result <= cpu_count


@pytest.mark.unit
class TestWorkerPoolCreateBatches:
    def test_create_batches_empty_list(self) -> None:
        pool = WorkerPool()
        result = pool._create_batches([], 4)

        assert result == []

    def test_create_batches_zero_workers(self) -> None:
        pool = WorkerPool()
        filepaths = [Path(f"file{i}.txt") for i in range(10)]
        result = pool._create_batches(filepaths, 0)

        assert result == []

    def test_create_batches_single_worker(self) -> None:
        pool = WorkerPool()
        filepaths = [Path(f"file{i}.txt") for i in range(10)]
        result = pool._create_batches(filepaths, 1)

        assert len(result) == 1
        assert len(result[0]) == 10

    def test_create_batches_multiple_workers(self) -> None:
        pool = WorkerPool()
        filepaths = [Path(f"file{i}.txt") for i in range(20)]
        result = pool._create_batches(filepaths, 4)

        assert len(result) == 4
        total_files = sum(len(batch) for batch in result)
        assert total_files == 20

    def test_create_batches_uneven_distribution(self) -> None:
        pool = WorkerPool()
        filepaths = [Path(f"file{i}.txt") for i in range(25)]
        result = pool._create_batches(filepaths, 4)

        assert len(result) >= 4
        total_files = sum(len(batch) for batch in result)
        assert total_files == 25

    def test_create_batches_single_file(self) -> None:
        pool = WorkerPool()
        filepaths = [Path("file.txt")]
        result = pool._create_batches(filepaths, 4)

        assert len(result) == 1
        assert len(result[0]) == 1


@pytest.mark.unit
class TestWorkerPoolExecute:
    def test_execute_empty_file_list(self, temp_dir: Path) -> None:
        pool = WorkerPool()
        tracker = ProgressTracker()
        operations = FileOperations(CopyStrategy())

        pool.execute([], temp_dir, temp_dir / "target", tracker, operations)

        assert tracker.get_total() == 0
        assert tracker.get_current() == 0

    def test_execute_single_file(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        source_file = source_dir / "file.txt"
        source_file.write_text("test content")

        pool = WorkerPool()
        tracker = ProgressTracker()
        operations = FileOperations(CopyStrategy())

        pool.execute([source_file], source_dir, target_dir, tracker, operations)

        target_file = target_dir / "file.txt"
        assert target_file.exists()
        assert target_file.read_text() == "test content"
        assert tracker.get_current() == 1
        assert tracker.get_total() == 1

    def test_execute_multiple_files(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        filepaths = []
        for i in range(10):
            file = source_dir / f"file{i}.txt"
            file.write_text(f"content {i}")
            filepaths.append(file)

        pool = WorkerPool()
        tracker = ProgressTracker()
        operations = FileOperations(CopyStrategy())

        pool.execute(filepaths, source_dir, target_dir, tracker, operations)

        assert tracker.get_current() == 10
        assert tracker.get_total() == 10

        for i in range(10):
            target_file = target_dir / f"file{i}.txt"
            assert target_file.exists()
            assert target_file.read_text() == f"content {i}"

    def test_execute_with_subdirectories(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        subdir = source_dir / "subdir"
        subdir.mkdir()

        file1 = source_dir / "file1.txt"
        file1.write_text("content 1")
        file2 = subdir / "file2.txt"
        file2.write_text("content 2")

        pool = WorkerPool()
        tracker = ProgressTracker()
        operations = FileOperations(CopyStrategy())

        pool.execute([file1, file2], source_dir, target_dir, tracker, operations)

        assert tracker.get_current() == 2
        assert (target_dir / "file1.txt").exists()
        assert (target_dir / "subdir" / "file2.txt").exists()

    def test_execute_progress_tracking(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        filepaths = []
        for i in range(5):
            file = source_dir / f"file{i}.txt"
            file.write_text(f"content {i}")
            filepaths.append(file)

        pool = WorkerPool()
        tracker = ProgressTracker()
        callback_calls: list = []

        def progress_callback(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            callback_calls.append((percentage, current, total, current_file))

        tracker.subscribe(progress_callback)
        operations = FileOperations(CopyStrategy())

        pool.execute(filepaths, source_dir, target_dir, tracker, operations)

        assert len(callback_calls) >= 5
        assert callback_calls[-1][1] == 5
        assert callback_calls[-1][2] == 5

    def test_execute_handles_errors_gracefully(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        existing_file = source_dir / "existing.txt"
        existing_file.write_text("content")
        nonexistent_file = source_dir / "nonexistent.txt"

        pool = WorkerPool()
        tracker = ProgressTracker()
        operations = FileOperations(CopyStrategy())

        pool.execute([existing_file, nonexistent_file], source_dir, target_dir, tracker, operations)

        assert tracker.get_current() == 2
        assert (target_dir / "existing.txt").exists()


@pytest.mark.unit
class TestWorkerPoolStop:
    def test_stop_sets_event(self) -> None:
        pool = WorkerPool()
        pool.stop()

        assert pool._stop_event.is_set() is True

    def test_stop_with_running_workers(self, temp_dir: Path) -> None:
        source_dir = temp_dir / "source"
        target_dir = temp_dir / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        filepaths = []
        for i in range(20):
            file = source_dir / f"file{i}.txt"
            file.write_text(f"content {i}")
            filepaths.append(file)

        pool = WorkerPool()
        tracker = ProgressTracker()
        operations = FileOperations(CopyStrategy())

        def slow_operation(source: Path, target: Path) -> None:
            time.sleep(0.1)
            operations._strategy.execute(source, target)

        slow_operations = FileOperations(CopyStrategy())
        # Use setattr to avoid mypy error about method assignment
        setattr(slow_operations._strategy, "execute", slow_operation)

        import threading

        def run_execute() -> None:
            pool.execute(filepaths, source_dir, target_dir, tracker, slow_operations)

        thread = threading.Thread(target=run_execute, daemon=True)
        thread.start()

        time.sleep(0.05)
        pool.stop()
        thread.join(timeout=2.0)

        assert pool._stop_event.is_set() is True
