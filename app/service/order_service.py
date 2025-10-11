from calendar import monthrange
from typing import Dict, List
from app.db.firebase import db
from app.service.table_service import get_table_by_id
from app.models.order_item import OrderItem
from fastapi import HTTPException
from google.cloud.firestore_v1 import FieldFilter

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

def finalize_order(order_id: str):
    try:
        order_ref = db.collection('orders').document(order_id)
        snap = order_ref.get()
        if not snap.exists:
            raise HTTPException(status_code=404, detail="Order not found")

        order = snap.to_dict() or {}
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
        print(e)
        raise
    except Exception as e:
        print(e)
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
        
        order_ref.update(updated_order_data)
        return {"message": "Order updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def add_items_to_order(order_id: str, new_items: List[OrderItem], total: str):
    existing_order = get_order_by_id(order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_copy = existing_order.copy()
    order_copy["orderItems"] = [item.dict() for item in new_items]
    order_copy["total"] = total
    
    response = update_order(order_id, order_copy)

    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    
    return response

def delete_order_items(order_id: str, order_items: List[str]):
    order_ref = db.collection('orders').document(order_id)
    existing_order = order_ref.get()

    if not existing_order.exists:
        raise HTTPException(status_code=404, detail="Order not found")

    order_data = existing_order.to_dict()
    current_order_items = order_data.get('orderItems', [])

    updated_order_items = [
        item for item in current_order_items if item['product_id'] not in order_items
    ]

    order_ref.update({
        'orderItems': updated_order_items
    })

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

def assign_order_to_table_service(order_id: str, table_id: int):
    try:
        if not get_order_by_id(order_id):
            raise HTTPException(status_code=404, detail="Order not found")

        if get_order_by_id(order_id).get("status") != "INACTIVE":
            raise HTTPException(status_code=400, detail="Order status is not INACTIVE")

        if not get_table_by_id(table_id):
            raise HTTPException(status_code=404, detail="Table not found")

        if get_table_by_id(str(table_id)).get("status") != "FREE":
            raise HTTPException(status_code=400, detail="Table status is not FREE")

        order_ref = db.collection('orders').document(order_id)
        order_ref.update({
            "status": "IN PROGRESS",
            "tableNumber": table_id
        })

        return {"message": "Order assigned to table successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def assign_employee_to_order(order_id, uid):
    order_ref = db.collection("orders").document(order_id)  
    try:
        order_ref.update({
            "employee": uid
        })
        return {"message": "Employee assigned successfully"}
    except Exception as e:
        return {"error": str(e)}

