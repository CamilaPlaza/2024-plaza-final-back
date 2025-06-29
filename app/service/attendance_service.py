from datetime import datetime
from app.db.firebase import db

def get_attendance_by_employee_and_shift(id_employee, shift_id):
    docs = db.collection("attendance").where("id_employee", "==", id_employee).where("shift_id", "==", shift_id).where("check_out_time", "==", None).stream()
    for doc in docs:
        return doc.id
    return None

def create_attendance_record(employee_id, shift_id, observations=None):
    try:
        now = datetime.now().isoformat()
        new_ref = db.collection("attendance").document()
        data = {
            "id_employee": employee_id,
            "shift_id": shift_id,
            "check_in_time": now,
            "check_out_time": None,
            "total_hours": "",
            "observations": observations or ""
        }
        new_ref.set(data)
        return {"message": "Check-in registrado", "id": new_ref.id}
    except Exception as e:
        return {"error": str(e)}



def update_attendance_checkout(attendance_id):
    try:
        doc = db.collection("attendance").document(attendance_id).get()
        if not doc.exists:
            return {"error": "Attendance record not found"}
        
        data = doc.to_dict()
        check_in_time = datetime.fromisoformat(data["check_in_time"])
        check_out_time = datetime.now()
        total = (check_out_time - check_in_time).total_seconds() / 3600

        db.collection("attendance").document(attendance_id).update({
            "check_out_time": check_out_time.isoformat(),
            "total_hours": str(round(total, 2))
        })

        return {"message": "Check-out registrado", "id": attendance_id}
    except Exception as e:
        return {"error": str(e)}

def find_open_attendance_for_today(employee_id: str, shift_id: str):
    today = datetime.now().date()
    start_of_day = datetime.combine(today, datetime.min.time()).isoformat()
    end_of_day = datetime.combine(today, datetime.max.time()).isoformat()

    docs = (
        db.collection("attendance")
        .where("id_employee", "==", employee_id)
        .where("shift_id", "==", shift_id)
        .where("check_out_time", "==", None)
        .where("check_in_time", ">=", start_of_day)
        .where("check_in_time", "<=", end_of_day)
        .stream()
    )

    for doc in docs:
        return doc.id

    return None