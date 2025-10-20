from calendar import monthrange
from typing import Dict, List
from app.db.firebase import db
from app.service.table_service import get_table_by_id
from app.models.order_item import OrderItem
from fastapi import HTTPException
from google.cloud.firestore_v1 import FieldFilter

def _is_admin(roles) -> bool:
    return "admin" in (roles or [])

def create_order(order_data):
    try:
        next_id = get_next_order_id_from_existing()
        orders_ref = db.collection('orders')
        new_order_ref = orders_ref.document(str(next_id))
        new_order_ref.set(order_data)
        return {
            "message": "Order created successfully",
            "order_id": next_id,
            "order": order_data
        }
    except Exception as e:
        return {"error": str(e)}

def _to_int_safe(v):
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        s = v.strip()
        if s.isdigit():
            return int(s)
        try:
            return int(float(s.replace(",", ".")))
        except:
            return 0
    return 0

def finalize_order_secure(order_id: str, actor_uid: str, actor_roles: list[str]):
    try:
        order_ref = db.collection('orders').document(order_id)
        snap = order_ref.get()
        if not snap.exists:
            raise HTTPException(status_code=404, detail="Order not found")
        order = snap.to_dict() or {}
        if order.get("status") != "IN PROGRESS":
            raise HTTPException(status_code=409, detail="Order is not in progress")
        employee_uid = (order.get("employee") or "").strip()
        if not employee_uid:
            raise HTTPException(status_code=400, detail="Employee UID missing in order")
        order_ref.update({"status": "FINALIZED"})
        user_ref = db.collection("users").document(employee_uid)
        user_snap = user_ref.get()
        if not user_snap.exists:
            raise HTTPException(status_code=404, detail="User not found")
        user = user_snap.to_dict() or {}
        current_global_points = _to_int_safe(user.get("globalPoints"))
        current_monthly_points = _to_int_safe(user.get("monthlyPoints"))
        user_ref.update({
            "globalPoints": str(current_global_points + 1),
            "monthlyPoints": str(current_monthly_points + 1)
        })
        return {"message": "Order finalized successfully, points updated"}
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

def get_order_by_id(order_id: str):
    try:
        order_ref = db.collection('orders').document(order_id)
        order_doc = order_ref.get()
        if not order_doc.exists:
            return None
        return order_doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving order: {str(e)}")

def get_all_orders():
    try:
        orders_ref = db.collection('orders').stream()
        orders_list = []
        for order in orders_ref:
            order_data = order.to_dict()
            order_data['id'] = order.id
            orders_list.append(order_data)
        return orders_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

def get_next_order_id_from_existing():
    try:
        orders = db.collection('orders').stream()
        existing_ids = [int(order.id) for order in orders if order.id.isdigit()]
        if existing_ids:
            next_id = max(existing_ids) + 1
        else:
            next_id = 1
        return next_id
    except Exception as e:
        raise Exception(f"Error retrieving next ID from existing products: {str(e)}")

