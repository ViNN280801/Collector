from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..core import CollectionConfigBuilder, CollectionService, PatternConfig
from ..types import JobId
from .auth import AuthManager
from .job_repository import InMemoryJobRepository
from .models import CollectionRequest, ProgressResponse, ResultResponse
from .routes import get_auth_manager as get_auth_manager_base

router_v2 = APIRouter(prefix="/api/v2")
job_repository_v2 = InMemoryJobRepository()
active_services_v2: Dict[str, CollectionService] = {}
active_services_lock_v2 = threading.Lock()

_auth_manager_v2: Optional[AuthManager] = None


def get_auth_manager_v2() -> Optional[AuthManager]:
    return _auth_manager_v2 or get_auth_manager_base()


def set_auth_manager_v2(manager: AuthManager) -> None:
    global _auth_manager_v2
    _auth_manager_v2 = manager


async def optional_auth_v2(
    http_request: Request,
    auth_manager: Optional[AuthManager] = Depends(get_auth_manager_v2),
) -> Optional[str]:
    if auth_manager and auth_manager.is_auth_required():
        try:
            api_key_auth = auth_manager.get_api_key_auth()
            api_key = http_request.headers.get("X-API-Key")
            if api_key:
                return await api_key_auth.verify_api_key(api_key)
        except Exception:
            pass
    return None


@router_v2.post("/collect")
async def collect_files_v2(
    request: CollectionRequest,
    user: Optional[str] = Depends(optional_auth_v2),
) -> Dict[str, Any]:
    source_paths = [Path(p) for p in request.source_paths]
    target_path = Path(request.target_path)

    patterns = []
    if request.patterns:
        for pattern_model in request.patterns:
            patterns.append(
                PatternConfig(
                    pattern=pattern_model.pattern,
                    pattern_type=pattern_model.pattern_type,
                )
            )

    config_builder = (
        CollectionConfigBuilder()
        .with_source_paths(source_paths)
        .with_target_path(target_path)
        .with_patterns(patterns)
        .with_operation_mode(request.operation_mode)
        .with_archive(
            request.create_archive,
            request.archive_format,
            request.archive_compression if hasattr(request, "archive_compression") else None,
        )
        .with_system_info(request.collect_system_info)
    )

    if request.email_config:
        email_config_dict = request.email_config.model_dump()
        config_builder.with_email(True, email_config_dict)

    config = config_builder.build()

    job_id = job_repository_v2.create_job({"config": config})

    service = CollectionService(config)

    with active_services_lock_v2:
        active_services_v2[job_id] = service

    progress_tracker = service.get_progress_tracker()

    def update_job_progress(percentage: float, current: int, total: int, current_file: Optional[str] = None) -> None:
        job_repository_v2.update_job(
            job_id,
            {
                "percentage": percentage,
                "current": current,
                "total": total,
                "current_file": current_file if current_file else "",
            },
        )

    progress_tracker.subscribe(update_job_progress)

    def run_collection():
        from datetime import datetime

        try:
            results = service.collect()
            job_repository_v2.update_job(
                job_id,
                {
                    "status": "completed",
                    "results": results,
                    "completed_at": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            job_repository_v2.update_job(
                job_id,
                {
                    "status": "failed",
                    "error": str(e),
                    "results": None,
                    "completed_at": datetime.now().isoformat(),
                },
            )
        finally:
            with active_services_lock_v2:
                if job_id in active_services_v2:
                    del active_services_v2[job_id]

    thread = threading.Thread(target=run_collection, daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "started", "api_version": "v2"}


@router_v2.get("/progress/{job_id}")
def get_progress_v2(job_id: str) -> ProgressResponse:
    job = job_repository_v2.get_job(JobId(job_id))

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return ProgressResponse(
        job_id=job_id,
        percentage=job.get("percentage", 0.0),
        current=job.get("current", 0),
        total=job.get("total", 0),
        current_file=job.get("current_file"),
    )


@router_v2.get("/result/{job_id}")
def get_result_v2(job_id: str) -> ResultResponse:
    job = job_repository_v2.get_job(JobId(job_id))

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return ResultResponse(job_id=job_id, status=job.get("status", "pending"), results=job.get("results", {}))
