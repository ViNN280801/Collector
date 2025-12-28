from __future__ import annotations

import uuid
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Protocol
else:
    try:
        from typing import Protocol
    except ImportError:
        from typing_extensions import Protocol

from ..types import JobId


class JobRepository(Protocol):
    def create_job(self, data: Dict[str, Any]) -> JobId: ...

    def get_job(self, job_id: JobId) -> Optional[Dict[str, Any]]: ...

    def update_job(self, job_id: JobId, updates: Dict[str, Any]) -> None: ...

    def delete_job(self, job_id: JobId) -> None: ...

    def get_all_jobs(self) -> List[Dict[str, Any]]: ...


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock: threading.Lock = threading.Lock()

    def create_job(self, data: Dict[str, Any]) -> JobId:
        job_id = JobId(str(uuid.uuid4()))
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": "pending",
                "percentage": 0.0,
                "current": 0,
                "total": 0,
                "current_file": None,
                "results": None,
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "error": None,
                **data,
            }
        return job_id

    def get_job(self, job_id: JobId) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(self, job_id: JobId, updates: Dict[str, Any]) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(updates)

    def delete_job(self, job_id: JobId) -> None:
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._jobs.values())
