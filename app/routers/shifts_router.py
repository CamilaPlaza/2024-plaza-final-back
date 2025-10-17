from fastapi import APIRouter, Depends, HTTPException
from app.controller.shifts_controller import (
    get_assigned_shift_for_employee_controller,
    get_current_shift_controller,
    register_new_shift,
    assign_shift_to_employee,
    get_employees_from_shift,
)
from app.models.shift import Shift
from app.models.shift_employee import ShiftEmployee
from app.dependencies import verify_token

router = APIRouter(prefix="/shifts", tags=["Shifts"])

def _roles(user_data: dict) -> list[str]:
    v = user_data.get("roles") or user_data.get("role") or []
    if isinstance(v, str):
        v = [v]
    return [str(x).strip().upper() for x in v]

def _is_admin(user_data: dict) -> bool:
    r = _roles(user_data or {})
    return "ADMIN" in r or "ROLE_ADMIN" in r or "ADMINISTRATOR" in r

def _uid(user_data: dict) -> str:
    return (user_data.get("uid") or user_data.get("user_id") or user_data.get("sub") or "").strip()

@router.post("/register")
def create_shift(shift: Shift, user_data=Depends(verify_token)):
    if not _is_admin(user_data):
        raise HTTPException(status_code=403, detail="Admin role required")
    return register_new_shift(shift)

@router.post("/assign")
def assign_employee(shift_employee: ShiftEmployee, user_data=Depends(verify_token)):
    if not _is_admin(user_data):
        raise HTTPException(status_code=403, detail="Admin role required")
    return assign_shift_to_employee(shift_employee)

@router.get("/{shift_id}/employees")
def list_employees(shift_id: str, user_data=Depends(verify_token)):
    if not _is_admin(user_data):
        raise HTTPException(status_code=403, detail="Admin role required")
    return get_employees_from_shift(shift_id)

@router.get("/current")
def get_current_shift(user_data=Depends(verify_token)):
    return get_current_shift_controller()

@router.get("/assigned")
def get_assigned_shift(employee_id: str | None = None, user_data=Depends(verify_token)):
    if not _is_admin(user_data):
        token_uid = _uid(user_data)
        target = employee_id or token_uid
        if not token_uid or target != token_uid:
            raise HTTPException(status_code=403, detail="Forbidden")
        return get_assigned_shift_for_employee_controller(token_uid)
    target = employee_id or _uid(user_data)
    if not target:
        raise HTTPException(status_code=400, detail="Missing employee_id")
    return get_assigned_shift_for_employee_controller(target)
