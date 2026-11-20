from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    url: str
    created_at: datetime
    criticality: str


class ServiceCreate(BaseModel):
    name: str
    description: str
    url: str
    criticality: Literal["low", "medium", "high"] = "medium"


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str


class HealthCheckCreate(BaseModel):
    is_up: bool
    response_ms: int | None = None
    message: str | None = None


class HealthCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    checked_at: datetime
    is_up: bool
    response_ms: int | None
    message: str | None


class IncidentCreate(BaseModel):
    title: str
    message: str
    service_ids: list[int] = Field(min_length=1)


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: str
    started_at: datetime
    resolved_at: datetime | None


class IncidentUpdatesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    status: str
    created_at: datetime


class IncidentDetail(IncidentRead):
    updates: list[IncidentUpdatesRead]


class IncidentStatusUpdate(BaseModel):
    status: Literal["investigating", "identified", "monitoring", "resolved"]
    message: str


class UptimeRead(BaseModel):
    service_id: int
    days: int
    total_checks: int
    up_checks: int
    uptime_percent: float | None


class MaintenanceCreate(BaseModel):
    service_id: int
    title: str
    description: str
    started_at: datetime
    ended_at: datetime

    @model_validator(mode="after")
    def check_order(self):
        if self.ended_at <= self.started_at:
            raise ValueError("ended_at must be after started_at")
        return self


class MaintenanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    title: str
    description: str
    started_at: datetime
    ended_at: datetime
