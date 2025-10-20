# order_router.py
from fastapi import APIRouter, Depends, Query, HTTPException, Header, Request
from typing import Any, Dict, List, Optional
from app.models.order import Order
from app.dependencies import verify_token
from app.controller.order_controller import (
    assign_employee_to_order_controller, assign_order_to_table_controller,
    delete_order_items_controller, register_new_order_controller, finalize_order_controller,
    get_orders_controller, get_order_controller, add_order_items_controller,
    register_new_order_public_controller
)
from app.controller.product_controller import check_product_in_in_progress_orders_controller

router = APIRouter(prefix="/orders", tags=["Orders"])

def _uid_from(user_data: dict) -> str:
    return (user_data.get("uid") or user_data.get("user_id") or user_data.get("sub") or "").strip()

def _roles_from(user_data: dict):
    roles = user_data.get("roles") or user_data.get("role") or []
    if isinstance(roles, str):
        roles = [roles]
    return [str(r) for r in roles]

@router.post("/register")
async def register_order(order: Order, request: Request):
    status = (order.status or "").strip().upper()
    if status == "INACTIVE":
        return register_new_order_public_controller(order)

    auth = (request.headers.get("authorization") or "").strip()
    low = auth.lower()
    if not auth or low in ("bearer", "bearer null", "bearer undefined"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_data = verify_token(authorization=auth)

    uid = _uid_from(user_data)
    roles = _roles_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return register_new_order_controller(order, uid, roles)

@router.put("/order-items/{order_id}")
async def update_order_items(order_id: str, body: Dict[str, Any], user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    roles = _roles_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    new_order_items = body.get("new_order_items", [])
    total = body.get("new_order_total", "")
    return add_order_items_controller(order_id, new_order_items, total, uid, roles)

@router.get("/{order_id}")
async def get_order(order_id: str, user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    roles = _roles_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return get_order_controller(order_id, uid, roles)

@router.get("")
async def orders(user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    roles = _roles_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return get_orders_controller(uid, roles)

@router.put("/finalize/{order_id}")
async def finalize_order(order_id: str, user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    roles = _roles_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return finalize_order_controller(order_id, uid, roles)

@router.put("/assign-table/{order_id}/{table_id}")
async def assign_order_to_table(order_id: str, table_id: int, user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    roles = _roles_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return assign_order_to_table_controller(order_id, table_id, uid, roles)

@router.delete("/delete-order-item/{order_id}")
async def delete_order_item(order_id: str, order_items: Optional[List[str]] = Query(None), user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    roles = _roles_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return delete_order_items_controller(order_id, order_items or [], uid, roles)

@router.put("/assign-order-employee/{orderId}/{uid}")
async def assign_employee_to_order(orderId: str, uid: str, user_data=Depends(verify_token)):
    actor_uid = _uid_from(user_data)
    roles = _roles_from(user_data)
    if not actor_uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return assign_employee_to_order_controller(orderId, uid, actor_uid, roles)

@router.get("/products")
async def check_product_in_in_progress_orders(user_data=Depends(verify_token)):
    return check_product_in_in_progress_orders_controller()
