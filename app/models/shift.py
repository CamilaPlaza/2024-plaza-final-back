from pydantic import BaseModel, Field, validator
from typing import Literal
from datetime import datetime

class Shift(BaseModel):
    start_time: str
    end_time: str
    status: Literal["PENDING", "ACTIVE", "FINISHED"]
    name: str = Field(..., min_length=1)

    @validator("start_time", "end_time")
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M")  # ej: "2025-06-26 14:00"
        except ValueError:
            raise ValueError("Time must be in format YYYY-MM-DD HH:MM")
        return v

    @validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v
