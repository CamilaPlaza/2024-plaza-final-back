from typing import Optional
from fastapi import HTTPException
from app.service.attendance_service import (
    create_attendance_record,
    update_attendance_checkout,
    get_attendance_by_employee_and_shift,
    find_open_attendance_for_today
)

def register_attendance_check_in(employee_id: str, shift_id: str, observations: Optional[str] = None):
    if not employee_id.strip() or not shift_id.strip():
        raise HTTPException(status_code=400, detail="Missing required data")
    
    existing = get_attendance_by_employee_and_shift(employee_id, shift_id)
    if existing:
        raise HTTPException(status_code=400, detail="Already checked in for this shift")

    return create_attendance_record(employee_id, shift_id, observations)


def register_attendance_check_out(attendance_id: str):
    if not attendance_id.strip():
        raise HTTPException(status_code=400, detail="Missing attendance ID")

    return update_attendance_checkout(attendance_id)

def get_open_attendance_controller(employee_id: str, shift_id: str):
    attendance_id = find_open_attendance_for_today(employee_id, shift_id)
    if attendance_id:
        return {"attendance_id": attendance_id}
    raise HTTPException(status_code=404, detail="No open attendance found")