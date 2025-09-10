from datetime import datetime, date, time, timedelta
from app.db.firebase import db

LATE_TOLERANCE_MIN = 15   # tolerancia para llegar "a tiempo"
EARLY_WINDOW_MIN   = 30   # se permite llegar hasta 30' antes

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

# ======================
#   LÓGICA DE PREVIEW
# ======================

def _get_shift(shift_id: str) -> dict | None:
    """Lee el shift y devuelve dict con start_time/end_time (strings HH:MM) y name si existe."""
    snap = db.collection("shifts").document(shift_id).get()
    if not snap.exists:
        return None
    return snap.to_dict() or {}

def _parse_hhmm(hhmm: str) -> time:
    return datetime.strptime(hhmm, "%H:%M").time()

def _evaluate_checkin_against_shift(shift_id: str, now_dt: datetime) -> dict:

    shift = _get_shift(shift_id)
    if not shift:
        return {
            "off_shift": True,
            "is_late": False,
            "minutes_late": 0,
            "expected_start": None,
            "expected_end": None,
        }

    start_s = shift.get("start_time")
    end_s   = shift.get("end_time")
    if not start_s or not end_s:
        return {
            "off_shift": True,
            "is_late": False,
            "minutes_late": 0,
            "expected_start": start_s,
            "expected_end": end_s,
        }

    start_t = _parse_hhmm(start_s)
    end_t   = _parse_hhmm(end_s)

    start_dt = datetime.combine(now_dt.date(), start_t)
    end_dt   = datetime.combine(now_dt.date(), end_t)
    if end_t <= start_t:
        end_dt += timedelta(days=1)

    early_from   = start_dt - timedelta(minutes=EARLY_WINDOW_MIN)
    late_limit   = start_dt + timedelta(minutes=LATE_TOLERANCE_MIN)


    if early_from <= now_dt <= end_dt:
        if now_dt <= late_limit:
            return {
                "off_shift": False,
                "is_late": False,
                "minutes_late": 0,
                "expected_start": start_s,
                "expected_end": end_s,
            }
        else:
            mins = int((now_dt - start_dt).total_seconds() // 60)
            return {
                "off_shift": False,
                "is_late": True,
                "minutes_late": max(mins, 0),
                "expected_start": start_s,
                "expected_end": end_s,
            }
    else:
        return {
            "off_shift": True,
            "is_late": False,
            "minutes_late": 0,
            "expected_start": start_s,
            "expected_end": end_s,
        }

def make_checkin_preview(employee_id: str, shift_id: str) -> dict:
    existing = find_open_attendance_for_today(employee_id)
    if existing:
        att_id = existing["id"] if isinstance(existing, dict) else existing
        return {
            "can_check_in": False,
            "reason": "already_open",
            "attendance_id": att_id,
        }

    now_dt = datetime.now()
    eval_res = _evaluate_checkin_against_shift(shift_id, now_dt)
    return {
        "can_check_in": True,
        "reason": "ok",
        "off_shift": eval_res["off_shift"],
        "is_late": eval_res["is_late"],
        "minutes_late": eval_res["minutes_late"],
        "expected_start": eval_res.get("expected_start"),
        "expected_end": eval_res.get("expected_end"),
        "now": iso_now(),
    }
