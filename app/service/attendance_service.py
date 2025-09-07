from datetime import datetime, date, time
from app.db.firebase import db

def today_str() -> str:
    return date.today().isoformat()

def iso_now() -> str:
    return datetime.now().isoformat()

def get_attendance_by_employee_and_shift(id_employee, shift_id):
    docs = (db.collection("attendance")
              .where("id_employee", "==", id_employee)
              .where("shift_id", "==", shift_id)
              .where("check_out_time", "==", None)
              .stream())
    for doc in docs:
        return doc.id
    return None

def create_attendance_record(employee_id, shift_id, observations=None):
    try:
        now = iso_now()
        work_date = today_str()

        new_ref = db.collection("attendance").document()
        data = {
            "id_employee": employee_id,
            "shift_id": shift_id,
            "work_date": work_date,
            "check_in_time": now,
            "check_out_time": None,
            "total_hours": "",
            "observations": observations or ""
        }
        new_ref.set(data)
        return {"message": "Check-in registrado", "id": new_ref.id}
    except Exception as e:
        return {"message": "Check-in registrado", "id": None, "error": str(e)}

def update_attendance_checkout(attendance_id):
    try:
        doc_ref = db.collection("attendance").document(attendance_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {"error": "Attendance record not found"}

        data = doc.to_dict()
        check_in_time = datetime.fromisoformat(data["check_in_time"])
        check_out_time = datetime.now()
        total = (check_out_time - check_in_time).total_seconds() / 3600

        doc_ref.update({
            "check_out_time": check_out_time.isoformat(),
            "total_hours": str(round(total, 2))
        })
        return {"message": "Check-out registrado", "id": attendance_id}
    except Exception as e:
        return {"error": str(e)}

def find_open_attendance_for_today(employee_id: str):
    try:
        today = today_str()
        q = (db.collection("attendance")
               .where("id_employee", "==", employee_id)
               .where("work_date", "==", today)
               .where("check_out_time", "==", None))

        for doc in q.stream():
            return {"id": doc.id}
        return None
    except Exception:
        return None
