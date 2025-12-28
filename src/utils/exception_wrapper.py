from __future__ import annotations

import sys
import logging
import traceback
from functools import wraps
from typing import Callable, Optional, TypeVar, Any

T = TypeVar("T")


def _is_testing_environment() -> bool:
    import os as os_module

    return "PYTEST_CURRENT_TEST" in os_module.environ or "pytest" in sys.modules


def exception_wrapper(logger: Optional[logging.Logger] = None):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error in {func.__module__}.{func.__qualname__}"

                if logger:
                    logger.error(error_msg, exc_info=True)
                elif not _is_testing_environment():
                    print(f"{error_msg}: {e}", file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)

                raise

        return wrapper

    return decorator
