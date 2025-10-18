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

def _uid_from(user_data: dict) -> str:
    return (user_data.get("uid") or user_data.get("user_id") or user_data.get("sub") or "").strip()

def _roles_from(user_data: dict):
    roles = user_data.get("roles") or user_data.get("role") or []
    if isinstance(roles, str):
        roles = [roles]
    return [str(r) for r in roles]

@router.post("/checkin")
def check_in(
    employee_id: Optional[str] = None,
    shift_id: str = "",
    observations: Optional[str] = None,
    user_data=Depends(verify_token)
):
    uid = _uid_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not shift_id:
        raise HTTPException(status_code=400, detail="Missing shift_id")
    return register_attendance_check_in(uid, shift_id, observations)

@router.put("/checkout/{attendance_id}")
def check_out(attendance_id: str, user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    roles = _roles_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return register_attendance_check_out(attendance_id, uid, roles)

@router.get("/open-attendance")
def get_open_attendance(employee_id: Optional[str] = None, user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return get_open_attendance_controller(uid)

@router.get("/checkin-preview")
def checkin_preview(employee_id: Optional[str] = None, shift_id: Optional[str] = None, user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not shift_id:
        raise HTTPException(status_code=400, detail="Missing required data")
    return get_checkin_preview_controller(uid, shift_id)

@router.get("/today")
def today(employee_id: Optional[str] = None, user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return get_today_attendance_controller(uid)

@router.post("/tips/apply")
def apply_tip(payload: ApplyTipIn, user_data=Depends(verify_token)):
    uid = _uid_from(user_data)
    roles = _roles_from(user_data)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return apply_tip_controller(payload.order_id, payload.mode, payload.value, uid, roles)

@router.get("/tips/total")
def get_current_tips_total(user_data = Depends(verify_token)):
    return get_current_tips_total_controller(user_data)