def update_order(order_id: str, updated_order_data: dict):
    try:
        order_ref = db.collection('orders').document(order_id)
        if "employee" in updated_order_data:
            updated_order_data.pop("employee", None)
        order_ref.update(updated_order_data)
        return {"message": "Order updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _calc_items_sum(items):
    def _f(x):
        try:
            return float(x)
        except:
            return 0.0
    def _qty(q):
        try:
            return float(q)
        except:
            return 0.0
    s = 0.0
    for it in items or []:
        s += _f(it.get("product_price", "0")) * _qty(it.get("amount", 0))
    return round(s + 1e-9, 2)

def add_items_to_order_secure(order_id: str, new_items: List[dict], total: str, actor_uid: str, actor_roles: list[str]):
    existing_order = get_order_by_id(order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if existing_order.get("status") != "IN PROGRESS":
        raise HTTPException(status_code=400, detail="Cannot add items to an order that is not in progress")

    new_items_objs = [OrderItem(**item) for item in new_items]
    existing_items = existing_order.get("orderItems", []) or []
    new_items_list = [it.dict() for it in new_items_objs]
    merged_items = existing_items + new_items_list

    try:
        declared_total_new = float(total)
    except Exception:
        raise HTTPException(status_code=400, detail="new_order_total must be a number")

    sum_new_items = _calc_items_sum(new_items_list)
    if round(declared_total_new + 1e-9, 2) != sum_new_items:
        raise HTTPException(status_code=400, detail="new_order_total must match the sum of the new items")

    new_total_calc = _calc_items_sum(merged_items)

    order_copy = existing_order.copy()
    order_copy["orderItems"] = merged_items
    order_copy["total"] = str(new_total_calc)

    response = update_order(order_id, order_copy)
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    return response

def delete_order_items_secure(order_id: str, order_items: List[str], actor_uid: str, actor_roles: list[str]):
    order_ref = db.collection('orders').document(order_id)
    existing_order = order_ref.get()
    if not existing_order.exists:
        raise HTTPException(status_code=404, detail="Order not found")
    order_data = existing_order.to_dict()
    if order_data.get("status") != "IN PROGRESS":
        raise HTTPException(status_code=400, detail="Cannot DELETE items from an order that is not in progress")
    current_order_items = order_data.get('orderItems', []) or []
    updated_order_items = [
        item for item in current_order_items if item.get('product_id') not in order_items
    ]
    order_ref.update({'orderItems': updated_order_items})
    new_total = _calc_items_sum(updated_order_items)
    order_ref.update({'total': str(new_total)})
    return {"message": "Order items deleted successfully"}

def get_orders_by_status(status: str):
    try:
        orders_ref = (
            db.collection('orders')
              .where(filter=FieldFilter('status', '==', status))
              .stream()
        )
        orders_list = []
        for order in orders_ref:
            order_data = order.to_dict()
            order_data['id'] = order.id
            orders_list.append(order_data)
        return orders_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

def get_months_revenue_service():
    try:
        orders = db.collection('orders').stream()
        months_revenue = {}
        for order in orders:
            order_data = order.to_dict()
            date = order_data.get('date')
            month = date.split('-')[1]
            year = date.split('-')[0]
            month_year = f"{year}-{month}"
            total = order_data.get('total')
            if month_year in months_revenue:
                months_revenue[month_year] += float(total)
            else:
                months_revenue[month_year] = float(total)
        return months_revenue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

def get_average_per_person_service(year: str, month: str) -> Dict[str, float]:
    try:
        m = f"{int(month):02d}"
        _, num_days = monthrange(int(year), int(m))
        average_per_person = {f"{year}-{m}-{day:02d}": 0 for day in range(1, num_days + 1)}
        orders = (
            db.collection('orders')
              .where(filter=FieldFilter('date', '>=', f"{year}-{m}-01"))
              .where(filter=FieldFilter('date', '<=', f"{year}-{m}-{num_days:02d}"))
              .stream()
        )
        daily_totals = {f"{year}-{m}-{day:02d}": [] for day in range(1, num_days + 1)}
        for order in orders:
          order_data = order.to_dict()
          date = order_data.get('date')
          total = order_data.get('total')
          amount_of_people = order_data.get('amountOfPeople')
          try:
              total = float(total)
          except (TypeError, ValueError):
              continue
          if amount_of_people and amount_of_people > 0 and date in daily_totals:
              average = total / amount_of_people
              daily_totals[date].append(average)
        for day, averages in daily_totals.items():
            if averages:
                average_per_person[day] = sum(averages)
        return average_per_person
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

def get_average_per_order_service(year: str, month: str) -> Dict[str, float]:
    try:
        m = f"{int(month):02d}"
        _, num_days = monthrange(int(year), int(m))
        average_per_order = {f"{year}-{m}-{day:02d}": 0 for day in range(1, num_days + 1)}
        orders = (
            db.collection('orders')
              .where(filter=FieldFilter('date', '>=', f"{year}-{m}-01"))
              .where(filter=FieldFilter('date', '<=', f"{year}-{m}-{num_days:02d}"))
              .stream()
        )
        daily_totals = {f"{year}-{m}-{day:02d}": [] for day in range(1, num_days + 1)}
        for order in orders:
            order_data = order.to_dict()
            date = order_data.get('date')
            total = order_data.get('total')
            try:
                total = float(total)
            except (TypeError, ValueError):
                continue
            if date in daily_totals:
                daily_totals[date].append(total)
        for day, totals in daily_totals.items():
            if totals:
                average_per_order[day] = sum(totals) / len(totals)
        return average_per_order
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

def assign_order_to_table_service_secure(order_id: str, table_id: int, actor_uid: str, actor_roles: list[str]):
    try:
        # Validaciones rápidas fuera de la tx (lecturas no-atomicas, solo para filtrar)
        order = get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.get("status") != "INACTIVE":
            raise HTTPException(status_code=400, detail="Order status is not INACTIVE")

        if not get_table_by_id(table_id):
            raise HTTPException(status_code=404, detail="Table not found")
        table = get_table_by_id(str(table_id))
        if table.get("status") != "FREE":
            raise HTTPException(status_code=400, detail="Table status is not FREE")

        # Refs
        order_ref = db.collection('orders').document(order_id)
        table_ref = db.collection('tables').document(str(table_id))

        # Transacción para actualizar ambos docs de forma atómica
        tx = db.transaction()

        # Releer dentro de la transacción y validar nuevamente (estado consistente)
        ord_snap = tx.get(order_ref)
        tbl_snap = tx.get(table_ref)
        if not ord_snap.exists:
            raise HTTPException(status_code=404, detail="Order not found")
        if not tbl_snap.exists:
            raise HTTPException(status_code=404, detail="Table not found")

        ord_data = ord_snap.to_dict() or {}
        tbl_data = tbl_snap.to_dict() or {}

        if ord_data.get("status") != "INACTIVE":
            raise HTTPException(status_code=400, detail="Order status is not INACTIVE")
        if tbl_data.get("status") != "FREE":
            raise HTTPException(status_code=400, detail="Table status is not FREE")

        # Updates atómicos
        tx.update(order_ref, {
            "status": "IN PROGRESS",
            "tableNumber": int(table_id)
        })
        tx.update(table_ref, {
            "status": "BUSY",
            "order_id": int(order_id)
        })

        # Confirmar
        tx.commit()

        return {"message": "Order assigned to table successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def assign_employee_to_order_secure(order_id: str, target_uid: str, actor_uid: str, actor_roles: list[str]):
    order_ref = db.collection("orders").document(order_id)
    snap = order_ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Order not found")
    order = snap.to_dict() or {}
    current_owner = (order.get("employee") or "").strip()
    if not _is_admin(actor_roles):
        if target_uid != actor_uid:
            raise HTTPException(status_code=403, detail="Forbidden: self-assignment only")
        if current_owner and current_owner != actor_uid and (order.get("status") != "INACTIVE"):
            raise HTTPException(status_code=403, detail="Forbidden: order already assigned to another employee")
    try:
        order_ref.update({"employee": target_uid})
        return {"message": "Employee assigned successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
