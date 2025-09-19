from pydantic import BaseModel, Field
from typing import Literal, Optional

ServerStatus = Literal["PENDING", "IN_PROGRESS", "COMPLETED"]

class Task(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    status: ServerStatus = "PENDING"

    tag: Optional[str] = None
    start_at: Optional[str] = None
    due_at: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
