from app.service.product_service import check_product_in_in_progress_orders, check_product_name_exists, create_product, get_products_by_category, lower_stock, products, update_product_newprice, update_product_newdescription, delete_product, product_by_id, update_product_newcategories, add_calories, update_stock
from app.models.product import Product
from app.service.category_service import check_multiple_categories_exist
from fastapi import HTTPException

def register_new_product(product: Product):
    if product.name.strip() == "":
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    if check_product_name_exists(product.name):
        raise HTTPException(status_code=400, detail="Product name already exists")

    try:
        price = float(product.price)
    except ValueError:
        raise HTTPException(status_code=400, detail="Price must be a number")
    if price <= 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative or zero")

    category_str = str(product.category).strip()
    if not category_str:
        raise HTTPException(status_code=400, detail="Category cannot be empty")

    check = check_multiple_categories_exist(category_str)
    if isinstance(check, bool):
        if not check:
            raise HTTPException(status_code=400, detail="Category does not exist")
    else:
        if not check.get("ok", False):
            missing = ", ".join(check.get("missing", [])) or "unknown"
            raise HTTPException(status_code=400, detail=f"Category does not exist: {missing}")

    if float(product.calories) < 0:
        raise HTTPException(status_code=400, detail="Calories must be a positive number")

    if int(product.stock) < 0:
        raise HTTPException(status_code=400, detail="Stock must be >= 0")

    product_data = product.dict()
    product_data["category"] = category_str
    response = create_product(product_data)
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    return {"message": "Product registered successfully", "id": response["id"]}

def get_products():
    try:
        return products()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def update_product_price(product_id: str, new_price: str):
    try:
        price = float(new_price)
        if price <= 0:
            raise HTTPException(status_code=400, detail="Price cannot be negative or zero")
    except ValueError:
        raise HTTPException(status_code=400, detail="Price must be a number")

    resp = update_product_newprice(product_id, new_price)
    if "error" in resp:
        msg = resp["error"]
        if msg == "Product not found":
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=500, detail=msg)
    return resp

def update_product_description(product_id: str, new_description: str):
    if not new_description or not new_description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    resp = update_product_newdescription(product_id, new_description)
    if "error" in resp:
        msg = resp["error"]
        if msg == "Product not found":
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=500, detail=msg)
    return resp

def update_product_categories(product_id: str, newcategories: str):
    newcategories = (newcategories or "").strip()
    if not newcategories:
        raise HTTPException(status_code=400, detail="Category cannot be empty")
    check = check_multiple_categories_exist(newcategories)
    if isinstance(check, bool):
        if not check:
            raise HTTPException(status_code=400, detail="Category does not exist")
    else:
        if not check.get("ok", False):
            missing = ", ".join(check.get("missing", [])) or "unknown"
            raise HTTPException(status_code=400, detail=f"Category does not exist: {missing}")
    resp = update_product_newcategories(product_id, newcategories)
    if "error" in resp:
        msg = resp["error"]
        if msg == "Product not found":
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=500, detail=msg)
    return resp


def delete_product_by_id(product_id: str):
    try:
        response = delete_product(product_id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_product_by_id(product_id: str):
    try:
        response = product_by_id(product_id)
        if "error" in response:
            raise HTTPException(status_code=404, detail=response["error"])
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def add_food_calories(product_id: str, calories: float):
    try:
        if calories < 0:
            raise HTTPException(status_code=400, detail="Calories must be >= 0")
        response = add_calories(product_id, calories)
        if "error" in response:
            msg = response["error"]
            if msg == "Product not found":
                raise HTTPException(status_code=404, detail=msg)
            raise HTTPException(status_code=500, detail=msg)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_products_by_category_controller(category_id: str):
    try:
        response = get_products_by_category(category_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def check_product_in_in_progress_orders_controller():
    try:
        return check_product_in_in_progress_orders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def update_stock_controller(product_id, stock):
    try:
        add_units = int(stock)
        if add_units < 0:
            raise HTTPException(status_code=400, detail="Stock must be >= 0")
    except ValueError:
        raise HTTPException(status_code=400, detail="Stock must be an integer")

    resp = update_stock(product_id, stock)
    if "error" in resp:
        msg = resp["error"]
        if msg == "Product not found":
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=500, detail=msg)
    return resp

def lower_stock_controller(product_id, stock):
    try:
        sub_units = int(stock)
        if sub_units <= 0:
            raise HTTPException(status_code=400, detail="Stock to lower must be > 0")
    except ValueError:
        raise HTTPException(status_code=400, detail="Stock must be an integer")

    resp = lower_stock(product_id, stock)
    if "error" in resp:
        msg = resp["error"]
        if msg in ("Product not found", "Insufficient stock"):
            raise HTTPException(status_code=404 if msg=="Product not found" else 400, detail=msg)
        raise HTTPException(status_code=500, detail=msg)
    return resp