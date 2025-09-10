from fastapi import APIRouter, Depends, HTTPException
from app.controller.shifts_controller import get_assigned_shift_for_employee_controller, get_current_shift_controller, register_new_shift, assign_shift_to_employee, get_employees_from_shift
from app.models.shift import Shift
from app.models.shift_employee import ShiftEmployee
from app.dependencies import verify_token
router = APIRouter(prefix="/shifts", tags=["Shifts"])

@router.post("/register")
def create_shift(shift: Shift, user_data=Depends(verify_token)):
    return register_new_shift(shift)

@router.post("/assign")
def assign_employee(shift_employee: ShiftEmployee, user_data=Depends(verify_token)):
    return assign_shift_to_employee(shift_employee)

@router.get("/{shift_id}/employees")
def list_employees(shift_id: str, user_data=Depends(verify_token)):
    return get_employees_from_shift(shift_id)

@router.get("/current")
def get_current_shift(user_data=Depends(verify_token)):
    return get_current_shift_controller()

@router.get("/assigned")
def get_assigned_shift(employee_id: str, user_data=Depends(verify_token)):
        return get_assigned_shift_for_employee_controller(employee_id)