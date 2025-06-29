from typing import Optional
from fastapi import APIRouter, Depends
from app.controller.attendance_controller import register_attendance_check_in, register_attendance_check_out, get_open_attendance_controller
from app.models.attendance import Attendance
from app.dependencies import verify_token

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("/checkin")
def check_in(
    employee_id: str,
    shift_id: str,
    observations: Optional[str] = None,
    user_data=Depends(verify_token)
):
    return register_attendance_check_in(employee_id, shift_id, observations)

@router.put("/checkout/{attendance_id}")
def check_out(attendance_id: str, user_data=Depends(verify_token)):
    return register_attendance_check_out(attendance_id)

@router.get("/open-attendance")
def get_open_attendance(employee_id: str, shift_id: str, user_data=Depends(verify_token)):
    return get_open_attendance_controller(employee_id, shift_id)