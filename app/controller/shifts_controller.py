from app.models.shift import Shift
from app.models.shift_employee import ShiftEmployee
from fastapi import HTTPException
from app.service.shift_service import create_shift, assign_employee_to_shift, get_current_shift_id, get_employees_by_shift

def register_new_shift(shift: Shift):
    try:
        response = create_shift(shift.dict())
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        return {"message": "Shift created successfully", "id": response["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def assign_shift_to_employee(shift_employee: ShiftEmployee):
    if not shift_employee.id_shift.strip() or not shift_employee.id_employee.strip():
        raise HTTPException(status_code=400, detail="Shift ID and Employee ID are required")

    if not isinstance(shift_employee.assigned_tasks, list):
        raise HTTPException(status_code=400, detail="Tasks must be a list")

    try:
        response = assign_employee_to_shift(shift_employee.dict())
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        return {"message": "Employee assigned to shift", "id": response["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_employees_from_shift(shift_id: str):
    if not shift_id.strip():
        raise HTTPException(status_code=400, detail="Shift ID is required")

    try:
        employees = get_employees_by_shift(shift_id)
        return employees
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_current_shift_controller():
    shift_id = get_current_shift_id()
    if not shift_id:
        raise HTTPException(status_code=404, detail="No current shift found")
    return {"shift_id": shift_id}