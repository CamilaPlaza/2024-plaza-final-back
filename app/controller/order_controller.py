import re
from typing import List
from fastapi import HTTPException
from app.service.order_service import (
    assign_employee_to_order, assign_order_to_table_service, create_order,
    delete_order_items, finalize_order, get_average_per_order_service, get_average_per_person_service, get_months_revenue_service, get_order_by_id, get_all_orders,
    add_items_to_order
)
from app.models.order import Order, OrderItem
from app.service.product_service import product_by_id
from app.service.table_service import get_table_by_id
from app.controller.table_controller import associate_order_with_table_controller
from app.service.user_service import user_by_id as fetch_user_by_id


# ----------------- helpers -----------------

def _parse_float(value: str, field_name: str) -> float:
    try:
        return float(value)
    except Exception:
        raise HTTPException(status_code=400, detail=f"{field_name} must be a number")

def _validate_date(date_str: str):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str or ""):
        raise HTTPException(status_code=400, detail="date must be in 'YYYY-MM-DD' format")

def _validate_time(time_str: str):
    if not re.fullmatch(r"\d{2}:\d{2}", time_str or ""):
        raise HTTPException(status_code=400, detail="time must be in 'HH:mm' format")

def _round2(x: float) -> float:
    return round(x + 1e-9, 2)

# --------------------------------------------
def register_new_order(order: Order):

    if order.status not in ("INACTIVE", "IN PROGRESS"):
        raise HTTPException(status_code=400, detail="status must be 'INACTIVE' or 'IN PROGRESS' on creation")

    if order.status == "IN PROGRESS":
        if order.tableNumber <= 0:
            raise HTTPException(status_code=400, detail="tableNumber must be > 0 when status is IN PROGRESS")


    _validate_date(order.date)
    _validate_time(order.time)

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

    employee_uid = (order.employee or "").strip()
    if employee_uid:
        employee_doc = fetch_user_by_id(employee_uid)
        if isinstance(employee_doc, dict) and "error" in employee_doc:
            if employee_doc["error"] == "User not found":
                raise HTTPException(status_code=404, detail="Employee not found")
            raise HTTPException(status_code=500, detail=employee_doc["error"])

    resp = create_order(order.dict())
    if isinstance(resp, dict) and "error" in resp:
        raise HTTPException(status_code=500, detail=resp["error"])
    return resp


def finalize_order_controller(order_id: str):
    order = get_order_by_id(order_id)
    print(order)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.get("status") != "IN PROGRESS":
        raise HTTPException(status_code=409, detail="Order is not in progress")
    return finalize_order(order_id)

def get_order_controller(order_id: str):
    try:
        response = get_order_by_id(order_id)
        if not response:
            raise HTTPException(status_code=404, detail="Order not found")
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_orders():
    try:
        response = get_all_orders()
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def add_order_items(order_id: str, new_order_items_data: List[dict], total: str):

    existing_order = get_order_by_id(order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if existing_order.get("status") != "IN PROGRESS":
        raise HTTPException(status_code=400, detail="Cannot add items to an order that is not in progress")

    if not isinstance(new_order_items_data, list) or not new_order_items_data:
        raise HTTPException(status_code=400, detail="new_order_items must be a non-empty list")

    new_items = [OrderItem(**item) for item in new_order_items_data]

    computed_total = 0.0
    for item in new_items:
        prod_res = product_by_id(item.product_id)
        if not isinstance(prod_res, dict) or "product" not in prod_res:
            raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")
        prod = prod_res["product"]

        if item.product_name != prod.get("name"):
            raise HTTPException(status_code=400, detail=f"Product name for product ID {item.product_id} does not match")
        if item.product_price != str(prod.get("price")):
            raise HTTPException(status_code=400, detail=f"Product price for product ID {item.product_id} does not match")

        price_f = _parse_float(item.product_price, "product_price")
        computed_total += price_f * item.amount

    declared_total = _parse_float(total, "new_order_total")
    if _round2(declared_total) != _round2(computed_total):
        raise HTTPException(status_code=400, detail="new_order_total does not match orderItems sum")

    return add_items_to_order(order_id, new_items, total)

def delete_order_items_controller(order_id: str, order_items: List[str]):
    existing_order = get_order_by_id(order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if existing_order.get("status") != "IN PROGRESS":
        raise HTTPException(status_code=400, detail="Cannot DELETE items from an order that is not in progress")

    if not isinstance(order_items, list) or not order_items:
        raise HTTPException(status_code=400, detail="order_items must be a non-empty list of product_id")

    return delete_order_items(order_id, order_items)

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

def assign_order_to_table_controller(order_id: str, table_id: int):
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.get("status") != "INACTIVE":
        raise HTTPException(status_code=400, detail="Order status is not INACTIVE")

    table = get_table_by_id(str(table_id))
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if table.get("status") != "FREE":
        raise HTTPException(status_code=400, detail="Table status is not FREE")
    resp = assign_order_to_table_service(order_id, table_id)
    
    resp2 = associate_order_with_table_controller(str(table_id), order_id)
    resp["table"] = resp2
    return resp

def assign_employee_to_order_controller(order_id, uid):
    try:
        order_id = str(order_id)
        uid = str(uid).strip()

        if uid.startswith('"') and uid.endswith('"'):
            uid = uid[1:-1].strip()

        if not uid:
            raise HTTPException(status_code=400, detail="Employee UID is required")

        if not get_order_by_id(order_id):
            raise HTTPException(status_code=404, detail="Order not found")

        user_lookup = fetch_user_by_id(uid)
        if isinstance(user_lookup, dict) and user_lookup.get("error"):
            if user_lookup["error"] == "User not found":
                raise HTTPException(status_code=404, detail="Employee not found")
            raise HTTPException(status_code=500, detail=user_lookup["error"])

        resp = assign_employee_to_order(order_id, uid)
        if isinstance(resp, dict) and resp.get("error"):
            if resp["error"] in ("Order not found", "Employee not found"):
                raise HTTPException(status_code=404, detail=resp["error"])
            raise HTTPException(status_code=500, detail=resp["error"])

        return resp

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))