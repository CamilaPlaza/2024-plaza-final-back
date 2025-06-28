from pydantic import BaseModel, Field
from typing import Literal

class Task(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED"] = "PENDING"
