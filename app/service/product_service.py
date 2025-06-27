from app.db.firebase import db

def get_next_product_id_from_existing():
    """
    Obtiene el próximo ID disponible en la colección 'products'.
    """
    try:
        # Obtener todos los documentos de la colección 'products'
        products = db.collection('products').stream()

        # Extraer los IDs existentes y convertirlos a enteros
        existing_ids = [int(product.id) for product in products if product.id.isdigit()]

        if existing_ids:
            # Encontrar el mayor ID existente y sumar 1
            next_id = max(existing_ids) + 1
        else:
            # Si no hay IDs, comenzamos desde 1
            next_id = 1

        return next_id
    except Exception as e:
        raise Exception(f"Error retrieving next ID from existing products: {str(e)}")


def create_product(product_data):
    try:
        next_id = get_next_product_id_from_existing()

        if 'category' in product_data:
            product_data['category'] = str(product_data['category'])

        new_product_ref = db.collection('products').document(str(next_id))
        new_product_ref.set(product_data)

        return {"message": "Product added successfully", "id": next_id}
    except Exception as e:
        return {"error": str(e)}



def products():
    try:
        products_ref = db.collection('products')
        products = products_ref.stream()
        product_list = []

        for product in products:
            product_dict = product.to_dict()
            product_dict['id'] = product.id
            product_list.append(product_dict)
            
        return {"products": product_list, "message": "Products retrieved successfully"}
    except Exception as e:
        return {"error": str(e)}  # Removed the status code tuple


def update_product_newprice(product_id: str, new_price):
    try:
        product_ref = db.collection('products').document(product_id)
        product_ref.update({"price": new_price})
        return {"message": "Product price updated successfully"}
    except Exception as e:
        return {"error": str(e)}


def update_product_newdescription(product_id, new_description):
    try:
        # Referencia al documento del producto que se va a actualizar
        product_ref = db.collection('products').document(product_id)

        # Actualización solo del campo 'description'
        product_ref.update({
            'description': new_description
        })

        return {"message": "Product description updated successfully"}
    except Exception as e:
        return {"error": str(e)}
    
def update_product_newcategories(product_id, new_categories):
    try:
        # Referencia al documento del producto que se va a actualizar
        product_ref = db.collection('products').document(product_id)

        # Actualización solo del campo 'category'
        product_ref.update({
            'category': new_categories  # Assuming new_categories is a comma-separated string
        })

        return {"message": "Product categories updated successfully"}
    except Exception as e:
        return {"error": str(e)}

def delete_product(product_id: str):
    product_ref = db.collection('products').document(product_id)
    product_doc = product_ref.get()
    if not product_doc.exists:
        raise ValueError("Product not found")
    product_ref.delete()
    return {"message": "Product deleted successfully"}


def product_by_id(product_id: str):
    try:
        # Retrieve the document reference
        product_ref = db.collection('products').document(product_id)
        product_doc = product_ref.get()

        if not product_doc.exists:
            return {"error": "Product not found"}
        
        product_data = product_doc.to_dict()
        product_data['id'] = product_id
        
        return {"product": product_data, "message": "Product retrieved successfully"}
    except Exception as e:
        return {"error": str(e)}

def add_calories(product_id: str, calories: float):
    try:
        product_ref = db.collection('products').document(product_id)
        product_ref.update({"calories": calories})
        return {"message": "Product calories updated successfully"}
    except Exception as e:
        return {"error": str(e)}

def check_product_name_exists(product_name: str):
    """
    Verifica si ya existe un producto con el nombre dado en la base de datos.
    """
    try:
        # Realizar una consulta en la colección 'products' para buscar coincidencias de nombre
        products_ref = db.collection('products')
        matching_products = products_ref.where("name", "==", product_name).stream()

        # Verificar si existe al menos un producto con el mismo nombre
        if any(matching_products):  # Si hay productos que coinciden
            return True

        # Si no hay coincidencias, retornamos False
        return False
    except Exception as e:
        raise Exception(f"Error checking if product name exists: {str(e)}")

def get_products_by_category(category_ids_str: str):
    try:
        # Reference to the 'products' collection
        category_ids = category_ids_str.split(', ')
        products_ref = db.collection('products')
        products = products_ref.stream()

        # Filter products by the provided category IDs
        filtered_products = []
        for product in products:
            product_data = product.to_dict()
            
            # Add the Firestore document ID to the product data
            product_data['id'] = product.id  
            
            # Split the product's categories and check if any match the input category_ids
            product_categories = product_data['category'].split(', ')
            if any(category_id in product_categories for category_id in category_ids):
                filtered_products.append(product_data)

        # Raise an exception if no products are found for the given categories
        if not filtered_products:
            raise Exception(f"No products found for categories {', '.join(category_ids)}")

        return filtered_products

    except Exception as e:
        raise Exception(f"Error retrieving products by categories: {str(e)}")
def check_product_in_in_progress_orders():
    """
    Retrieves all products that are present in any 'IN PROGRESS' orders.
    """
    try:
        # Referencia a la colección 'orders' en Firestore
        orders_ref = db.collection('orders')
        
        # Consulta para obtener todas las órdenes que están 'IN PROGRESS'
        in_progress_orders = orders_ref.where("status", "==", "IN PROGRESS").stream()

        # Lista para almacenar todos los productos de las órdenes "IN PROGRESS"
        products_in_orders = []

        # Recorremos cada orden en progreso y obtenemos los productos de los orderItems
        for order in in_progress_orders:
            order_data = order.to_dict()
            for item in order_data.get('orderItems', []):
                products_in_orders.append(item)

        # Verificamos si no se encontró ningún producto
        if not products_in_orders:
            raise Exception("No products found in 'IN PROGRESS' orders")

        return products_in_orders

    except Exception as e:
        raise Exception(f"Error retrieving products from 'IN PROGRESS' orders: {str(e)}")

def update_stock(product_id: str, new_stock: str):
    try:
        product_ref = db.collection('products').document(product_id)
        
        # Retrieve the current stock and convert to integer
        current_stock = int(product_ref.get().to_dict()["stock"])
        
        # Convert new_stock to integer and add to current stock
        updated_stock = current_stock + int(new_stock)
        
        # Update the stock in the database
        product_ref.update({"stock": str(updated_stock)})
        
        return {"message": "Product stock updated successfully"}
    except Exception as e:
        return {"error": str(e)}

    
def lower_stock(product_id: str, new_stock: str):
    try:
        product_ref = db.collection('products').document(product_id)
        
        # Retrieve the current stock and convert to integer
        current_stock = int(product_ref.get().to_dict()["stock"])
        
        # Convert new_stock to integer and add to current stock
        updated_stock = current_stock - int(new_stock)
        
        # Update the stock in the database
        product_ref.update({"stock": str(updated_stock)})
        
        return {"message": "Product stock updated successfully"}
    except Exception as e:
        return {"error": str(e)}