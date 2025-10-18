from typing import Dict, Union
from fastapi import HTTPException
from app.service.table_service import (
    associate_order_with_table, clean_table_service, close_table_service,
    get_tables_service, get_table_by_id, update_table_status, create_table
)
from app.service.order_service import get_order_by_id
from app.service.attendance_service import find_open_attendance_for_today

def _uid(user_data: dict) -> str:
    return (user_data.get("uid") or user_data.get("user_id") or user_data.get("sub") or "").strip()

def _require_checkin(user_data: dict):
    uid = _uid(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    opened = find_open_attendance_for_today(uid)
    if not opened:
        raise HTTPException(status_code=403, detail="CHECKIN_REQUIRED")

def get_tables_controller():
    resp = get_tables_service()
    if isinstance(resp, dict) and "error" in resp:
        raise HTTPException(status_code=500, detail=resp["error"])
    return resp

def get_table_by_id_controller(table_id: str):
    table = get_table_by_id(table_id)
    if isinstance(table, dict) and "error" in table:
        raise HTTPException(status_code=500, detail=table["error"])
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return table

def update_table_status_controller(table_id: str, new_status: str):
    resp = update_table_status(table_id, new_status)
    if isinstance(resp, dict) and "error" in resp:
        if resp["error"] == "Table not found":
            raise HTTPException(status_code=404, detail=resp["error"])
        raise HTTPException(status_code=500, detail=resp["error"])
    return resp

def associate_order_with_table_controller(table_id: str, order_id: int, user_data: dict):
    _require_checkin(user_data)
    table = get_table_by_id(table_id)
    if isinstance(table, dict) and "error" in table:
        raise HTTPException(status_code=500, detail=table["error"])
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    current_status = table.get("status")
    if current_status != "FREE":
        raise HTTPException(
            status_code=409,
            detail=f"Table status must be 'FREE' to associate an order (current: '{current_status}')"
        )
    order = get_order_by_id(str(order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    resp = associate_order_with_table(table_id, str(order_id))
    if isinstance(resp, dict) and "error" in resp:
        if resp["error"] == "Table not found":
            raise HTTPException(status_code=404, detail=resp["error"])
        raise HTTPException(status_code=500, detail=resp["error"])
    return resp

def close_table_controller(table_id: str, body: Dict[str, Union[str, int]], user_data: dict):
    _require_checkin(user_data)
    status = body.get("status")
    order_id = body.get("order_id")
    if status != "FINISHED":
        raise HTTPException(status_code=400, detail="Status must be 'FINISHED'")
    if order_id != 0:
        raise HTTPException(status_code=400, detail="Order ID must be 0")
    table = get_table_by_id(table_id)
    if isinstance(table, dict) and "error" in table:
        raise HTTPException(status_code=500, detail=table["error"])
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if int(table.get("order_id", 0)) == 0:
        raise HTTPException(status_code=409, detail="Table has no order to close")
    resp = close_table_service(table_id)
    return resp

def clean_table_controller(table_id: str, body: Dict[str, Union[str, int]], user_data: dict):
    _require_checkin(user_data)
    status = body.get("status")
    order_id = body.get("order_id")
    if status != "FREE":
        raise HTTPException(status_code=400, detail="Status must be 'FREE'")
    if order_id != 0:
        raise HTTPException(status_code=400, detail="Order ID must be 0")
    table = get_table_by_id(table_id)
    if isinstance(table, dict) and "error" in table:
        raise HTTPException(status_code=500, detail=table["error"])
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if table.get("status") != "FINISHED":
        raise HTTPException(
            status_code=409,
            detail=f"Table must be 'FINISHED' to clean (current: '{table.get('status')}')"
        )
    resp = clean_table_service(table_id)
    return resp

def create_table_controller(body: Dict[str, Union[str, int]], user_data: dict):
    _require_checkin(user_data)
    try:
        capacity = body.get("capacity")
        if capacity is None:
            raise HTTPException(status_code=400, detail="Capacidad requerida")
        if not isinstance(capacity, int):
            raise HTTPException(status_code=400, detail="Capacidad debe ser un número entero")
        if capacity < 2 or capacity > 12:
            raise HTTPException(status_code=400, detail="La capacidad debe estar entre 2 y 12")
        table_data = {
            "capacity": capacity,
            "order_id": 0,
            "status": "FREE"
        }
        resp = create_table(table_data)
        if isinstance(resp, dict) and "error" in resp:
            raise HTTPException(status_code=500, detail=resp["error"])
        return {"message": "Mesa creada exitosamente", "id": resp["id"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
