from app.db.firebase import db

from typing import Dict, Any

tasks_collection = db.collection("tasks")
shift_employee_collection = db.collection("shift_employee")

def create_task(task_data: Dict[str, Any]):
    try:
        new_doc_ref = tasks_collection.document()
        task_data['id'] = new_doc_ref.id
        new_doc_ref.set(task_data)
        return {"message": "Task created", "id": new_doc_ref.id}
    except Exception as e:
        return {"error": str(e)}

def update_task_status(task_id: str, new_status: str):
    try:
        doc_ref = tasks_collection.document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {"error": "Task not found"}

        doc_ref.update({"status": new_status})
        return {"message": "Status updated", "id": task_id}
    except Exception as e:
        return {"error": str(e)}

def assign_tasks_to_employee_shift(data: Dict[str, Any]):
    try:
        id_employee = data['id_employee']
        id_shift = data['id_shift']
        assigned_tasks = data['assigned_tasks']

        query = shift_employee_collection.where("id_employee", "==", id_employee).where("id_shift", "==", id_shift).limit(1).get()

        if query:
            doc_ref = query[0].reference
            doc_ref.update({"assigned_tasks": assigned_tasks})
        else:
            new_doc_ref = shift_employee_collection.document()
            new_doc_ref.set(data)

        return {"message": "Tasks assigned/updated successfully"}
    except Exception as e:
        return {"error": str(e)}
