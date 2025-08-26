from pydantic import BaseModel, Field

class Category(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    type: str = "Custom"