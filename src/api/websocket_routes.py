from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from .routes import job_repository
from ..types import JobId

router = APIRouter(prefix="/api/v1")
active_connections: Dict[str, Set[WebSocket]] = {}
connections_lock = asyncio.Lock()


async def broadcast_progress(job_id: str, progress_data: Dict[str, Any]) -> None:
    async with connections_lock:
        if job_id in active_connections:
            disconnected = set()
            for connection in active_connections[job_id]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(progress_data)
                    else:
                        disconnected.add(connection)
                except Exception:
                    disconnected.add(connection)

            active_connections[job_id] -= disconnected
            if not active_connections[job_id]:
                del active_connections[job_id]


@router.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()

    job_id_typed = JobId(job_id)

    async with connections_lock:
        if job_id not in active_connections:
            active_connections[job_id] = set()
        active_connections[job_id].add(websocket)

    job = job_repository.get_job(job_id_typed)
    if job:
        initial_data = {
            "job_id": job_id,
            "percentage": job.get("percentage", 0.0),
            "current": job.get("current", 0),
            "total": job.get("total", 0),
            "current_file": job.get("current_file"),
            "status": job.get("status", "pending"),
        }
        try:
            await websocket.send_json(initial_data)
        except Exception:
            pass

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        async with connections_lock:
            if job_id in active_connections:
                active_connections[job_id].discard(websocket)
                if not active_connections[job_id]:
                    del active_connections[job_id]


def setup_websocket_progress_updates() -> None:
    original_update = job_repository.update_job

    def update_job_with_websocket(job_id: JobId, updates: Dict[str, Any]) -> None:
        original_update(job_id, updates)
        if "percentage" in updates or "current" in updates or "status" in updates:
            job = job_repository.get_job(job_id)
            if job:
                progress_data = {
                    "job_id": str(job_id),
                    "percentage": job.get("percentage", 0.0),
                    "current": job.get("current", 0),
                    "total": job.get("total", 0),
                    "current_file": job.get("current_file"),
                    "status": job.get("status", "pending"),
                }
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(broadcast_progress(str(job_id), progress_data))
                except RuntimeError:
                    pass

    # Use setattr to avoid mypy error about method assignment
    setattr(job_repository, "update_job", update_job_with_websocket)


setup_websocket_progress_updates()
