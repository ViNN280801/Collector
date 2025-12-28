from __future__ import annotations

import time
import threading
from collections import defaultdict
from typing import Callable, Dict, List, Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock: threading.Lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        current_time = time.time()

        with self._lock:
            request_times = self._requests[key]

            request_times[:] = [t for t in request_times if current_time - t < self._window_seconds]

            if len(request_times) < self._max_requests:
                request_times.append(current_time)
                return True

            return False

    def get_remaining_requests(self, key: str) -> int:
        current_time = time.time()

        with self._lock:
            request_times = self._requests[key]
            request_times[:] = [t for t in request_times if current_time - t < self._window_seconds]
            return max(0, self._max_requests - len(request_times))


async def rate_limit_middleware(
    request: Request, call_next: Callable[[Request], Any], limiter: RateLimiter
) -> Response:
    client_ip = request.client.host if request.client else "unknown"

    if not limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"},
        )

    response: Response = await call_next(request)
    return response
