from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    url: str
    created_at: datetime


class ServiceCreate(BaseModel):
    name: str
    description: str
    url: str


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
