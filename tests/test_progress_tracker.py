from __future__ import annotations

import threading
from typing import List

import pytest

from src.core.progress_tracker import ProgressTracker


@pytest.mark.unit
class TestProgressTracker:
    def test_set_total(self) -> None:
        tracker = ProgressTracker()
        tracker.set_total(100)

        assert tracker.get_total() == 100
        assert tracker.get_current() == 0

    def test_increment(self) -> None:
        tracker = ProgressTracker()
        tracker.set_total(10)
        tracker.increment()

        assert tracker.get_current() == 1

    def test_increment_with_file(self) -> None:
        tracker = ProgressTracker()
        tracker.set_total(5)
        tracker.increment(current_file="/path/to/file.log")

        assert tracker.get_current() == 1

    def test_calculate_percentage_zero_total(self) -> None:
        tracker = ProgressTracker()
        tracker.set_total(0)
        tracker.increment()

        assert tracker._calculate_percentage() == 0.0

    def test_calculate_percentage_half(self) -> None:
        tracker = ProgressTracker()
        tracker.set_total(10)
        for _ in range(5):
            tracker.increment()

        assert tracker._calculate_percentage() == 50.0

    def test_calculate_percentage_full(self) -> None:
        tracker = ProgressTracker()
        tracker.set_total(10)
        for _ in range(10):
            tracker.increment()

        assert tracker._calculate_percentage() == 100.0

    def test_calculate_percentage_never_exceeds_100(self) -> None:
        tracker = ProgressTracker()
        tracker.set_total(10)
        for _ in range(15):
            tracker.increment()

        assert tracker._calculate_percentage() == 100.0

    def test_subscribe_callback(self) -> None:
        tracker = ProgressTracker()
        callback_called: List[tuple] = []

        def callback(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            callback_called.append((percentage, current, total, current_file))

        tracker.subscribe(callback)
        tracker.set_total(10)
        tracker.increment()

        assert len(callback_called) == 1
        assert callback_called[0][0] == 10.0
        assert callback_called[0][1] == 1
        assert callback_called[0][2] == 10

    def test_unsubscribe_callback(self) -> None:
        tracker = ProgressTracker()
        callback_called: List[tuple] = []

        def callback(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            callback_called.append((percentage, current, total, current_file))

        tracker.subscribe(callback)
        tracker.set_total(10)
        tracker.increment()
        tracker.unsubscribe(callback)
        tracker.increment()

        assert len(callback_called) == 1

    def test_multiple_callbacks(self) -> None:
        tracker = ProgressTracker()
        callback1_called: List[tuple] = []
        callback2_called: List[tuple] = []

        def callback1(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            callback1_called.append((percentage, current, total, current_file))

        def callback2(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            callback2_called.append((percentage, current, total, current_file))

        tracker.subscribe(callback1)
        tracker.subscribe(callback2)
        tracker.set_total(10)
        tracker.increment()

        assert len(callback1_called) == 1
        assert len(callback2_called) == 1

    def test_reset(self) -> None:
        tracker = ProgressTracker()
        tracker.set_total(10)
        tracker.increment()
        tracker.reset()

        assert tracker.get_total() == 0
        assert tracker.get_current() == 0

    def test_thread_safety(self) -> None:
        tracker = ProgressTracker()
        tracker.set_total(100)
        results: List[int] = []

        def worker() -> None:
            for _ in range(10):
                tracker.increment()
                results.append(tracker.get_current())

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert tracker.get_current() == 50
        assert len(results) == 50

    def test_callback_exception_handling(self) -> None:
        tracker = ProgressTracker()
        callback_called = False

        def failing_callback(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            nonlocal callback_called
            callback_called = True
            raise ValueError("Callback error")

        def working_callback(percentage: float, current: int, total: int, current_file: str | None = None) -> None:
            pass

        tracker.subscribe(failing_callback)
        tracker.subscribe(working_callback)
        tracker.set_total(10)
        tracker.increment()

        assert callback_called is True
        assert tracker.get_current() == 1
