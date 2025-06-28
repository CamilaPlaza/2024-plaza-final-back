from fastapi import APIRouter
from app.controller.task_controller import create_new_task, update_task_state, assign_task
from app.models.task import Task
from app.models.shift_employee import ShiftEmployee

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/register")
def create_task(task: Task):
    return create_new_task(task)

@router.put("/{task_id}/status/{status}")
def change_status(task_id: str, status: str):
    return update_task_state(task_id, status)

@router.post("/assign")
def assign_task_to_employee(shift_employee: ShiftEmployee):
    return assign_task(shift_employee)
