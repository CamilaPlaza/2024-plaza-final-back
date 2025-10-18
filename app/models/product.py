from typing import Any
from pydantic import BaseModel, Field, constr

class Product(BaseModel):
    id: int = Field(default=None)
    name: str = Field(min_length=2, max_length=80)
    price: str
    description: str = Field(min_length=1, max_length=400)
    category: str = Field(min_length=1, max_length=120)
    calories: float = Field(ge=0)
    cost: Any
    imageUrl: str
    stock: str = Field(pattern=r"^\d+$")