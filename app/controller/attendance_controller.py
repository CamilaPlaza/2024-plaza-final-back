from typing import Optional
from fastapi import HTTPException
from app.service.attendance_service import (
    create_attendance_record,
    update_attendance_checkout,
    find_open_attendance_for_today,
    make_checkin_preview,   # 👈 nuevo
)

def register_attendance_check_in(employee_id: str, shift_id: str, observations: Optional[str] = None):
    if not employee_id.strip() or not shift_id.strip():
        raise HTTPException(status_code=400, detail="Missing required data")

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
