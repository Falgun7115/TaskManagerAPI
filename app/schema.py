from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    """Schema for creating a task."""

    title: str
    description: Optional[str] = None


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status."""

    status: str


class TaskResponse(BaseModel):
    """Schema for task API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
