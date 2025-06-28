from fastapi import APIRouter
from app.routers import (
    auth_router,
    user_router,
    product_router,
    category_router,
    table_router,
    order_router,
    calories_router,
    goal_router,
    charts_router,
    shifts_router, 
    tasks_router, 
    attendance_router
)

router = APIRouter()

router.include_router(auth_router.router)
router.include_router(user_router.router)
router.include_router(product_router.router)
router.include_router(category_router.router)
router.include_router(table_router.router)
router.include_router(order_router.router)
router.include_router(calories_router.router)
router.include_router(goal_router.router)
router.include_router(charts_router.router)
router.include_router(shifts_router.router)
router.include_router(tasks_router.router)
router.include_router(attendance_router.router)