from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_create_and_get_memory() -> None:
    response = client.post(
        "/v1/memories",
        json={"key": "user_theme_preference", "value": "Prefers markdown"},
    )
    assert response.status_code == 200

    response = client.get("/v1/memories", params={"key": "user_theme_preference"})
    assert response.status_code == 200
    assert response.json()["value"] == "Prefers markdown"


def test_create_and_get_fact() -> None:
    payload = {
        "subject": "database_cluster",
        "fact": "Port 5432 is restricted to internal VPC traffic.",
        "confidence": 1.0,
    }

    response = client.post("/v1/facts/database_cluster", json=payload)
    assert response.status_code == 200

    response = client.get("/v1/facts/database_cluster")
    assert response.status_code == 200
    assert response.json()["fact"] == payload["fact"]


def test_create_and_get_anti_pattern() -> None:
    payload = {
        "mistake_trigger": "retry_loop_on_422",
        "consequence": "Agent must halt and request schema correction.",
    }

    response = client.post("/v1/anti-patterns", json=payload)
    assert response.status_code == 200

    response = client.get("/v1/anti-patterns", params={"key": payload["mistake_trigger"]})
    assert response.status_code == 200
    assert response.json()["value"] == payload["consequence"]


def test_task_transitions_from_pending_to_completed() -> None:
    pending = {
        "task_id": "task_001",
        "description": "Scrape API documentation endpoints.",
        "status": "pending",
    }
    completed = {**pending, "status": "completed"}

    response = client.post("/v1/tasks/task_001", json=pending)
    assert response.status_code == 200

    response = client.put("/v1/tasks/task_001", json=completed)
    assert response.status_code == 200

    response = client.get("/v1/tasks/task_001")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_status_upsert_and_get() -> None:
    payload = {
        "agent_id": "coder_agent_prime",
        "current_state": "executing_task_001",
        "last_heartbeat": "2026-05-25T16:00:00Z",
    }

    response = client.put("/v1/status/coder_agent_prime", json=payload)
    assert response.status_code == 200

    response = client.get("/v1/status/coder_agent_prime")
    assert response.status_code == 200
    assert response.json()["current_state"] == "executing_task_001"


def test_invalid_schema_returns_422() -> None:
    response = client.post("/v1/facts/database_cluster", json={"subject": "database_cluster"})
    assert response.status_code == 422
