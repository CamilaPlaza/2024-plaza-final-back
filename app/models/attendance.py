from pydantic import BaseModel, Field, validator
from typing import Optional
import datetime

class Attendance(BaseModel):
    id_employee: str = Field(..., min_length=1)
    check_in_time: Optional[datetime.datetime] = None
    check_out_time: Optional[datetime.datetime] = None
    shift_id: str = Field(..., min_length=1)
    total_hours: Optional[str] = Field("", pattern=r"^\d+(\.\d{1,2})?$")
    observations: Optional[str] = ""

    @validator('total_hours')
    def total_hours_should_be_string_or_empty(cls, v):
        if v is not None and not isinstance(v, str):
            raise ValueError("Total hours must be a string")
        return v
