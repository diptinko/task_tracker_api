from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

class TaskBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, examples=["Написать фичу"])
    description: Optional[str] = Field(None, max_length=500, examples=["Реализовать фичу по ТЗ"])
    assignee: str = Field(..., examples=["Иван Иванов"])

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee: Optional[str] = None
    status: Optional[TaskStatus] = None

class TaskRead(TaskBase):
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)