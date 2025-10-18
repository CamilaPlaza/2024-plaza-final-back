# app/service/attendance_service.py
from datetime import datetime, date, time, timedelta
from fastapi import HTTPException
from app.db.firebase import db

LATE_TOLERANCE_MIN = 15
EARLY_WINDOW_MIN   = 30

def today_str() -> str:
    return date.today().isoformat()

def iso_now() -> str:
    return datetime.now().isoformat()

def _round2(x: float) -> float:
    return round(float(x), 2)

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
            "observations": observations or "",
            "tips_total_ars": 0.0,
            "tipped_orders": [],
            "updated_at": now,
        }
        new_ref.set(data)
        return {"message": "Check-in registrado", "id": new_ref.id}
    except Exception as e:
        return {"message": "Check-in registrado", "id": None, "error": str(e)}

def _get_attendance_doc(attendance_id):
    doc_ref = db.collection("attendance").document(attendance_id)
    doc = doc_ref.get()
    return doc_ref, doc

def update_attendance_checkout_secure(attendance_id: str, actor_uid: str, actor_roles: list[str]):
    try:
        doc_ref, doc = _get_attendance_doc(attendance_id)
        if not doc.exists:
            return {"error": "Attendance record not found"}
        data = doc.to_dict() or {}
        owner_uid = (data.get("id_employee") or "").strip()
        is_admin = "admin" in (actor_roles or [])

        if not is_admin and owner_uid != actor_uid:
            raise HTTPException(status_code=403, detail="Forbidden")

        if data.get("check_out_time"):
            return {"message": "Check-out ya registrado", "id": attendance_id}

        check_in_time = datetime.fromisoformat(data["check_in_time"])
        check_out_time = datetime.now()
        total = (check_out_time - check_in_time).total_seconds() / 3600
        doc_ref.update({
            "check_out_time": check_out_time.isoformat(),
            "total_hours": str(round(total, 2)),
            "updated_at": iso_now(),
        })
        return {"message": "Check-out registrado", "id": attendance_id}
    except HTTPException:
        raise
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

def _get_shift(shift_id: str) -> dict | None:
    snap = db.collection("shifts").document(shift_id).get()
    if not snap.exists:
        return None
    return snap.to_dict() or {}

def _parse_hhmm(hhmm: str) -> time:
    return datetime.strptime(hhmm, "%H:%M").time()

def has_any_attendance_today(employee_id: str) -> bool:
    today = today_str()
    q = (db.collection("attendance")
           .where("id_employee", "==", employee_id)
           .where("work_date", "==", today)
           .limit(1))
    for _ in q.stream():
        return True
    return False

