from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MemorySchema(BaseModel):
    key: str = Field(min_length=1)
    value: str


class FactSchema(BaseModel):
    subject: str = Field(min_length=1)
    fact: str
    confidence: float = Field(ge=0.0, le=1.0)


class PatternSchema(BaseModel):
    trigger: str = Field(min_length=1)
    successful_action: str


class AntiPatternSchema(BaseModel):
    mistake_trigger: str = Field(min_length=1)
    consequence: str


class TaskSchema(BaseModel):
    task_id: str = Field(min_length=1)
    description: str
    status: Literal["pending", "in_progress", "completed", "failed"]


class StatusSchema(BaseModel):
    agent_id: str = Field(min_length=1)
    current_state: str
    last_heartbeat: datetime
