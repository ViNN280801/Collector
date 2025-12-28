from __future__ import annotations

from argparse import ArgumentParser

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..core.security_constants import MAX_REQUEST_SIZE_BYTES, MAX_REQUEST_SIZE_MB
from .auth import AuthManager
from .auth_routes import router as auth_router
from .rate_limiter import RateLimiter, rate_limit_middleware
from .routes import router, set_auth_manager
from .routes_extended import router_extended
from .routes_v2 import router_v2, set_auth_manager_v2
from .websocket_routes import router as websocket_router

rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
auth_manager = AuthManager(require_auth=False)
set_auth_manager(auth_manager)
set_auth_manager_v2(auth_manager)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Universal Log Collector API",
        version="0.0.1",
        description="Universal file collector with CLI, REST API and GUI interfaces",
    )
    app.include_router(router)
    app.include_router(router_v2)
    app.include_router(router_extended)
    app.include_router(auth_router)
    app.include_router(websocket_router)

    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        return await rate_limit_middleware(request, call_next, rate_limiter)

    @app.middleware("http")
    async def check_request_size(request: Request, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > MAX_REQUEST_SIZE_BYTES:
                        return JSONResponse(
                            status_code=413,
                            content={
                                "error": "Payload Too Large",
                                "message": f"Request body exceeds maximum size: {MAX_REQUEST_SIZE_MB}MB",
                                "size": size,
                                "max_size": MAX_REQUEST_SIZE_BYTES,
                            },
                        )
                except ValueError:
                    pass
        return await call_next(request)

    return app


def main() -> None:
    parser = ArgumentParser(description="Universal Log Collector API")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    args = parser.parse_args()

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
