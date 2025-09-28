from fastapi import APIRouter, Depends, Query
from app.controller.task_controller import (
    create_and_attach_task_controller,
    assign_tasks_bulk_controller,
    update_task_status_controller,
    get_tasks_for_employee_controller,
)
from app.models.payloads import CreateTaskPayload, AssignTasksPayload
from app.dependencies import verify_token

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/register")
def create_and_attach_task(payload: CreateTaskPayload, user_data=Depends(verify_token)):
    return create_and_attach_task_controller(payload, user_data)

@router.post("/assign")
def assign_tasks_bulk(payload: AssignTasksPayload, user_data=Depends(verify_token)):
    return assign_tasks_bulk_controller(payload, user_data)

@router.put("/{employee_id}/{shift_id}/{task_id}/status/{status}")
def update_task_status(employee_id: str, shift_id: str, task_id: str, status: str, user_data=Depends(verify_token)):
    return update_task_status_controller(employee_id, shift_id, task_id, status, user_data)

@router.get("/by-employee/{employee_id}")
def tasks_by_employee(employee_id: str, shift_id: str | None = Query(default=None), user_data=Depends(verify_token)):

    return get_tasks_for_employee_controller(employee_id, shift_id, user_data)
