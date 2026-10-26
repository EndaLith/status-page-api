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
