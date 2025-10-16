from fastapi import APIRouter, Depends
from app.models.product import Product
from app.dependencies import verify_token
from app.controller.product_controller import (
    register_new_product, get_products, update_product_price,
    update_product_description, delete_product_by_id, get_product_by_id,
    update_product_categories, check_product_in_in_progress_orders_controller, 
    lower_stock_controller, update_stock_controller
)

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/register")
async def register_product(product: Product, user_data=Depends(verify_token)):
    return register_new_product(product)

@router.get("/getAll")
async def products(user_data=Depends(verify_token)):
    return get_products()

@router.get("/{product_id}")
async def get_product(product_id: str, user_data=Depends(verify_token)):
    return get_product_by_id(product_id)

@router.put("/updatePriceByID/{product_id}/{new_price}")
async def update_price(product_id: str, new_price: str, user_data=Depends(verify_token)):
    return update_product_price(product_id, new_price)

@router.put("/updateDescriptionByID/{product_id}/{new_description}")
async def update_description(product_id: str, new_description: str, user_data=Depends(verify_token)):
    return update_product_description(product_id, new_description)

@router.put("/updateCategoriesByID/{product_id}/{new_category}")
async def update_categories(product_id: str, new_category: str, user_data=Depends(verify_token)):
    return update_product_categories(product_id, new_category)

@router.delete("/deleteByID/{product_id}")
async def delete_product(product_id: str, user_data=Depends(verify_token)):
    return delete_product_by_id(product_id)

@router.put("/updateStockByID/{product_id}/{stock}")
async def update_stock(product_id: str, stock: str, user_data=Depends(verify_token)):
    return update_stock_controller(product_id, stock)

@router.put("/lowerStockByID/{product_id}/{stock}")
async def lower_stock(product_id: str, stock: str, user_data=Depends(verify_token)):
    return lower_stock_controller(product_id, stock)

@router.get("/check-in-progress")
async def check_product_in_orders(user_data=Depends(verify_token)):
    return check_product_in_in_progress_orders_controller()
