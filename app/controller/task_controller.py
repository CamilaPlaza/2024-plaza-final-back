from fastapi import HTTPException
from typing import Optional

from app.models.payloads import CreateTaskPayload, AssignTasksPayload
from app.service.task_service import (
    create_and_attach_task_service,
    assign_tasks_bulk_service,
    update_task_status_service,
    get_tasks_for_employee_service,
    is_task_in_employee_shift,
)

ALLOWED_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETED"}

def _is_admin(user_data: dict) -> bool:
    role = str(user_data.get("role", "")).strip().lower()
    return role in {"admin", "administrator"}

def _uid(user_data: dict) -> str:
    return str(user_data.get("uid") or user_data.get("user_id") or "")

# --------------------
# controllers
# --------------------

def create_and_attach_task_controller(payload: CreateTaskPayload, user_data: dict):
    if not _is_admin(user_data):
        raise HTTPException(status_code=403, detail="Only admins can create tasks")

    try:
        creator = _uid(user_data)
        resp = create_and_attach_task_service(payload.dict(), created_by=creator)
        if "error" in resp:
            raise HTTPException(status_code=500, detail=resp["error"])
        return resp  # {message, id, employee_id, shift_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def assign_tasks_bulk_controller(payload: AssignTasksPayload, user_data: dict):
    if not _is_admin(user_data):
        raise HTTPException(status_code=403, detail="Only admins can assign tasks")

    try:
        creator = _uid(user_data)
        resp = assign_tasks_bulk_service(payload.dict(), created_by=creator)
        if "error" in resp:
            raise HTTPException(status_code=500, detail=resp["error"])
        return resp  # {message, added}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def update_task_status_controller(employee_id: str, shift_id: str, task_id: str, status: str, user_data: dict):
    status = str(status or "").upper()
    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status value")

    # Empleado solo puede tocar lo suyo
    if not _is_admin(user_data):
        me = _uid(user_data)
        if me != employee_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        try:
            if not is_task_in_employee_shift(employee_id, shift_id, task_id):
                raise HTTPException(status_code=403, detail="Task not found in your shift")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    try:
        resp = update_task_status_service(employee_id, shift_id, task_id, status)
        if "error" in resp:
            raise HTTPException(status_code=500, detail=resp["error"])
        return resp  # {message, id, new_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_tasks_for_employee_controller(employee_id: str, shift_id: Optional[str], user_data: dict):
    # Empleado solo puede leer lo suyo; admin cualquiera
    if not _is_admin(user_data):
        me = _uid(user_data)
        if me != employee_id:
            raise HTTPException(status_code=403, detail="Forbidden")

    try:
        resp = get_tasks_for_employee_service(employee_id, shift_id)
        if "error" in resp:
            raise HTTPException(status_code=500, detail=resp["error"])
        return resp  # {"tasks":[...]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
