from typing import List
from pydantic import BaseModel, Field

class ShiftEmployee(BaseModel):
    id_employee: str = Field(..., min_length=1)
    id_shift: str = Field(..., min_length=1)
    assigned_tasks: List[str]