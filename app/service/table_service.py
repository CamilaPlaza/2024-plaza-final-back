from fastapi import HTTPException
from app.db.firebase import db

def get_next_table_id():
    try:
        tables_ref = db.collection("tables")
        tables = tables_ref.stream()
        ids = [int(doc.id) for doc in tables if doc.id.isdigit()]
        return str(max(ids) + 1) if ids else "1"
    except Exception as e:
        raise Exception(f"Error al calcular el próximo ID de mesa: {str(e)}")

def create_table(table_data):
    try:
        next_id = get_next_table_id()
        new_table_ref = db.collection("tables").document(next_id)
        new_table_ref.set(table_data)
        return {"message": "Mesa creada correctamente", "id": next_id}
    except Exception as e:
        return {"error": str(e)}

def get_tables_service():
    try:
        tables_ref = db.collection('tables').stream()
        tables = []
        for table in tables_ref:
            tab = table.to_dict()
            tab['id'] = table.id
            tables.append(tab)
        return tables
    except Exception as e:
        return {"error": str(e)}

def get_table_by_id(table_id: str):
    try:
        table_ref = db.collection('tables').document(table_id).get()
        if table_ref.exists:
            table = table_ref.to_dict()
            table['id'] = table_ref.id
            return table
        else:
            return None
    except Exception as e:
        return {"error": str(e)}

def update_table_status(table_id: str, new_status: str):
    try:
        tables_ref = db.collection('tables').document(table_id)
        if tables_ref.get().exists:
            tables_ref.update({"status": new_status})
            return {"message": "Table status updated successfully"}
        else:
            return {"error": "Table not found"}
    except Exception as e:
        return {"error": str(e)}

def associate_order_with_table(table_id: str, order_id: str):
    try:
        table_ref = db.collection('tables').document(table_id)
        doc = table_ref.get()
        if not doc.exists:
            return {"error": "Table not found"}

        order_id_int = int(order_id)
        table_ref.update({"order_id": order_id_int})
        update_table_status(table_id, "BUSY")
        return {"message": "Order associated with table successfully"}
    except Exception as e:
        return {"error": str(e)}

def close_table_service(table_id: str):
    try:
        table_ref = db.collection('tables').document(str(table_id))
        table_doc = table_ref.get()
        if not table_doc.exists:
            raise HTTPException(status_code=404, detail="Table not found")

        table_ref.update({
            "status": "FINISHED",
            "order_id": 0
        })
        return {"message": "Table closed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def clean_table_service(table_id: str):
    try:
        table_ref = db.collection('tables').document(str(table_id))
        table_doc = table_ref.get()
        if not table_doc.exists:
            raise HTTPException(status_code=404, detail="Table not found")

        table_ref.update({
            "status": "FREE",
            "order_id": 0
        })
        return {"message": "Table cleaned successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
