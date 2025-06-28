from fastapi import HTTPException
from app.models.task import Task
from app.models.shift_employee import ShiftEmployee
from app.service.task_service import (
    create_task,
    update_task_status,
    assign_tasks_to_employee_shift,
)

def create_new_task(task: Task):
    try:
        response = create_task(task.dict())
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        return {"message": "Task created successfully", "id": response["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def update_task_state(task_id: str, status: str):
    if status not in ["PENDING", "IN_PROGRESS", "COMPLETED"]:
        raise HTTPException(status_code=400, detail="Invalid status value")
    if not task_id or len(task_id.strip()) == 0:
        raise HTTPException(status_code=400, detail="Task ID is required")

    try:
        response = update_task_status(task_id, status)
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        return {"message": "Task status updated", "id": task_id, "new_status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def assign_task(shift_employee: ShiftEmployee):
    if not shift_employee.id_employee or len(shift_employee.id_employee.strip()) == 0:
        raise HTTPException(status_code=400, detail="Employee ID is required")
    if not shift_employee.id_shift or len(shift_employee.id_shift.strip()) == 0:
        raise HTTPException(status_code=400, detail="Shift ID is required")
    if not shift_employee.assigned_tasks or not isinstance(shift_employee.assigned_tasks, list) or len(shift_employee.assigned_tasks) == 0:
        raise HTTPException(status_code=400, detail="Assigned tasks list cannot be empty")

    for task_id in shift_employee.assigned_tasks:
        if not isinstance(task_id, str) or len(task_id.strip()) == 0:
            raise HTTPException(status_code=400, detail="Each task ID must be a non-empty string")

    try:
        response = assign_tasks_to_employee_shift(shift_employee.dict())
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        return {"message": "Tasks assigned successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
