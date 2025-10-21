# app/controller/attendance_controller.py
from typing import Optional, List
from fastapi import HTTPException
from app.service.attendance_service import (
    create_attendance_record,
    get_current_tips_total_service,
    get_today_attendance_data,
    has_any_attendance_today,
    update_attendance_checkout_secure,
    find_open_attendance_for_today,
    make_checkin_preview,
    apply_tip_for_order_secure,
    get_order_employee,  # nuevo helper expuesto desde service
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

def register_attendance_check_out(attendance_id: str, actor_uid: str, actor_roles: List[str]):
    if not attendance_id.strip():
        raise HTTPException(status_code=400, detail="Missing attendance ID")
    # valida ownership (o admin) en service
    return update_attendance_checkout_secure(attendance_id, actor_uid, actor_roles)

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

def apply_tip_controller(order_id: str, mode: str, value: float, actor_uid: str, actor_roles: List[str]):
    target_emp = get_order_employee(order_id)
    if not target_emp:
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")
    return apply_tip_for_order_secure(order_id, mode, value, actor_uid, actor_roles)

def get_current_tips_total_controller(user_data: dict):
    uid = (user_data.get("uid") or user_data.get("user_id") or user_data.get("sub") or "").strip()
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return get_current_tips_total_service(uid)
