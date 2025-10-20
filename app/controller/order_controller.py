import re
from typing import List
from fastapi import HTTPException
from app.service.order_service import (
    assign_employee_to_order_secure, assign_order_to_table_service_secure, create_order,
    delete_order_items_secure, finalize_order_secure, get_average_per_order_service,
    get_average_per_person_service, get_months_revenue_service, get_order_by_id,
    get_all_orders, add_items_to_order_secure
)
from app.models.order import Order, OrderItem
from app.service.product_service import product_by_id
from app.controller.table_controller import associate_order_with_table_controller
from app.service.user_service import user_by_id as fetch_user_by_id
from app.service.attendance_service import find_open_attendance_for_today

def _parse_float(value: str, field_name: str) -> float:
    try:
        return float(value)
    except Exception:
        raise HTTPException(status_code=400, detail=f"{field_name} must be a number")

def _validate_date(date_str: str):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str or ""):
        raise HTTPException(status_code=400, detail="date must be in 'YYYY-MM-DD' format")

def _validate_time(time_str: str):
    """
    Acepta HH:mm o HH:mm:ss (24h). Rechaza otros formatos.
    """
    if not re.fullmatch(r"\d{2}:\d{2}(:\d{2})?", time_str or ""):
        raise HTTPException(status_code=400, detail="time must be in 'HH:mm' format")

def _normalize_time_to_HH_mm(time_str: str) -> str:
    """
    Normaliza 'HH:mm' o 'HH:mm:ss' a 'HH:mm'.
    """
    if not time_str:
        raise HTTPException(status_code=400, detail="time must be in 'HH:mm' format")
    if re.fullmatch(r"\d{2}:\d{2}:\d{2}", time_str):
        return time_str[:5]
    if re.fullmatch(r"\d{2}:\d{2}", time_str):
        return time_str
    raise HTTPException(status_code=400, detail="time must be in 'HH:mm' format")

def _round2(x: float) -> float:
    return round(x + 1e-9, 2)

def _require_checkin(actor_uid: str):
    opened = find_open_attendance_for_today(actor_uid)
    if not opened:
        raise HTTPException(status_code=403, detail="CHECKIN_REQUIRED")

def register_new_order_controller(order: Order, actor_uid: str, actor_roles: list[str]):
    _require_checkin(actor_uid)
    is_admin = "admin" in (actor_roles or [])
    incoming_emp = (order.employee or "").strip()
    if not is_admin and incoming_emp and incoming_emp != actor_uid:
        raise HTTPException(status_code=403, detail="Non-admin can only create orders for themselves")
    target_uid = incoming_emp or actor_uid if is_admin or not incoming_emp else actor_uid

    if order.status not in ("INACTIVE", "IN PROGRESS"):
        raise HTTPException(status_code=400, detail="status must be 'INACTIVE' or 'IN PROGRESS' on creation")
    if order.status == "IN PROGRESS":
        if order.tableNumber <= 0:
            raise HTTPException(status_code=400, detail="tableNumber must be > 0 when status is IN PROGRESS")

    _validate_date(order.date)
    _validate_time(order.time)
    norm_time = _normalize_time_to_HH_mm(order.time)

    if not order.orderItems:
        raise HTTPException(status_code=400, detail="At least one order item is required")

    computed_total = 0.0
    for raw_item in order.orderItems:
        prod_res = product_by_id(raw_item.product_id)
        if not isinstance(prod_res, dict) or "product" not in prod_res:
            raise HTTPException(status_code=404, detail=f"Product with ID {raw_item.product_id} not found")
        prod = prod_res["product"]
        if raw_item.product_name != prod.get("name"):
            raise HTTPException(status_code=400, detail=f"Product name for product ID {raw_item.product_id} does not match")
        db_price_str = str(prod.get("price"))
        if raw_item.product_price != db_price_str:
            raise HTTPException(status_code=400, detail=f"Product price for product ID {raw_item.product_id} does not match")
        item_price = _parse_float(raw_item.product_price, "product_price")
        computed_total += item_price * raw_item.amount

    declared_total = _parse_float(order.total, "total")
    if _round2(declared_total) != _round2(computed_total):
        raise HTTPException(status_code=400, detail="total does not match orderItems sum")

    if target_uid:
        employee_doc = fetch_user_by_id(target_uid)
        if isinstance(employee_doc, dict) and "error" in employee_doc:
            if employee_doc["error"] == "User not found":
                raise HTTPException(status_code=404, detail="Employee not found")
            raise HTTPException(status_code=500, detail=employee_doc["error"])

    data = order.dict()
    data["employee"] = target_uid
    data["time"] = norm_time  # ← guardamos HH:mm normalizado

    resp = create_order(data)
    if isinstance(resp, dict) and "error" in resp:
        raise HTTPException(status_code=500, detail=resp["error"])
    return resp

