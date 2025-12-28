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

router = APIRouter(prefix="/api/v1")
job_repository = InMemoryJobRepository()
active_services: Dict[str, CollectionService] = {}
active_services_lock = threading.Lock()

_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> Optional[AuthManager]:
    return _auth_manager


def set_auth_manager(manager: AuthManager) -> None:
    global _auth_manager
    _auth_manager = manager


async def optional_auth(
    http_request: Request,
    auth_manager: Optional[AuthManager] = Depends(get_auth_manager),
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


@router.post("/collect")
async def collect_files(
    request: CollectionRequest,
    user: Optional[str] = Depends(optional_auth),
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

    job_id = job_repository.create_job({"config": config})

    service = CollectionService(config)

    with active_services_lock:
        active_services[job_id] = service

    progress_tracker = service.get_progress_tracker()

    def update_job_progress(percentage: float, current: int, total: int, current_file: Optional[str] = None) -> None:
        job_repository.update_job(
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
            job_repository.update_job(
                job_id,
                {
                    "status": "completed",
                    "results": results,
                    "completed_at": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            job_repository.update_job(
                job_id,
                {
                    "status": "failed",
                    "error": str(e),
                    "results": None,
                    "completed_at": datetime.now().isoformat(),
                },
            )
        finally:
            with active_services_lock:
                if job_id in active_services:
                    del active_services[job_id]

    thread = threading.Thread(target=run_collection, daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "started"}


@router.get("/progress/{job_id}")
def get_progress(job_id: str) -> ProgressResponse:
    job = job_repository.get_job(JobId(job_id))

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return ProgressResponse(
        job_id=job_id,
        percentage=job.get("percentage", 0.0),
        current=job.get("current", 0),
        total=job.get("total", 0),
        current_file=job.get("current_file"),
    )


@router.get("/result/{job_id}")
def get_result(job_id: str) -> ResultResponse:
    job = job_repository.get_job(JobId(job_id))

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job_status = job.get("status", "pending")
    if job_status not in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED, detail=f"Job is still {job_status}. Please wait for completion."
        )

    results = job.get("results")
    if results is None:
        results = {}

    return ResultResponse(job_id=job_id, status=job_status, results=results)


@router.delete("/job/{job_id}")
def cancel_job(job_id: str) -> Dict[str, Any]:
    job = job_repository.get_job(JobId(job_id))

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    with active_services_lock:
        if job_id in active_services:
            service = active_services[job_id]
            service._worker_pool.stop()
            del active_services[job_id]

    job_repository.delete_job(JobId(job_id))

    return {"status": "cancelled"}
