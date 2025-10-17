from app.service.category_service import check_category_name_exists, create_category, get_categories, get_category_by_id, delete_category_by_id, update_category_name
from app.models.category import Category
from fastapi import HTTPException
from app.service.order_service import get_orders_by_status
from app.service.product_service import product_by_id

def register_new_category(category: Category):
    if not isinstance(category.type, str):
        raise HTTPException(status_code=400, detail="Category type must be a string")
    if category.type == "Default":
        raise HTTPException(status_code=400, detail="Category type cannot be 'Default'")
    if category.type != "Custom":
        category.type = "Custom"
    if not category.name or category.name.strip() == "":
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    if check_category_name_exists(category.name.strip()):
        raise HTTPException(status_code=400, detail="Category name already exists")
    resp = create_category(category.dict())
    if isinstance(resp, dict) and "error" in resp:
        raise HTTPException(status_code=500, detail=resp["error"])
    return {"message": "Category registered successfully", "id": resp["id"]}

def get_all_categories():
    resp = get_categories()
    if isinstance(resp, dict) and "error" in resp:
        raise HTTPException(status_code=500, detail=resp["error"])
    return resp

def get_category_by_id_controller(category_id: str):
    cat = get_category_by_id(category_id)
    if isinstance(cat, dict) and "error" in cat:
        raise HTTPException(status_code=500, detail=cat["error"])
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat

def delete_category_controller(category_id: str):
    cat = get_category_by_id(category_id)
    if isinstance(cat, dict) and "error" in cat:
        raise HTTPException(status_code=500, detail=cat["error"])
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if cat.get('type') == "Default":
        raise HTTPException(status_code=400, detail="Cannot delete a 'Default' category")
    resp = delete_category_by_id(category_id)
    if isinstance(resp, dict) and "error" in resp:
        if resp["error"] == "Category not found":
            raise HTTPException(status_code=404, detail=resp["error"])
        raise HTTPException(status_code=500, detail=resp["error"])
    return resp

def update_category_name_controller(category_id: str, new_name: str):
    cat = get_category_by_id(category_id)
    if isinstance(cat, dict) and "error" in cat:
        raise HTTPException(status_code=500, detail=cat["error"])
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if cat.get('type') == "Default":
        raise HTTPException(status_code=400, detail="Cannot edit the name of a 'Default' category")
    if not new_name or new_name.strip() == "":
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    new_name_norm = new_name.strip()
    if new_name_norm == cat.get("name"):
        return {"message": "Category name updated successfully"}
    if check_category_name_exists(new_name_norm):
        raise HTTPException(status_code=400, detail="Category name already exists")
    resp = update_category_name(category_id, new_name_norm)
    if isinstance(resp, dict) and "error" in resp:
        if resp["error"] == "Category not found":
            raise HTTPException(status_code=404, detail=resp["error"])
        raise HTTPException(status_code=500, detail=resp["error"])
    return resp

def get_category_revenue_controller():
    try:
        orders = get_orders_by_status('FINALIZED')
        category_revenue = {}
        prod_cache = {}
        cat_cache = {}
        for order in orders or []:
            for item in order.get('orderItems', []):
                product_id = item.get('product_id')
                amount = item.get('amount', 0)
                if product_id in prod_cache:
                    prod = prod_cache[product_id]
                else:
                    prod = product_by_id(product_id)
                    prod_cache[product_id] = prod
                if not isinstance(prod, dict) or 'product' not in prod:
                    continue
                product_data = prod['product']
                category_field = product_data.get('category')
                if isinstance(category_field, str):
                    cats = [c.strip() for c in category_field.split(',') if c.strip()]
                elif isinstance(category_field, list):
                    cats = category_field
                else:
                    cats = []
                try:
                    price = float(product_data.get('price', 0))
                    cost  = float(product_data.get('cost', 0))
                    margin = (price - cost) * float(amount or 0)
                except Exception:
                    margin = 0
                for cat_id in cats:
                    if cat_id in cat_cache:
                        cat = cat_cache[cat_id]
                    else:
                        cat = get_category_by_id(cat_id)
                        cat_cache[cat_id] = cat
                    if not cat or (isinstance(cat, dict) and "error" in cat):
                        continue
                    cat_name = cat.get('name')
                    if not cat_name:
                        continue
                    category_revenue[cat_name] = category_revenue.get(cat_name, 0) + margin
        return category_revenue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating category revenue: {str(e)}")
