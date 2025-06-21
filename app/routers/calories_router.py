from fastapi import APIRouter, Depends
from app.dependencies import verify_token
from app.controller.product_controller import add_food_calories, update_stock_controller, lower_stock_controller

router = APIRouter()

@router.put("/add/{product_id}/{calories}")
async def add_calories(product_id: str, calories: float, user_data=Depends(verify_token)):
    return add_food_calories(product_id, calories)
