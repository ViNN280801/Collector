from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def test_data_dir(temp_dir: Path) -> Path:
    data_dir = temp_dir / "test_data"
    data_dir.mkdir()

    for i in range(5):
        (data_dir / f"file{i}.log").write_text(f"content {i}")

    return data_dir


@pytest.mark.integration
class TestAPICollect:
    def test_post_collect_success(self, api_client: TestClient, test_data_dir: Path, temp_dir: Path) -> None:
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        response = api_client.post(
            "/api/v1/collect",
            json={
                "source_paths": [str(test_data_dir)],
                "target_path": str(target_dir),
                "patterns": [{"pattern": "*.log", "pattern_type": "glob"}],
                "operation_mode": "copy",
                "collect_system_info": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"

    def test_post_collect_with_regex_pattern(self, api_client: TestClient, test_data_dir: Path, temp_dir: Path) -> None:
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        response = api_client.post(
            "/api/v1/collect",
            json={
                "source_paths": [str(test_data_dir)],
                "target_path": str(target_dir),
                "patterns": [{"pattern": "file[0-2]\\.log", "pattern_type": "regex"}],
                "operation_mode": "copy",
                "collect_system_info": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_post_collect_invalid_request(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/api/v1/collect",
            json={
                "source_paths": [],
                "target_path": "/tmp/target",
            },
        )

        assert response.status_code == 422

    def test_post_collect_missing_fields(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/api/v1/collect",
            json={},
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestAPIProgress:
    def test_get_progress_not_found(self, api_client: TestClient) -> None:
        response = api_client.get("/api/v1/progress/nonexistent-job-id")

        assert response.status_code == 404

    def test_get_progress_success(self, api_client: TestClient, test_data_dir: Path, temp_dir: Path) -> None:
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        collect_response = api_client.post(
            "/api/v1/collect",
            json={
                "source_paths": [str(test_data_dir)],
                "target_path": str(target_dir),
                "patterns": [{"pattern": "*.log", "pattern_type": "glob"}],
                "operation_mode": "copy",
                "collect_system_info": False,
            },
        )

        job_id = collect_response.json()["job_id"]

        time.sleep(0.5)

        progress_response = api_client.get(f"/api/v1/progress/{job_id}")

        assert progress_response.status_code == 200
        data = progress_response.json()
        assert data["job_id"] == job_id
        assert "percentage" in data
        assert "current" in data
        assert "total" in data
        assert data["total"] == 5


@pytest.mark.integration
class TestAPIResult:
    def test_get_result_not_found(self, api_client: TestClient) -> None:
        response = api_client.get("/api/v1/result/nonexistent-job-id")

        assert response.status_code == 404

    def test_get_result_success(self, api_client: TestClient, test_data_dir: Path, temp_dir: Path) -> None:
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        collect_response = api_client.post(
            "/api/v1/collect",
            json={
                "source_paths": [str(test_data_dir)],
                "target_path": str(target_dir),
                "patterns": [{"pattern": "*.log", "pattern_type": "glob"}],
                "operation_mode": "copy",
                "collect_system_info": False,
            },
        )

        job_id = collect_response.json()["job_id"]

        max_wait = 10.0
        wait_time = 0.0
        while wait_time < max_wait:
            result_response = api_client.get(f"/api/v1/result/{job_id}")
            if result_response.status_code == 200:
                data = result_response.json()
                if data.get("status") == "completed":
                    assert data["job_id"] == job_id
                    assert "results" in data
                    assert data["results"]["total_files"] == 5
                    return
            elif result_response.status_code == 202:
                time.sleep(0.5)
                wait_time = wait_time + 0.5
                continue
            else:
                break
            time.sleep(0.5)
            wait_time = wait_time + 0.5

        pytest.fail("Job did not complete within timeout")

        pytest.fail("Job did not complete in time")


@pytest.mark.integration
class TestAPICancel:
    def test_delete_job_not_found(self, api_client: TestClient) -> None:
        response = api_client.delete("/api/v1/job/nonexistent-job-id")

        assert response.status_code == 404

    def test_delete_job_success(self, api_client: TestClient, test_data_dir: Path, temp_dir: Path) -> None:
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        collect_response = api_client.post(
            "/api/v1/collect",
            json={
                "source_paths": [str(test_data_dir)],
                "target_path": str(target_dir),
                "patterns": [{"pattern": "*.log", "pattern_type": "glob"}],
                "operation_mode": "copy",
                "collect_system_info": False,
            },
        )

        job_id = collect_response.json()["job_id"]

        cancel_response = api_client.delete(f"/api/v1/job/{job_id}")

        assert cancel_response.status_code == 200
        data = cancel_response.json()
        assert data["status"] == "cancelled"

        result_response = api_client.get(f"/api/v1/result/{job_id}")
        assert result_response.status_code == 404


@pytest.mark.integration
class TestAPIRateLimiting:
    def test_rate_limiting(self, api_client: TestClient, test_data_dir: Path, temp_dir: Path) -> None:
        target_dir = temp_dir / "target"
        target_dir.mkdir()

        for i in range(105):
            response = api_client.post(
                "/api/v1/collect",
                json={
                    "source_paths": [str(test_data_dir)],
                    "target_path": str(target_dir),
                    "patterns": [{"pattern": "*.log", "pattern_type": "glob"}],
                    "operation_mode": "copy",
                    "collect_system_info": False,
                },
            )

            if i >= 100:
                assert response.status_code == 429
            else:
                assert response.status_code in (200, 429)
