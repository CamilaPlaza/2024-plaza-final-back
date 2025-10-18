from pydantic import BaseModel

class Table(BaseModel):
    status: str
    capacity: int
    order_id: int
