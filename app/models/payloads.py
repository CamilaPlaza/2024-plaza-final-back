from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.task import Task

class CreateTaskPayload(BaseModel):
    id_employee: str = Field(..., min_length=1)
    id_shift: str = Field(..., min_length=1)
    task: Task  # puede venir sin id/created_at/created_by; status opcional

class AssignTasksPayload(BaseModel):
    id_employee: str = Field(..., min_length=1)
    id_shift: str = Field(..., min_length=1)
    shift_assignments: List[Task] = Field(default_factory=list)
