from __future__ import annotations

from typing import Any, Dict

COLLECTION_REQUEST_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["target_path", "source_paths"],
    "properties": {
        "target_path": {"type": "string", "minLength": 1},
        "source_paths": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1,
        },
        "patterns": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "minLength": 1},
                    "pattern_type": {"type": "string", "enum": ["regex", "glob"]},
                },
                "required": ["pattern"],
            },
        },
        "pattern_type": {"type": "string", "enum": ["regex", "glob"], "default": "glob"},
        "operation_mode": {
            "type": "string",
            "enum": ["copy", "move", "move_remove"],
            "default": "copy",
        },
        "create_archive": {"type": "boolean", "default": False},
        "archive_format": {"type": "string", "default": "zip"},
        "collect_system_info": {"type": "boolean", "default": True},
        "email_config": {
            "type": "object",
            "properties": {
                "smtp_host": {"type": "string"},
                "smtp_port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "from_email": {"type": "string", "format": "email"},
                "to_email": {"type": "string", "format": "email"},
            },
        },
    },
}

PROGRESS_RESPONSE_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["job_id", "percentage", "current", "total"],
    "properties": {
        "job_id": {"type": "string"},
        "percentage": {"type": "number", "minimum": 0.0, "maximum": 100.0},
        "current": {"type": "integer", "minimum": 0},
        "total": {"type": "integer", "minimum": 0},
        "current_file": {"type": ["string", "null"]},
    },
}

RESULT_RESPONSE_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["job_id", "status", "results"],
    "properties": {
        "job_id": {"type": "string"},
        "status": {"type": "string", "enum": ["completed", "failed", "cancelled"]},
        "results": {"type": "object"},
    },
}


def validate_request(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    try:
        from jsonschema import validate as jsonschema_validate

        jsonschema_validate(instance=data, schema=schema)
        return True
    except Exception:
        return False
