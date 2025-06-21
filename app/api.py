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
    charts_router
)

router = APIRouter()

router.include_router(auth_router.router)
router.include_router(user_router.router, prefix="/users")
router.include_router(product_router.router, prefix="/products")
router.include_router(category_router.router, prefix="/categories")
router.include_router(table_router.router, prefix="/tables")
router.include_router(order_router.router, prefix="/orders")
router.include_router(calories_router.router, prefix="/calories")
router.include_router(goal_router.router, prefix="/goals")
router.include_router(charts_router.router, prefix="/charts")
