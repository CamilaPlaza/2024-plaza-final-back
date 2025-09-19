from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from app.db.firebase import db

# Colecciones
SHIFT_EMPLOYEE = db.collection("shift_employee")

ALLOWED_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETED"}

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _clean_status(val: Optional[str]) -> str:
    s = str(val or "PENDING").upper()
    return s if s in ALLOWED_STATUSES else "PENDING"

def _ensure_shift_doc(id_employee: str, id_shift: str) -> Dict[str, Any]:
    """
    Busca doc por (id_employee,id_shift). Si no existe, lo crea con shift_assignments=[]
    Devuelve {"ref": doc_ref, "data": dict}
    """
    q = (
        SHIFT_EMPLOYEE.where("id_employee", "==", id_employee)
        .where("id_shift", "==", id_shift)
        .limit(1)
        .get()
    )
    if q:
        snap = q[0]
        return {"ref": snap.reference, "data": snap.to_dict() or {}}
    # crear
    ref = SHIFT_EMPLOYEE.document()
    data = {
        "id": ref.id,
        "id_employee": id_employee,
        "id_shift": id_shift,
        "shift_assignments": [],
        "updated_at": _now_iso(),
    }
    ref.set(data)
    return {"ref": ref, "data": data}

def _append_tasks(doc_ref, existing: List[Dict[str, Any]], tasks_to_add: List[Dict[str, Any]]):
    updated = list(existing)
    for t in tasks_to_add:
        # si viene sin id, genero uno
        tid = t.get("id") or str(uuid4())
        t["id"] = tid
        # defaults / saneo
        t["status"] = _clean_status(t.get("status"))
        if "created_at" not in t or not t.get("created_at"):
            t["created_at"] = _now_iso()
        updated.append(t)
    doc_ref.update({"shift_assignments": updated, "updated_at": _now_iso()})
    return [t["id"] for t in tasks_to_add]

# --------------------
# Create and attach
# --------------------

def create_and_attach_task_service(payload: Dict[str, Any], created_by: Optional[str]) -> Dict[str, Any]:
    """
    payload: {
      "id_employee": str,
      "id_shift": str,
      "task": {
        "name": str, "description": str,
        "status"?: str, "tag"?: str,
        "start_at"?: str, "due_at"?: str
      }
    }
    """
    try:
        id_employee = str(payload.get("id_employee", "")).strip()
        id_shift = str(payload.get("id_shift", "")).strip()
        task = dict(payload.get("task") or {})

        if not id_employee or not id_shift:
            return {"error": "id_employee and id_shift are required"}
        name = str(task.get("name", "")).strip()
        desc = str(task.get("description", "")).strip()
        if not name or not desc:
            return {"error": "name and description are required"}

        # normalizar tarea
        task["id"] = str(uuid4())
        task["status"] = _clean_status(task.get("status"))
        task["created_at"] = _now_iso()
        if created_by:
            task["created_by"] = created_by

        # upsert del doc de shift
        bucket = _ensure_shift_doc(id_employee, id_shift)
        ref, data = bucket["ref"], bucket["data"]
        current = list(data.get("shift_assignments") or [])
        ref.update({"shift_assignments": current + [task], "updated_at": _now_iso()})
        return {
            "message": "Task created and attached",
            "id": task["id"],
            "employee_id": id_employee,
            "shift_id": id_shift,
        }
    except Exception as e:
        return {"error": str(e)}

# --------------------
# Assign bulk
# --------------------

def assign_tasks_bulk_service(payload: Dict[str, Any], created_by: Optional[str]) -> Dict[str, Any]:
    """
    payload: {
      "id_employee": str,
      "id_shift": str,
      "shift_assignments": [ Task, Task, ... ]  # pueden venir sin id/status
    }
    """
    try:
        id_employee = str(payload.get("id_employee", "")).strip()
        id_shift = str(payload.get("id_shift", "")).strip()
        incoming = list(payload.get("shift_assignments") or [])
        if not id_employee or not id_shift:
            return {"error": "id_employee and id_shift are required"}
        if not incoming:
            return {"error": "shift_assignments cannot be empty"}

        # validar mínimos & set defaults
        to_add: List[Dict[str, Any]] = []
        for raw in incoming:
            t = dict(raw or {})
            name = str(t.get("name", "")).strip()
            desc = str(t.get("description", "")).strip()
            if not name or not desc:
                return {"error": "each task must have name and description"}
            t["status"] = _clean_status(t.get("status"))
            t["id"] = t.get("id") or str(uuid4())
            if created_by and not t.get("created_by"):
                t["created_by"] = created_by
            if not t.get("created_at"):
                t["created_at"] = _now_iso()
            to_add.append(t)

        bucket = _ensure_shift_doc(id_employee, id_shift)
        ref, data = bucket["ref"], bucket["data"]
        existing = list(data.get("shift_assignments") or [])

        # MERGE simple: agrega al final; si ya existe id igual, lo deja tal cual (no duplica)
        existing_ids = {t.get("id") for t in existing}
        new_items = [t for t in to_add if t["id"] not in existing_ids]

        ref.update({"shift_assignments": existing + new_items, "updated_at": _now_iso()})
        return {"message": "Tasks assigned/updated successfully", "added": len(new_items)}
    except Exception as e:
        return {"error": str(e)}

# --------------------
# Update status (embedded)
# --------------------

def update_task_status_service(employee_id: str, shift_id: str, task_id: str, new_status: str) -> Dict[str, Any]:
    try:
        new_status = _clean_status(new_status)
        bucket = _ensure_shift_doc(employee_id, shift_id)
        ref, data = bucket["ref"], bucket["data"]
        arr = list(data.get("shift_assignments") or [])

        found = False
        for i, t in enumerate(arr):
            if t.get("id") == task_id:
                arr[i] = {**t, "status": new_status}
                found = True
                break

        if not found:
            return {"error": "Task not found in this shift"}

        ref.update({"shift_assignments": arr, "updated_at": _now_iso()})
        return {"message": "Status updated", "id": task_id, "new_status": new_status}
    except Exception as e:
        return {"error": str(e)}

# --------------------
# Get tasks for employee
# --------------------

def get_tasks_for_employee_service(employee_id: str, shift_id: Optional[str]) -> Dict[str, Any]:
    try:
        if not employee_id:
            return {"error": "employee_id required"}

        tasks: List[Dict[str, Any]] = []

        if shift_id:
            q = (
                SHIFT_EMPLOYEE.where("id_employee", "==", employee_id)
                .where("id_shift", "==", shift_id)
                .limit(1)
                .get()
            )
            if q:
                d = q[0].to_dict() or {}
                for t in d.get("shift_assignments", []):
                    tasks.append({**t, "id_shift": shift_id})
        else:
            q = SHIFT_EMPLOYEE.where("id_employee", "==", employee_id).stream()
            for snap in q:
                d = snap.to_dict() or {}
                sid = d.get("id_shift")
                for t in d.get("shift_assignments", []):
                    tasks.append({**t, "id_shift": sid})

        return {"tasks": tasks}
    except Exception as e:
        return {"error": str(e)}

# --------------------
# Permission helper
# --------------------

def is_task_in_employee_shift(employee_id: str, shift_id: str, task_id: str) -> bool:
    try:
        q = (
            SHIFT_EMPLOYEE.where("id_employee", "==", employee_id)
            .where("id_shift", "==", shift_id)
            .limit(1)
            .get()
        )
        if not q:
            return False
        d = q[0].to_dict() or {}
        for t in d.get("shift_assignments", []):
            if t.get("id") == task_id:
                return True
        return False
    except Exception:
        return False
