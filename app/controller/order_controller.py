from typing import List
from app.service.order_service import assign_employee_to_order, assign_order_to_table_service, create_order, delete_order_items, finalize_order, get_months_revenue_service, get_order_by_id, get_all_orders, add_items_to_order, get_average_per_person_service, get_average_per_order_service
from app.models.order import Order
from app.models.order import OrderItem
from app.controller.table_controller import associate_order_with_table_controller
from fastapi import HTTPException
from app.service.product_service import product_by_id
from app.service.table_service import get_table_by_id, update_table_status

def register_new_order(order: Order):
    order_data = order.dict()
    order_items = order_data.get('orderItems', [])
    
    if not order_items:
        raise HTTPException(status_code=400, detail="At least one order item is required")
    
    for item in order_items:
        product_id = item.get('product_id')
        if not product_id:
            raise HTTPException(status_code=400, detail="Product ID is required in the order item")

        product_data = product_by_id(product_id)
        
        print(f"Fetched product from database: {product_data}")

        product = product_data.get('product', {})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")

        product_name = item.get('product_name')
        product_price = item.get('product_price')

        if product_name != product.get('name'):
            raise HTTPException(status_code=400, detail=f"Product name for product ID {product_id} does not match")

        if product_price != str(product.get('price')): 
            raise HTTPException(status_code=400, detail=f"Product price for product ID {product_id} does not match")

    response = create_order(order_data)
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    
    return response

def finalize_order_controller(order_id: str):
    """
    Endpoint to finalize an order by ID.
    """
    try:
        # Call the service to finalize the order
        response = finalize_order(order_id)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_order_controller(order_id: str):
    try:
        response = get_order_by_id(order_id)
        if not response:
            raise HTTPException(status_code=404, detail="Order not found")
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_orders():
    try:
        response = get_all_orders()
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def add_order_items(order_id: str, new_order_items_data: List[dict], total: str):
    try:
        # Fetch the existing order
        existing_order = get_order_by_id(order_id)
        if not existing_order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Check if the order status is 'IN PROGRESS'
        if existing_order.get("status") != "IN PROGRESS":
            raise HTTPException(status_code=400, detail="Cannot add items to an order that is not in progress")

        # Convertir los datos de la solicitud en instancias de OrderItem
        new_order_items = [OrderItem(**item) for item in new_order_items_data]

        # Validar que cada product_id exista en la tabla de productos
        for item in new_order_items:
            product_id = item.product_id
            product = product_by_id(product_id)  # Fetch product details by product_id
            if "error" in product:
                raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")

        # Actualizar la orden con los nuevos ítems (que ya incluyen viejos y nuevos)
        response = add_items_to_order(order_id, new_order_items, total)
        return response
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def delete_order_items_controller(order_id: str, order_items: List[str]):
    try:
        # Fetch the existing order
        existing_order = get_order_by_id(order_id)
        if not existing_order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Check if the order status is 'IN PROGRESS'
        if existing_order.get("status") != "INACTIVE":
            raise HTTPException(status_code=400, detail="Cannot DELETE items to an order that is not in progress")

        # Convertir los datos de la solicitud en instancias de OrderItem

        # Actualizar la orden con los nuevos ítems (que ya incluyen viejos y nuevos)
        response = delete_order_items(order_id, order_items)
        return response
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_months_revenue():
    try:
        response = get_months_revenue_service()
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_average_per_person_controller(year: str, month: str):
    try:
        response = get_average_per_person_service(year, month)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_average_per_order_controller(year: str, month: str):
    try:
        response = get_average_per_order_service(year, month)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def assign_order_to_table_controller(order_id: str, table_id: int):
    try:
        response = assign_order_to_table_service(order_id, table_id)
        response2 = associate_order_with_table_controller(str(table_id), order_id)
        response["table"] = response2
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def assign_employee_to_order_controller(order_id, uid):
    try:
        response = assign_employee_to_order(str(order_id), uid)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))