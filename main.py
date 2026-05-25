import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import ValidationError

from database import delete_value, get_value, init_db, upsert_value
from schemas import (
    AntiPatternSchema,
    FactSchema,
    MemorySchema,
    PatternSchema,
    StatusSchema,
    TaskSchema,
)

app = FastAPI(title="parameter-mem")
DB_PATH = os.getenv("PARAMETER_MEM_DB", "parameter_mem.db")
KV_CATEGORIES = {"memories", "patterns", "anti-patterns"}


@app.on_event("startup")
def startup() -> None:
    init_db(DB_PATH)


def _ensure_path_matches(path_value: str, body_value: str, field: str) -> None:
    if path_value != body_value:
        raise HTTPException(status_code=400, detail=f"{field} in path and body must match")


@app.post("/v1/{category}")
def create_kv(category: str, payload: dict[str, Any]) -> dict[str, Any]:
    if category not in KV_CATEGORIES:
        raise HTTPException(status_code=404, detail="Unsupported category")

    try:
        if category == "memories":
            validated = MemorySchema.model_validate(payload)
            key = validated.key
            value: Any = validated.value
        elif category == "patterns":
            validated = PatternSchema.model_validate(payload)
            key = validated.trigger
            value = validated.successful_action
        else:
            validated = AntiPatternSchema.model_validate(payload)
            key = validated.mistake_trigger
            value = validated.consequence
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    upsert_value(category, key, value, DB_PATH)
    return {"category": category, "key": key, "value": value}


@app.get("/v1/{category}")
def get_kv(category: str, key: str = Query(..., min_length=1)) -> dict[str, Any]:
    if category not in KV_CATEGORIES:
        raise HTTPException(status_code=404, detail="Unsupported category")

    value = get_value(category, key, DB_PATH)
    if value is None:
        raise HTTPException(status_code=404, detail="Not found")

    return {"category": category, "key": key, "value": value}


@app.delete("/v1/{category}")
def delete_kv(category: str, key: str = Query(..., min_length=1)) -> dict[str, str]:
    if category not in KV_CATEGORIES:
        raise HTTPException(status_code=404, detail="Unsupported category")

    deleted = delete_value(category, key, DB_PATH)
    if not deleted:
        raise HTTPException(status_code=404, detail="Not found")

    return {"status": "deleted"}


@app.post("/v1/facts/{subject}")
def create_fact(subject: str, payload: FactSchema) -> FactSchema:
    _ensure_path_matches(subject, payload.subject, "subject")
    upsert_value("facts", subject, payload.model_dump(mode="json"), DB_PATH)
    return payload


@app.get("/v1/facts/{subject}")
def get_fact(subject: str) -> FactSchema:
    value = get_value("facts", subject, DB_PATH)
    if value is None:
        raise HTTPException(status_code=404, detail="Not found")
    return FactSchema.model_validate(value)


@app.post("/v1/tasks/{task_id}")
def create_task(task_id: str, payload: TaskSchema) -> TaskSchema:
    return _upsert_task(task_id, payload)


@app.put("/v1/tasks/{task_id}")
def update_task(task_id: str, payload: TaskSchema) -> TaskSchema:
    return _upsert_task(task_id, payload)


def _upsert_task(task_id: str, payload: TaskSchema) -> TaskSchema:
    _ensure_path_matches(task_id, payload.task_id, "task_id")
    upsert_value("tasks", task_id, payload.model_dump(mode="json"), DB_PATH)
    return payload


@app.get("/v1/tasks/{task_id}")
def get_task(task_id: str) -> TaskSchema:
    value = get_value("tasks", task_id, DB_PATH)
    if value is None:
        raise HTTPException(status_code=404, detail="Not found")
    return TaskSchema.model_validate(value)


@app.put("/v1/status/{agent_id}")
def upsert_status(agent_id: str, payload: StatusSchema) -> StatusSchema:
    _ensure_path_matches(agent_id, payload.agent_id, "agent_id")
    upsert_value("status", agent_id, payload.model_dump(mode="json"), DB_PATH)
    return payload


@app.get("/v1/status/{agent_id}")
def get_status(agent_id: str) -> StatusSchema:
    value = get_value("status", agent_id, DB_PATH)
    if value is None:
        raise HTTPException(status_code=404, detail="Not found")
    return StatusSchema.model_validate(value)
