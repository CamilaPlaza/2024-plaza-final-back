from typing import List
from pydantic import BaseModel, Field
from app.models.task import Task

class ShiftEmployee(BaseModel):
    id_employee: str = Field(..., min_length=1)
    id_shift: str = Field(..., min_length=1)
    shift_assignments: List[Task] = Field(default_factory=list)
