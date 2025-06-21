from fastapi import APIRouter, Depends
from typing import Any, Dict, List
from app.models.order import Order
from app.dependencies import verify_token
from app.controller.order_controller import (
    assign_employee_to_order_controller, assign_order_to_table_controller,
    delete_order_items_controller, register_new_order, finalize_order_controller, get_orders,
    get_order_controller, add_order_items
)
from app.controller.product_controller import check_product_in_in_progress_orders_controller

router = APIRouter()

@router.post("/register")
async def register_order(order: Order):
    return register_new_order(order)

@router.put("/order-items/{order_id}")
async def update_order_items(order_id: str, body: Dict[str, Any], user_data=Depends(verify_token)):
    new_order_items = body.get("new_order_items", [])
    total = body.get("new_order_total", "")
    return add_order_items(order_id, new_order_items, total)

@router.get("/{order_id}")
async def get_order(order_id: str, user_data=Depends(verify_token)):
    return get_order_controller(order_id)

@router.get("/")
async def orders(user_data=Depends(verify_token)):
    return get_orders()

@router.put("/finalize/{order_id}")
async def finalize_order(order_id: str, user_data=Depends(verify_token)):
    return finalize_order_controller(order_id)

@router.put("/assign-table/{order_id}/{table_id}")
async def assign_order_to_table(order_id: str, table_id: int, user_data=Depends(verify_token)):
    return assign_order_to_table_controller(order_id, table_id)

@router.delete("/delete-order-item/{order_id}")
async def delete_order_item(order_id: str, order_items: List[str], user_data=Depends(verify_token)):
    return delete_order_items_controller(order_id, order_items)

@router.put("/assign-order-employee/{orderId}/{uid}")
async def assign_employee_to_order(orderId: int, uid: str, user_data=Depends(verify_token)):
    return assign_employee_to_order_controller(orderId, uid)

@router.get("/products")
async def check_product_in_in_progress_orders(user_data=Depends(verify_token)):
    return check_product_in_in_progress_orders_controller()
