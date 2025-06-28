from fastapi import HTTPException
from app.models.attendance import Attendance
from app.service.attendance_service import (
    create_attendance_record,
    update_attendance_checkout,
    get_attendance_by_employee_and_shift
)
from datetime import datetime

def register_attendance_check_in(attendance: Attendance):
    if not attendance.id_employee or not isinstance(attendance.id_employee, str):
        raise HTTPException(status_code=400, detail="Invalid or missing employee ID")
    
    if not attendance.shift_id or not isinstance(attendance.shift_id, str):
        raise HTTPException(status_code=400, detail="Invalid or missing shift ID")
    existing = get_attendance_by_employee_and_shift(attendance.id_employee, attendance.shift_id)
    if existing:
        raise HTTPException(status_code=400, detail="Already checked in for this shift")

    return create_attendance_record(attendance)

def register_attendance_check_out(id_employee: str, shift_id: str, checkout_time: str):
    if not id_employee:
        raise HTTPException(status_code=400, detail="Missing employee ID")
    if not shift_id:
        raise HTTPException(status_code=400, detail="Missing shift ID")
    if not checkout_time:
        raise HTTPException(status_code=400, detail="Missing checkout time")

    try:
        datetime.fromisoformat(checkout_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format for checkout")

    updated = update_attendance_checkout(id_employee, shift_id, checkout_time)
    if "error" in updated:
        raise HTTPException(status_code=400, detail=updated["error"])
    return updated
