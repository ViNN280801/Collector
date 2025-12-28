from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PCInfoConfigModel(BaseModel):
    collect_os_info: bool = Field(default=True)
    collect_cpu_info: bool = Field(default=True)
    collect_ram_info: bool = Field(default=True)
    collect_disk_info: bool = Field(default=True)
    collect_network_info: bool = Field(default=False)
    collect_env_vars: bool = Field(default=False)
    collect_python_info: bool = Field(default=True)
    collect_process_info: bool = Field(default=False)


class EmailConfigExtended(BaseModel):
    smtp_host: str
    smtp_port: int = Field(ge=1, le=65535, default=587)
    username: str
    password: str
    from_email: str
    to_email: str
    use_tls: bool = Field(default=True)
    use_ssl: bool = Field(default=False)
    timeout: int = Field(ge=1, le=300, default=30)
    max_attachment_size_mb: int = Field(ge=1, le=100, default=25)


class JobListResponse(BaseModel):
    jobs: List[Dict[str, Any]]
    total: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    percentage: float = Field(ge=0.0, le=100.0)
    current: int
    total: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
