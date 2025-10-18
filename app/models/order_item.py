from pydantic import BaseModel, Field

class OrderItem(BaseModel):
    product_id: str = Field(min_length=1)
    product_name: str = Field(min_length=1)
    product_price: str
    amount: int = Field(gt=0)
