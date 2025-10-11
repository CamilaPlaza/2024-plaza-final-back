# app/controller/attendance_controller.py
from typing import Optional
from fastapi import HTTPException
from app.service.attendance_service import (
    create_attendance_record,
    get_today_attendance_data,
    has_any_attendance_today,
    update_attendance_checkout,
    find_open_attendance_for_today,
    make_checkin_preview,
    apply_tip_for_order,
)

def register_attendance_check_in(employee_id: str, shift_id: str, observations: Optional[str] = None):
    if not employee_id.strip() or not shift_id.strip():
        raise HTTPException(status_code=400, detail="Missing required data")
    if has_any_attendance_today(employee_id):
        raise HTTPException(status_code=409, detail="Attendance already completed today")
    existing = find_open_attendance_for_today(employee_id)
    if existing:
        return {"created": False, "id": existing if isinstance(existing, str) else existing.get("id")}
    created = create_attendance_record(employee_id, shift_id, observations)
    return {"created": True, "id": created["id"]}

def register_attendance_check_out(attendance_id: str):
    if not attendance_id.strip():
        raise HTTPException(status_code=400, detail="Missing attendance ID")
    return update_attendance_checkout(attendance_id)

def get_open_attendance_controller(employee_id: str):
    found = find_open_attendance_for_today(employee_id)
    if found:
        attendance_id = found["id"] if isinstance(found, dict) else found
        return {"open": True, "attendance_id": attendance_id}
    return {"open": False}

def get_checkin_preview_controller(employee_id: str, shift_id: str):
    return make_checkin_preview(employee_id, shift_id)

def get_today_attendance_controller(employee_id: str):
    data = get_today_attendance_data(employee_id)
    return data or {}

def apply_tip_controller(order_id: str, mode: str, value: float):
    return apply_tip_for_order(order_id, mode, value)
