from pydantic import BaseModel, Field, validator
from typing import Literal
from datetime import datetime

class Shift(BaseModel):
    start_time: str
    end_time: str
    status: Literal["PENDING", "ACTIVE", "FINISHED"]
    name: str = Field(..., min_length=1)

    @validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v
