from app.db.firebase import db

def get_next_product_id_from_existing():
    try:
        products = db.collection('products').stream()
        existing_ids = [int(product.id) for product in products if product.id.isdigit()]

        if existing_ids:
            next_id = max(existing_ids) + 1
        else:
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
        return {"error": str(e)}

def update_product_newprice(product_id: str, new_price):
    try:
        product_ref = db.collection('products').document(product_id)
        snap = product_ref.get()
        if not snap.exists:
            return {"error": "Product not found"}
        product_ref.update({"price": new_price})
        return {"message": "Product price updated successfully"}
    except Exception as e:
        return {"error": str(e)}

def update_product_newdescription(product_id, new_description):
    try:
        product_ref = db.collection('products').document(product_id)
        snap = product_ref.get()
        if not snap.exists:
            return {"error": "Product not found"}
        product_ref.update({'description': new_description})
        return {"message": "Product description updated successfully"}
    except Exception as e:
        return {"error": str(e)}
    
def update_product_newcategories(product_id, new_categories):
    try:
        product_ref = db.collection('products').document(product_id)
        snap = product_ref.get()
        if not snap.exists:
            return {"error": "Product not found"}
        product_ref.update({'category': new_categories})
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
    try:
        products_ref = db.collection('products')
        matching_products = products_ref.where("name", "==", product_name).stream()

        if any(matching_products):
            return True

        return False
    except Exception as e:
        raise Exception(f"Error checking if product name exists: {str(e)}")

def get_products_by_category(category_ids_str: str):
    try:
        category_ids = category_ids_str.split(', ')
        products_ref = db.collection('products')
        products = products_ref.stream()

        filtered_products = []
        for product in products:
            product_data = product.to_dict()
            
            product_data['id'] = product.id  
            
            product_categories = product_data['category'].split(', ')
            if any(category_id in product_categories for category_id in category_ids):
                filtered_products.append(product_data)

        if not filtered_products:
            raise Exception(f"No products found for categories {', '.join(category_ids)}")

        return filtered_products

    except Exception as e:
        raise Exception(f"Error retrieving products by categories: {str(e)}")
    
def check_product_in_in_progress_orders():

    try:
        orders_ref = db.collection('orders')
        in_progress_orders = orders_ref.where("status", "==", "IN PROGRESS").stream()
        products_in_orders = []

        for order in in_progress_orders:
            order_data = order.to_dict()
            for item in order_data.get('orderItems', []):
                products_in_orders.append(item)

        if not products_in_orders:
            raise Exception("No products found in 'IN PROGRESS' orders")

        return products_in_orders

    except Exception as e:
        raise Exception(f"Error retrieving products from 'IN PROGRESS' orders: {str(e)}")

def update_stock(product_id: str, new_stock: str):
    try:
        product_ref = db.collection('products').document(product_id)
        snap = product_ref.get()
        if not snap.exists:
            return {"error": "Product not found"}

        data = snap.to_dict() or {}
        current_stock = int(data.get("stock", "0"))
        updated_stock = current_stock + int(new_stock)
        product_ref.update({"stock": str(updated_stock)})
        return {"message": "Product stock updated successfully"}
    except Exception as e:
        return {"error": str(e)}
 
def lower_stock(product_id: str, new_stock: str):
    try:
        product_ref = db.collection('products').document(product_id)
        snap = product_ref.get()
        if not snap.exists:
            return {"error": "Product not found"}

        data = snap.to_dict() or {}
        current_stock = int(data.get("stock", "0"))
        updated_stock = current_stock - int(new_stock)
        if updated_stock < 0:
            return {"error": "Insufficient stock"}
        product_ref.update({"stock": str(updated_stock)})
        return {"message": "Product stock updated successfully"}
    except Exception as e:
        return {"error": str(e)}    

def check_multiple_categories_exist(category_ids_str: str) -> dict:
    ids = [c.strip() for c in category_ids_str.split(',') if c.strip()]
    missing = []
    for cid in ids:
        if not db.collection('categories').document(cid).get().exists:
            missing.append(cid)
    return {"ok": len(missing) == 0, "missing": missing}