def register_new_order_public_controller(order: Order):
    if order.status != "INACTIVE":
        raise HTTPException(status_code=400, detail="Public order must have status INACTIVE")

    if (order.tableNumber or 0) != 0:
        raise HTTPException(status_code=400, detail="tableNumber must be 0 for public orders")
    if (order.employee or "").strip():
        raise HTTPException(status_code=400, detail="employee must be empty for public orders")

    _validate_date(order.date)
    _validate_time(order.time)
    norm_time = _normalize_time_to_HH_mm(order.time)

    if not order.orderItems:
        raise HTTPException(status_code=400, detail="At least one order item is required")

    computed_total = 0.0
    for raw_item in order.orderItems:
        prod_res = product_by_id(raw_item.product_id)
        if not isinstance(prod_res, dict) or "product" not in prod_res:
            raise HTTPException(status_code=404, detail=f"Product with ID {raw_item.product_id} not found")
        prod = prod_res["product"]
        if raw_item.product_name != prod.get("name"):
            raise HTTPException(status_code=400, detail=f"Product name for product ID {raw_item.product_id} does not match")
        db_price_str = str(prod.get("price"))
        if raw_item.product_price != db_price_str:
            raise HTTPException(status_code=400, detail=f"Product price for product ID {raw_item.product_id} does not match")

        item_price = _parse_float(raw_item.product_price, "product_price")
        computed_total += item_price * raw_item.amount

    declared_total = _parse_float(order.total, "total")
    if _round2(declared_total) != _round2(computed_total):
        raise HTTPException(status_code=400, detail="total does not match orderItems sum")

    data = order.dict()
    data["status"] = "INACTIVE"
    data["employee"] = ""
    data["tableNumber"] = 0
    data["time"] = norm_time  # ← guardamos HH:mm normalizado

    resp = create_order(data)
    if isinstance(resp, dict) and "error" in resp:
        raise HTTPException(status_code=500, detail=resp["error"])
    return resp

def finalize_order_controller(order_id: str, actor_uid: str, actor_roles: list[str]):
    _require_checkin(actor_uid)
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.get("status") != "IN PROGRESS":
        raise HTTPException(status_code=409, detail="Order is not in progress")
    return finalize_order_secure(order_id, actor_uid, actor_roles)

def get_order_controller(order_id: str, actor_uid: str, actor_roles: list[str]):
    response = get_order_by_id(order_id)
    if not response:
        raise HTTPException(status_code=404, detail="Order not found")
    return response

def get_orders_controller(actor_uid: str, actor_roles: list[str]):
    return get_all_orders()

def add_order_items_controller(order_id: str, new_order_items_data: List[dict], total: str, actor_uid: str, actor_roles: list[str]):
    _require_checkin(actor_uid)
    if not isinstance(new_order_items_data, list) or not new_order_items_data:
        raise HTTPException(status_code=400, detail="new_order_items must be a non-empty list")
    return add_items_to_order_secure(order_id, new_order_items_data, total, actor_uid, actor_roles)

def delete_order_items_controller(order_id: str, order_items: List[str], actor_uid: str, actor_roles: list[str]):
    _require_checkin(actor_uid)
    if not isinstance(order_items, list) or not order_items:
        raise HTTPException(status_code=400, detail="order_items must be a non-empty list of product_id")
    return delete_order_items_secure(order_id, order_items, actor_uid, actor_roles)

def get_months_revenue():
    try:
        response = get_months_revenue_service()
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_average_per_person_controller(year: str, month: str):
    try:
        response = get_average_per_person_service(year, month)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_average_per_order_controller(year: str, month: str):
    try:
        response = get_average_per_order_service(year, month)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def assign_order_to_table_controller(order_id: str, table_id: int, actor_uid: str, actor_roles: list[str]):
    _require_checkin(actor_uid)
    resp = assign_order_to_table_service_secure(order_id, table_id, actor_uid, actor_roles)
    return resp

def assign_employee_to_order_controller(order_id: str, target_uid: str, actor_uid: str, actor_roles: list[str]):
    _require_checkin(actor_uid)
    if not target_uid or not isinstance(target_uid, str):
        raise HTTPException(status_code=400, detail="Employee UID is required")
    return assign_employee_to_order_secure(order_id, target_uid.strip(), actor_uid, actor_roles)
