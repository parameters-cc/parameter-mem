import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any


DEFAULT_DB_PATH = os.getenv("PARAMETER_MEM_DB", "parameter_mem.db")
_thread_local = threading.local()


def _get_thread_connections() -> dict[str, sqlite3.Connection]:
    connections = getattr(_thread_local, "connections", None)
    if connections is None:
        connections = {}
        _thread_local.connections = connections
    return connections


def _connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    normalized_path = os.path.abspath(db_path)
    connections = _get_thread_connections()
    conn = connections.get(normalized_path)
    if conn is None:
        conn = sqlite3.connect(normalized_path)
        conn.row_factory = sqlite3.Row
        connections[normalized_path] = conn
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kv_store (
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                PRIMARY KEY (category, key)
            )
            """
        )


def upsert_value(category: str, key: str, value: Any, db_path: str = DEFAULT_DB_PATH) -> None:
    serialized = json.dumps(value)
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO kv_store (category, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(category, key) DO UPDATE SET
                value=excluded.value,
                updated_at=excluded.updated_at
            """,
            (category, key, serialized, now),
        )


def get_value(category: str, key: str, db_path: str = DEFAULT_DB_PATH) -> Any | None:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT value FROM kv_store WHERE category = ? AND key = ?",
            (category, key),
        ).fetchone()

    if row is None:
        return None

    return json.loads(row["value"])


def delete_value(category: str, key: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    with _connect(db_path) as conn:
        cur = conn.execute(
            "DELETE FROM kv_store WHERE category = ? AND key = ?",
            (category, key),
        )
        return cur.rowcount > 0
