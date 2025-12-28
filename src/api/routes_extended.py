from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from ..types import JobId
from .models_extended import JobListResponse, JobStatusResponse
from .routes import job_repository

router_extended = APIRouter(prefix="/api/v1")


@router_extended.get("/jobs")
def list_jobs() -> JobListResponse:
    all_jobs = job_repository.get_all_jobs()
    return JobListResponse(jobs=all_jobs, total=len(all_jobs))


@router_extended.get("/status/{job_id}")
def get_job_status(job_id: str) -> JobStatusResponse:
    job = job_repository.get_job(JobId(job_id))

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return JobStatusResponse(
        job_id=job_id,
        status=job.get("status", "pending"),
        percentage=job.get("percentage", 0.0),
        current=job.get("current", 0),
        total=job.get("total", 0),
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        error=job.get("error"),
    )


@router_extended.get("/health")
def health_check() -> Dict[str, Any]:
    return {"status": "healthy", "service": "universal-log-collector", "version": "2.0"}


@router_extended.get("/metrics")
def get_metrics() -> Dict[str, Any]:
    all_jobs = job_repository.get_all_jobs()

    total_jobs = len(all_jobs)
    completed_jobs = sum(1 for j in all_jobs if j.get("status") == "completed")
    failed_jobs = sum(1 for j in all_jobs if j.get("status") == "failed")
    pending_jobs = sum(1 for j in all_jobs if j.get("status") == "pending")

    total_files_processed = sum(j.get("current", 0) for j in all_jobs if j.get("status") == "completed")

    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "pending_jobs": pending_jobs,
        "total_files_processed": total_files_processed,
    }
