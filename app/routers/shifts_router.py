from fastapi import APIRouter
from app.controller.shifts_controller import register_new_shift, assign_shift_to_employee, get_employees_from_shift
from app.models.shift import Shift
from app.models.shift_employee import ShiftEmployee

router = APIRouter(prefix="/shifts", tags=["Shifts"])

@router.post("/register")
def create_shift(shift: Shift):
    return register_new_shift(shift)

@router.post("/assign")
def assign_employee(shift_employee: ShiftEmployee):
    return assign_shift_to_employee(shift_employee)

@router.get("/{shift_id}/employees")
def list_employees(shift_id: str):
    return get_employees_from_shift(shift_id)
