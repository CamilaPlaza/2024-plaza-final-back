from calendar import monthrange
from typing import Dict, List
from app.db.firebase import db
from app.service.table_service import get_table_by_id
from app.models.order_item import OrderItem
from fastapi import HTTPException

def create_order(order_data):
    try:
        next_id = get_next_order_id_from_existing()
        
        orders_ref = db.collection('orders')
        new_order_ref = orders_ref.document(str(next_id))
        new_order_ref.set(order_data)

        # Cambiar el estado de la mesa a 'BUSY'
        '''print(table_id)
        if table_id:
            update_table_status(table_id, "BUSY")'''

        return {
            "message": "Order created successfully",
            "order_id": next_id,  # Devuelve el ID de la nueva orden
            "order": order_data  # También puedes devolver los datos de la orden
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
        # Obtener todos los documentos de la colección 'products'
        orders = db.collection('orders').stream()

        # Extraer los IDs existentes y convertirlos a enteros
        existing_ids = [int(order.id) for order in orders if order.id.isdigit()]

        if existing_ids:
            # Encontrar el mayor ID existente y sumar 1
            next_id = max(existing_ids) + 1
        else:
            # Si no hay IDs, comenzamos desde 1
            next_id = 1

        return next_id
    except Exception as e:
        raise Exception(f"Error retrieving next ID from existing products: {str(e)}")

def update_order(order_id: str, updated_order_data: dict):
    try:
        # Reference to the order in the database
        order_ref = db.collection('orders').document(order_id)
        
        # Perform the update in the database
        order_ref.update(updated_order_data)
        return {"message": "Order updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def add_items_to_order(order_id: str, new_items: List[OrderItem], total: str):
    existing_order = get_order_by_id(order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Preparar los datos de la orden actualizados con los nuevos ítems (viejos y nuevos ya incluidos en 'new_items')
    order_copy = existing_order.copy()
    order_copy["orderItems"] = [item.dict() for item in new_items]  # Reemplazar directamente los ítems
    order_copy["total"] = total  # Actualizar el total
    
    # Actualizar la orden en la base de datos
    response = update_order(order_id, order_copy)

    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    
    return response

def delete_order_items(order_id: str, order_items: List[str]):
    # Obtener la orden existente
    order_ref = db.collection('orders').document(order_id)
    existing_order = order_ref.get()

    if not existing_order.exists:
        raise HTTPException(status_code=404, detail="Order not found")

    # Obtener los orderItems de la orden
    order_data = existing_order.to_dict()
    current_order_items = order_data.get('orderItems', [])

    # Filtrar los orderItems que no estén en la lista order_items
    updated_order_items = [
        item for item in current_order_items if item['product_id'] not in order_items
    ]

    # Actualizar la orden con los nuevos orderItems
    order_ref.update({
        'orderItems': updated_order_items
    })

    return {"message": "Order items deleted successfully"}

def get_orders_by_status(status: str):
    """
    Retrieves all orders from the 'orders' collection with the specified status.
    """
    try:
        orders_ref = db.collection('orders').where('status', '==', status).stream()
        orders_list = []

        for order in orders_ref:
            order_data = order.to_dict()
            order_data['id'] = order.id  # Add the document ID to the order data
            orders_list.append(order_data)
        return orders_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

def get_months_revenue_service():
    try:
        #necesito ver todas las ordenes de mi base y armar una lista que asocie mes con el total de plata de cada orden en el mes
        #en este caso, lo que me interesa es el mes y el total de plata
        #la lista lo construyo con un diccionario donde la llave es el mes y el valor es el total de plata

        orders = db.collection('orders').stream()
        months_revenue = {}
        for order in orders:
            order_data = order.to_dict()
            date = order_data.get('date')
            #necesito mes y año juntos
            #ejemplo: 2022-01
            #ejemplo: 2022-02
            # i need to join month and year together
            # example: 2022-01
            # example: 2022-02
            #
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
        _, num_days = monthrange(int(year), int(month))

        average_per_person = {f"{year}-{int(month):02d}-{day:02d}": 0 for day in range(1, num_days + 1)}

        # Query orders within the specified month
        orders = db.collection('orders') \
                   .where('date', '>=', f"{year}-{month}-01") \
                   .where('date', '<=', f"{year}-{month}-{num_days}") \
                   .stream()

        # Dictionary to accumulate the sum of averages per day
        daily_totals = {f"{year}-{int(month):02d}-{day:02d}": [] for day in range(1, num_days + 1)}

        for order in orders:
            order_data = order.to_dict()
            date = order_data.get('date')
            total = order_data.get('total')
            amount_of_people = order_data.get('amountOfPeople')

            # Ensure that total is converted to float
            try:
                total = float(total)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid total value: {total}")

            # Ensure amount_of_people is valid
            if amount_of_people > 0:
                average = total / amount_of_people
                if date in daily_totals:
                    daily_totals[date].append(average)

        # Calculate the sum of averages for each day
        for day, averages in daily_totals.items():
            if averages:  # Only sum if there are averages for that day
                average_per_person[day] = sum(averages)

        return average_per_person
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

def get_average_per_order_service(year: str, month: str) -> Dict[str, float]:
    # i need to get the average per order so, sum all the orders totals and divide by the amount of orders
    try:
        _, num_days = monthrange(int(year), int(month))

        average_per_order = {f"{year}-{int(month):02d}-{day:02d}": 0 for day in range(1, num_days + 1)}

        # Query orders within the specified month
        orders = db.collection('orders') \
                   .where('date', '>=', f"{year}-{month}-01") \
                   .where('date', '<=', f"{year}-{month}-{num_days}") \
                   .stream()

        # Dictionary to accumulate the sum of averages per day
        daily_totals = {f"{year}-{int(month):02d}-{day:02d}": [] for day in range(1, num_days + 1)}

        for order in orders:
            order_data = order.to_dict()
            date = order_data.get('date')
            total = order_data.get('total')

            # Ensure that total is converted to float
            try:
                total = float(total)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid total value: {total}")

            daily_totals[date].append(total)

        # Calculate the sum of averages for each day
        for day, totals in daily_totals.items():
            if totals:  # Only sum if there are totals for that day
                average = sum(totals) / len(totals)
                average_per_order[day] = average

        return average_per_order
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

def assign_order_to_table_service(order_id: str, table_id: int):
    try:
        #el estado de a orden que me llega tiene ser "INACTIVE" porque significa que no tiene una mesa asignada, la mesa se asigna con el table_id, y deberia chequear que este free esa mesa

        #verifico que la orden exista
        if not get_order_by_id(order_id):
            raise HTTPException(status_code=404, detail="Order not found")
        #verifico que tenga status inactive
        if get_order_by_id(order_id).get("status") != "INACTIVE":
            raise HTTPException(status_code=400, detail="Order status is not INACTIVE")
        #verifico que la mesa exista
        if not get_table_by_id(table_id):
            raise HTTPException(status_code=404, detail="Table not found")
        #verifico que la mesa tenga status FREE
        if get_table_by_id(str(table_id)).get("status") != "FREE":
            raise HTTPException(status_code=400, detail="Table status is not FREE")
        #entonces ahora si puedo a la orden ponerle estado "IN PROGRESS" y asignarle el tableNumber a la orden

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

