from fastapi import APIRouter
from app.controller.attendance_controller import register_attendance_check_in, register_attendance_check_out
from app.models.attendance import Attendance

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("/checkin")
def check_in(attendance: Attendance):
    return register_attendance_check_in(attendance)

@router.put("/checkout")
def check_out(id_employee: str, shift_id: str, checkout_time: str):
    return register_attendance_check_out(id_employee, shift_id, checkout_time)
