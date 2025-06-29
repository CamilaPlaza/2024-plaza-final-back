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
        query = db.collection("shift_assignments").where("shift_id", "==", shift_id).stream()
        return [doc.to_dict() for doc in query]
    except Exception as e:
        return {"error": str(e)}

def get_current_shift_id():
    now = datetime.now().time()

    docs = db.collection("shifts").where("status", "==", "ACTIVE").stream()
    for doc in docs:
        data = doc.to_dict()
        start = datetime.strptime(data["start_time"], "%H:%M").time()
        end = datetime.strptime(data["end_time"], "%H:%M").time()

        if start > end:
            if now >= start or now <= end:
                return doc.id
        else:
            if start <= now < end:
                return doc.id
    return None