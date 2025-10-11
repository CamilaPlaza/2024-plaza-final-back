# app/router/attendance_router.py
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.controller.attendance_controller import (
    get_current_tips_total_controller,
    get_today_attendance_controller,
    register_attendance_check_in,
    register_attendance_check_out,
    get_open_attendance_controller,
    get_checkin_preview_controller,
    apply_tip_controller,
)
from app.dependencies import verify_token

router = APIRouter(prefix="/attendance", tags=["Attendance"])

class ApplyTipIn(BaseModel):
    order_id: str
    mode: Literal["percent", "absolute"]
    value: float

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
def get_open_attendance(employee_id: str, user_data=Depends(verify_token)):
    return get_open_attendance_controller(employee_id)

@router.get("/checkin-preview")
def checkin_preview(employee_id: str, shift_id: str, user_data=Depends(verify_token)):
    if not employee_id or not shift_id:
        raise HTTPException(status_code=400, detail="Missing required data")
    return get_checkin_preview_controller(employee_id, shift_id)

@router.get("/today")
def today(employee_id: str, user_data=Depends(verify_token)):
    return get_today_attendance_controller(employee_id)

@router.post("/tips/apply")
def apply_tip(payload: ApplyTipIn, user_data=Depends(verify_token)):
    return apply_tip_controller(payload.order_id, payload.mode, payload.value)

@router.get("/tips/total")
def get_current_tips_total(user_data = Depends(verify_token)):
    return get_current_tips_total_controller(user_data)