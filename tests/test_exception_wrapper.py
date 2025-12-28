from __future__ import annotations

import io
import logging
from contextlib import redirect_stderr
from unittest.mock import MagicMock

import pytest

from src.utils.exception_wrapper import exception_wrapper


@pytest.mark.unit
class TestExceptionWrapper:
    def test_exception_wrapper_without_logger(self) -> None:
        import os
        import sys

        original_env = os.environ.get("PYTEST_CURRENT_TEST")
        pytest_in_modules = "pytest" in sys.modules

        try:
            if "PYTEST_CURRENT_TEST" in os.environ:
                del os.environ["PYTEST_CURRENT_TEST"]
            if "pytest" in sys.modules:
                sys.modules.pop("pytest", None)

            @exception_wrapper()
            def failing_function() -> None:
                raise ValueError("Test error")

            stderr_capture = io.StringIO()
            with redirect_stderr(stderr_capture):
                with pytest.raises(ValueError, match="Test error"):
                    failing_function()

            stderr_output = stderr_capture.getvalue()
            assert "Error in" in stderr_output
            assert "failing_function" in stderr_output
            assert "Test error" in stderr_output
        finally:
            if original_env is not None:
                os.environ["PYTEST_CURRENT_TEST"] = original_env
            if pytest_in_modules:
                import pytest as pytest_module

                sys.modules["pytest"] = pytest_module

    def test_exception_wrapper_with_logger(self) -> None:
        mock_logger = MagicMock(spec=logging.Logger, autospec=True)

        @exception_wrapper(logger=mock_logger)
        def failing_function() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Error in" in call_args[0][0]
        assert call_args[1]["exc_info"] is True

    def test_exception_wrapper_preserves_function_metadata(self) -> None:
        @exception_wrapper()
        def test_function() -> str:
            """Test docstring"""
            return "success"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test docstring"

    def test_exception_wrapper_successful_execution(self) -> None:
        @exception_wrapper()
        def successful_function() -> str:
            return "success"

        result = successful_function()
        assert result == "success"

    def test_exception_wrapper_with_arguments(self) -> None:
        @exception_wrapper()
        def function_with_args(a: int, b: int) -> int:
            if a < 0:
                raise ValueError("Negative value")
            return a + b

        assert function_with_args(5, 3) == 8

        with pytest.raises(ValueError, match="Negative value"):
            function_with_args(-1, 3)

    def test_exception_wrapper_with_kwargs(self) -> None:
        @exception_wrapper()
        def function_with_kwargs(**kwargs: int) -> int:
            if "x" in kwargs and kwargs["x"] < 0:
                raise ValueError("Negative value")
            return sum(kwargs.values())

        assert function_with_kwargs(x=5, y=3) == 8

        with pytest.raises(ValueError, match="Negative value"):
            function_with_kwargs(x=-1, y=3)

    def test_exception_wrapper_re_raises_exception(self) -> None:
        @exception_wrapper()
        def failing_function() -> None:
            raise RuntimeError("Original error")

        with pytest.raises(RuntimeError, match="Original error") as exc_info:
            failing_function()

        assert exc_info.value.args[0] == "Original error"

    def test_exception_wrapper_with_method(self) -> None:
        class TestClass:
            @exception_wrapper()
            def failing_method(self) -> None:
                raise ValueError("Method error")

        obj = TestClass()
        with pytest.raises(ValueError, match="Method error"):
            obj.failing_method()

    def test_exception_wrapper_multiple_decorators(self) -> None:
        call_count = 0

        def count_calls(func):
            def wrapper(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                return func(*args, **kwargs)

            return wrapper

        @count_calls
        @exception_wrapper()
        def test_function() -> str:
            return "success"

        result = test_function()
        assert result == "success"
        assert call_count == 1
