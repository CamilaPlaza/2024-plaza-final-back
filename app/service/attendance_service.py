from datetime import datetime
from app.db.firebase import db

def get_attendance_by_employee_and_shift(id_employee, shift_id):
    docs = db.collection("attendance").where("id_employee", "==", id_employee).where("shift_id", "==", shift_id).where("check_out_time", "==", None).stream()
    for doc in docs:
        return doc.id
    return None

def create_attendance_record(attendance):
    try:
        new_ref = db.collection("attendance").document()
        data = attendance.dict()
        data["check_in_time"] = datetime.now().isoformat()
        data["check_out_time"] = None
        data["total_hours"] = ""
        db.collection("attendance").document(new_ref.id).set(data)
        return {"message": "Check-in registrado", "id": new_ref.id}
    except Exception as e:
        return {"error": str(e)}

def update_attendance_checkout(id_employee, shift_id, checkout_time_str):
    try:
        docs = db.collection("attendance").where("id_employee", "==", id_employee).where("shift_id", "==", shift_id).where("check_out_time", "==", None).stream()
        for doc in docs:
            data = doc.to_dict()
            check_in_time = datetime.fromisoformat(data["check_in_time"])
            check_out_time = datetime.fromisoformat(checkout_time_str)
            total = (check_out_time - check_in_time).total_seconds() / 3600
            db.collection("attendance").document(doc.id).update({
                "check_out_time": checkout_time_str,
                "total_hours": str(round(total, 2))
            })
            return {"message": "Check-out registrado", "id": doc.id}
        return {"error": "No open attendance record found"}
    except Exception as e:
        return {"error": str(e)}