def _evaluate_checkin_against_shift(shift_id: str, now_dt: datetime) -> dict:
    shift = _get_shift(shift_id)
    if not shift:
        return {"off_shift": True,"is_late": False,"minutes_late": 0,"expected_start": None,"expected_end": None}
    start_s = shift.get("start_time")
    end_s   = shift.get("end_time")
    if not start_s or not end_s:
        return {"off_shift": True,"is_late": False,"minutes_late": 0,"expected_start": start_s,"expected_end": end_s}
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
            return {"off_shift": False,"is_late": False,"minutes_late": 0,"expected_start": start_s,"expected_end": end_s}
        else:
            mins = int((now_dt - start_dt).total_seconds() // 60)
            return {"off_shift": False,"is_late": True,"minutes_late": max(mins, 0),"expected_start": start_s,"expected_end": end_s}
    else:
        return {"off_shift": True,"is_late": False,"minutes_late": 0,"expected_start": start_s,"expected_end": end_s}

def make_checkin_preview(employee_id: str, shift_id: str) -> dict:
    existing = find_open_attendance_for_today(employee_id)
    if existing:
        att_id = existing["id"] if isinstance(existing, dict) else existing
        return {"can_check_in": False,"reason": "already_open","attendance_id": att_id}
    if has_any_attendance_today(employee_id):
        return {"can_check_in": False,"reason": "already_completed"}
    now_dt = datetime.now()
    eval_res = _evaluate_checkin_against_shift(shift_id, now_dt)
    return {"can_check_in": True,"reason": "ok","off_shift": eval_res["off_shift"],"is_late": eval_res["is_late"],"minutes_late": eval_res["minutes_late"],"expected_start": eval_res.get("expected_start"),"expected_end": eval_res.get("expected_end"),"now": iso_now()}

def get_today_attendance_data(employee_id: str) -> dict | None:
    today = today_str()
    q = (db.collection("attendance")
           .where("id_employee", "==", employee_id)
           .where("work_date", "==", today))
    for doc in q.stream():
        d = doc.to_dict() or {}
        d["id"] = doc.id
        return d
    return None

def _get_order(order_id: str) -> dict | None:
    snap = db.collection("orders").document(order_id).get()
    if not snap.exists:
        return None
    d = snap.to_dict() or {}
    d["id"] = snap.id
    return d

def get_order_employee(order_id: str) -> str | None:
    order = _get_order(order_id)
    if not order:
        return None
    return (order.get("employee") or "").strip() or None

def apply_tip_for_order_secure(order_id: str, mode: str, value: float, actor_uid: str, actor_roles: list[str]):
    if not order_id or not isinstance(order_id, str):
        raise HTTPException(status_code=400, detail="Invalid order_id")
    if mode not in ("percent", "absolute"):
        raise HTTPException(status_code=400, detail="Invalid mode")

    try:
        valf = float(value)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid value")
    if valf <= 0:
        raise HTTPException(status_code=400, detail="Value must be greater than 0")

    order = _get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")
    if order.get("status") != "FINALIZED":
        raise HTTPException(status_code=409, detail="ORDER_NOT_FINALIZED")

    # ownership: el pedido debe pertenecer al actor (o ser admin)
    employee_id = (order.get("employee") or "").strip()
    if not employee_id:
        raise HTTPException(status_code=403, detail="ORDER_WITHOUT_EMPLOYEE")
    is_admin = "admin" in (actor_roles or [])
    if not is_admin and employee_id != actor_uid:
        raise HTTPException(status_code=403, detail="FORBIDDEN_TIP_ON_OTHERS_ORDER")

    try:
        base_total = float(order.get("total"))
    except Exception:
        raise HTTPException(status_code=409, detail="INVALID_ORDER_TOTAL")

    if mode == "percent":
        if valf > 50:
            raise HTTPException(status_code=400, detail="INVALID_PERCENT_VALUE")
        amount = _round2(base_total * (valf / 100.0))
    else:
        amount = _round2(valf)

    opened = find_open_attendance_for_today(employee_id)
    if not opened or not isinstance(opened, dict) or "id" not in opened:
        raise HTTPException(status_code=409, detail="NO_OPEN_ATTENDANCE")
    att_id = opened["id"]

    att_ref = db.collection("attendance").document(att_id)
    att_doc = att_ref.get()
    if not att_doc.exists:
        raise HTTPException(status_code=404, detail="ATTENDANCE_NOT_FOUND")
    att = att_doc.to_dict() or {}

    tipped_orders = att.get("tipped_orders") or []
    if order_id in tipped_orders:
        raise HTTPException(status_code=409, detail="TIP_ALREADY_APPLIED_FOR_ORDER")

    tips_total = att.get("tips_total_ars", 0.0)
    try:
        tips_total = float(tips_total)
    except Exception:
        tips_total = 0.0

    new_total = _round2(tips_total + amount)
    tipped_orders.append(order_id)

    att_ref.update({
        "tips_total_ars": new_total,
        "tipped_orders": tipped_orders,
        "updated_at": iso_now(),
    })

    return {
        "order_id": order_id,
        "added_tip_amount": amount,
        "tips_total_ars": new_total,
        "mode": mode,
        "value": valf,
        "attendance_id": att_id,
    }

def _to_float(v, default=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default

def get_current_tips_total_service(uid: str) -> dict:
    opened = find_open_attendance_for_today(uid)
    if not opened or not isinstance(opened, dict) or "id" not in opened:
        return {
            "open": False,
            "attendance_id": None,
            "tips_total_ars": 0.0,
            "tipped_orders": []
        }

    att_id = opened["id"]
    doc = db.collection("attendance").document(att_id).get()
    if not doc.exists:
        return {
            "open": False,
            "attendance_id": None,
            "tips_total_ars": 0.0,
            "tipped_orders": []
        }

    att = doc.to_dict() or {}
    tips_total = _to_float(att.get("tips_total_ars", 0.0), 0.0)
    tipped_orders = att.get("tipped_orders") or []
    if not isinstance(tipped_orders, list):
        tipped_orders = []

    return {
        "open": True,
        "attendance_id": att_id,
        "tips_total_ars": round(tips_total, 2),
        "tipped_orders": tipped_orders
    }
