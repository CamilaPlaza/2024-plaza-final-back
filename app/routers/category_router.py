from fastapi import APIRouter, Depends
from app.models.category import Category
from app.dependencies import verify_token
from app.controller.category_controller import (
    delete_category_controller, get_all_categories,
    get_category_by_id_controller, register_new_category,
    update_category_name_controller, get_category_revenue_controller
)
from app.controller.product_controller import get_products_by_category_controller

router = APIRouter()

@router.get("/")
async def categories():
    return get_all_categories()

@router.post("/register")
async def register_category(category: Category, user_data=Depends(verify_token)):
    return register_new_category(category)

@router.get("/{category_id}")
async def get_category(category_id: str, user_data=Depends(verify_token)):
    return get_category_by_id_controller(category_id)

@router.delete("/{category_id}")
async def delete_category(category_id: str, user_data=Depends(verify_token)):
    return delete_category_controller(category_id)

@router.put("/updateNameByID/{category_id}/{new_name}")
async def update_category_name(category_id: str, new_name: str, user_data=Depends(verify_token)):
    return update_category_name_controller(category_id, new_name)

@router.get("/revenue")
async def get_category_revenue(user_data=Depends(verify_token)):
    return get_category_revenue_controller()

@router.get("/getProductsByCategoryID/{category_id}")
async def get_products_by_category(category_id: str, user_data=Depends(verify_token)):
    return get_products_by_category_controller(category_id)
