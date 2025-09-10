from datetime import datetime
from app.db.firebase import db

def create_shift(shift_data):
    try:
        new_ref = db.collection("shifts").document()
        shift_data["id"] = new_ref.id
        new_ref.set(shift_data)
        return {"id": new_ref.id}
    except Exception as e:
        return {"error": str(e)}

def assign_employee_to_shift(data):
    try:
        new_ref = db.collection("shift_assignments").document()
        data["id"] = new_ref.id
        new_ref.set(data)
        return {"id": new_ref.id}
    except Exception as e:
        return {"error": str(e)}

def get_employees_by_shift(shift_id):
    try:
        query = db.collection("shift_assignments").where("id_shift", "==", shift_id).stream()
        return [doc.to_dict() for doc in query]
    except Exception as e:
        return {"error": str(e)}

def get_current_shift_id(): #Shift actual del día, el momento
    now = datetime.now().time()

    docs = db.collection("shifts").stream()
    for doc in docs:
        data = doc.to_dict() or {}
        start_str = data.get("start_time")
        end_str   = data.get("end_time")
        if not start_str or not end_str:
            continue

        start = datetime.strptime(start_str, "%H:%M").time()
        end   = datetime.strptime(end_str,   "%H:%M").time()

        if start <= end:
            in_range = start <= now < end
        else:
            in_range = (now >= start) or (now < end)

        if in_range:
            return data.get("id") or doc.id

    return None


def get_assigned_shift_for_employee(employee_id: str):

    try:
        if not employee_id:
            return {"error": "Missing employee_id"}

        q = (db.collection("shift_assignments")
               .where("id_employee", "==", employee_id)
               .limit(1)
               .stream())

        assignment_doc = None
        for doc in q:
            assignment_doc = doc
            break

        if not assignment_doc:
            return None

        assignment = assignment_doc.to_dict() or {}
        shift_id = assignment.get("id_shift")
        if not shift_id:
            return {"error": "Assignment without id_shift"}
        
        shift_snap = db.collection("shifts").document(shift_id).get()
        if not shift_snap.exists:
            return {"error": "Shift not found"}

        shift = shift_snap.to_dict() or {}
        shift["id"] = shift_snap.id
        return shift

    except Exception as e:
        return {"error": str(e)}
