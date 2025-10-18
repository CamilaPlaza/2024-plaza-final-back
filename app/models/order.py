from typing import List, Literal, Optional
from app.models.order_item import OrderItem
from pydantic import BaseModel, Field

class Order(BaseModel):
    status: Optional[Literal["INACTIVE","IN PROGRESS","FINALIZED"]] = None
    amountOfPeople: int = Field(ge=0)
    tableNumber: int = Field(ge=0)
    date: str
    time: str
    total: str
    orderItems: List[OrderItem]
    employee: Optional[str] = None