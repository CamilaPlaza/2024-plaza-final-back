from fastapi import APIRouter, Depends
from app.dependencies import verify_token
from app.controller.order_controller import get_average_per_order_controller, get_average_per_person_controller, get_months_revenue

router = APIRouter(prefix="/charts", tags=["Charts"])

@router.get("/monthly-revenue")
async def get_monthly_revenue(user_data=Depends(verify_token)):
    return get_months_revenue()

@router.get("/average_per_person/{year}/{month}")
async def get_average_per_person(year: str, month: str, user_data=Depends(verify_token)):
    return get_average_per_person_controller(year, month)

@router.get("/averare_per_order/{year}/{month}")
async def get_average_per_order(year: str, month: str, user_data=Depends(verify_token)):
    return get_average_per_order_controller(year, month)
