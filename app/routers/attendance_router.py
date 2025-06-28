from fastapi import APIRouter, Depends
from app.controller.attendance_controller import register_attendance_check_in, register_attendance_check_out
from app.models.attendance import Attendance
from app.dependencies import verify_token

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("/checkin")
def check_in(attendance: Attendance, user_data=Depends(verify_token)):
    return register_attendance_check_in(attendance)

@router.put("/checkout")
def check_out(id_employee: str, shift_id: str, checkout_time: str, user_data=Depends(verify_token)):
    return register_attendance_check_out(id_employee, shift_id, checkout_time)
