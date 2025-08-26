from app.db.firebase import db
from app.models.category import Category
from fastapi import HTTPException

def get_next_id_from_existing():
    try:
        categories = db.collection('category').stream()
        
        existing_ids = [int(category.id) for category in categories if category.id.isdigit()]

        if existing_ids:
            next_id = max(existing_ids) + 1
        else:
            next_id = 1

        return next_id
    except Exception as e:
        raise Exception(f"Error retrieving next ID from existing categories: {str(e)}")


def create_category(category_data):
    try:
        next_id = get_next_id_from_existing()
        new_category_ref = db.collection('category').document(str(next_id))
        new_category_ref.set(category_data)

        return {"message": "Category added successfully", "id": next_id}
    except Exception as e:
        return {"error": str(e)}

def register_new_category(category: Category):
    if category.type == "Default":
        raise HTTPException(status_code=400, detail="Cannot create a category with type 'Default'")
    
    response = create_category(category.dict())
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    
    return {"message": "Category registered successfully", "id": response["id"]}

def update_category_name(category_id: str, new_name: str):
    try:
        category_ref = db.collection('category').document(category_id)
        category = category_ref.get()
        
        if not category.exists:
            raise HTTPException(status_code=404, detail="Category not found")
        
        category_data = category.to_dict()
        
        if category_data['type'] == "Default":
            raise HTTPException(status_code=400, detail="Cannot edit the name of a 'Default' category")
        
        category_ref.update({"name": new_name})
        
        return {"message": "Category name updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_categories():
    try:
        categories_ref = db.collection('category').stream()
        categories = []
        for category in categories_ref:
            cat = category.to_dict()
            cat['id'] = category.id
            categories.append(cat)
        return {"categories": categories}
    except Exception as e:
        return {"error": str(e)}

def get_category_by_id(category_id: str):

    try:
        category_ref = db.collection('category').document(category_id).get()
        if category_ref.exists:
            category = category_ref.to_dict()
            category['id'] = category_ref.id
            return category
        else:
            return None
    except Exception as e:
        return {"error": str(e)}

def delete_category_by_id(category_id: str):

    try:
        category_ref = db.collection('category').document(category_id)
        if category_ref.get().exists:
            category_ref.delete()
            return {"message": "Category deleted successfully"}
        else:
            return {"error": "Category not found"}
    except Exception as e:
        return {"error": str(e)}

def update_category_name(category_id: str, new_name: str):
    try:
        category_ref = db.collection('category').document(category_id)
        if category_ref.get().exists:
            category_ref.update({"name": new_name})
            return {"message": "Category name updated successfully"}
        else:
            return {"error": "Category not found"}
    except Exception as e:
        return {"error": str(e)}

def category_exists(category_id: int) -> bool:

    try:
        category_ref = db.collection('category').document(str(category_id))
        return category_ref.get().exists
    except Exception as e:
        raise Exception(f"Error al verificar la categoría con ID {category_id}: {str(e)}")

def check_multiple_categories_exist(category_str: str) -> bool:
    try:
        category_ids = [int(category_id.strip()) for category_id in category_str.split(",") if category_id.strip()]
        print(category_ids)
        for category_id in category_ids:
            exists = category_exists(category_id)
            if not exists:
                raise Exception(f"Category with id {category_id} does not exist.")
        return True
    except ValueError as e:
        raise Exception(f"Error al verificar múltiples categorías: {str(e)}")

def check_category_name_exists(category_name: str) -> bool:

    try:
        categories_ref = db.collection('category')
        matching_categories = categories_ref.where("name", "==", category_name).stream()

        if any(matching_categories):
            return True

        return False
    except Exception as e:
        raise Exception(f"Error checking if category name exists: {str(e)}")
