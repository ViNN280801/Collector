from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class PatternConfigModel(BaseModel):
    pattern: str = Field(..., min_length=1)
    pattern_type: str = Field(default="glob")

    @field_validator("pattern_type")
    @classmethod
    def validate_pattern_type(cls, v: str) -> str:
        if v not in ("regex", "glob"):
            raise ValueError("pattern_type must be 'regex' or 'glob'")
        return v


class EmailConfigModel(BaseModel):
    smtp_host: str
    smtp_port: int = Field(ge=1, le=65535)
    username: str
    password: str
    from_email: str
    to_email: str


class CollectionRequest(BaseModel):
    target_path: str = Field(..., min_length=1)
    source_paths: List[str] = Field(..., min_length=1)
    patterns: Optional[List[PatternConfigModel]] = None
    pattern_type: str = Field(default="glob")
    operation_mode: str = Field(default="copy")
    create_archive: bool = Field(default=False)
    archive_format: str = Field(default="zip")
    archive_compression: Optional[str] = Field(default=None)
    collect_system_info: bool = Field(default=True)
    email_config: Optional[EmailConfigModel] = None

    @field_validator("pattern_type")
    @classmethod
    def validate_pattern_type(cls, v: str) -> str:
        if v not in ("regex", "glob"):
            raise ValueError("pattern_type must be 'regex' or 'glob'")
        return v

    @field_validator("operation_mode")
    @classmethod
    def validate_operation_mode(cls, v: str) -> str:
        if v not in ("copy", "move", "move_remove"):
            raise ValueError("operation_mode must be 'copy', 'move', or 'move_remove'")
        return v

    @field_validator("archive_format")
    @classmethod
    def validate_archive_format(cls, v: str) -> str:
        if v not in ("zip", "tar", "7z"):
            raise ValueError("archive_format must be 'zip', 'tar', or '7z'")
        return v


class ProgressResponse(BaseModel):
    job_id: str
    percentage: float = Field(ge=0.0, le=100.0)
    current: int = Field(ge=0)
    total: int = Field(ge=0)
    current_file: Optional[str] = None


class ResultResponse(BaseModel):
    job_id: str
    status: str
    results: Dict[str, Any]

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("completed", "failed", "cancelled"):
            raise ValueError("status must be 'completed', 'failed', or 'cancelled'")
        return v
