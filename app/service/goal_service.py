from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi import HTTPException
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from app.db.firebase import db
from app.models.goal import Goal
from app.service.product_service import products


def create_goal(goal: Goal):
    try:
        next_id = get_next_goal_id()
        goal_data = goal.dict(by_alias=True, exclude_unset=True)

        # Normalizar categoryId a None o str
        category_id = goal_data.get('categoryId')
        if category_id is None:
            goal_data['categoryId'] = None
        elif not isinstance(category_id, str):
            raise Exception("categoryId must be a string or None")

        # Guardar
        db.collection('goals').document(str(next_id)).set(goal_data)
        return next_id
    except Exception as e:
        # En create podemos devolver mensaje 500 controlado
        raise HTTPException(status_code=500, detail=str(e))


def get_next_goal_id() -> int:
    try:
        goals = db.collection('goals').stream()
        existing = [int(doc.id) for doc in goals if doc.id.isdigit()]
        return max(existing) + 1 if existing else 1
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving next ID from existing goals: {str(e)}")


def get_category_product_mapping() -> Dict[str, str]:
    """
    Mapea category_id -> 'productId1,productId2,...'
    """
    try:
        products_response = products()  # debe devolver {"products": [...]}
        products_list = products_response.get("products", [])

        category_to_products = defaultdict(set)
        for prod in products_list:
            product_id = prod.get('id')
            categories_str = prod.get('category', '') or ''
            for cat in categories_str.split(','):
                cat = cat.strip()
                if cat and product_id:
                    category_to_products[cat].add(product_id)

        # sets -> string
        return {k: ','.join(sorted(v)) for k, v in category_to_products.items()}
    except Exception as e:
        # Si esto falla, levantamos error para que el front lo reciba como 500
        raise HTTPException(status_code=500, detail=str(e))


def _parse_order_date(value: Any) -> Optional[datetime]:
    """
    Convierte el campo 'date' de la orden a datetime.
    Soporta:
      - firestore.Timestamp
      - string 'YYYY-MM-DD' (o variantes comunes)
    Devuelve None si no puede parsear.
    """
    if value is None:
        return None

    # Firestore Timestamp
    if hasattr(value, "to_datetime"):
        try:
            return value.to_datetime()
        except Exception:
            pass

    # String
    if isinstance(value, str):
        # Intentos más comunes
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value[:10], fmt)  # cortar posible tiempo
            except Exception:
                continue

    return None


def goals(monthYear: str) -> List[dict]:
    """
    Devuelve las metas del mes 'MM/YY' con el campo actualIncome calculado.
    Evita índices compuestos: consulta FINALIZED y filtra rango por fecha en Python.
    """
    try:
        # Calcular rango de mes
        start_date = datetime.strptime(monthYear, "%m/%y")
        end_date = (start_date.replace(day=28) + timedelta(days=4))  # próximo mes
        end_date = end_date.replace(day=1) - timedelta(days=1)       # último día del mes (23:59:59 concepto)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Traer goals del mes
        goals_q = db.collection('goals').where(filter=FieldFilter('date', '==', monthYear)).stream()

        category_products = get_category_product_mapping()
        out: List[dict] = []

        # Traer órdenes FINALIZED (sin rango de fecha → NO necesita índice compuesto)
        orders_iter = db.collection('orders').where(
            filter=FieldFilter('status', '==', 'FINALIZED')
        ).stream()

        # Para no re-streamear por cada goal, materializamos una lista liviana con lo necesario
        orders_cache = []
        for order_doc in orders_iter:
            od = order_doc.to_dict()
            orders_cache.append({
                "total": float(od.get('total', 0) or 0),
                "date": od.get('date'),
                "items": od.get('orderItems', [])
            })

        for goal_doc in goals_q:
            g = goal_doc.to_dict()
            g['id'] = goal_doc.id

            actual_income = 0.0
            category_id = g.get('categoryId')  # None o str
            associated_products = []
            if category_id:
                associated_products = (category_products.get(str(category_id), "") or "").split(',')
                associated_products = [p.strip() for p in associated_products if p.strip()]

            # Filtrar por fecha en Python y acumular income
            for od in orders_cache:
                order_dt = _parse_order_date(od["date"])
                if not order_dt:
                    continue
                if not (start_date <= order_dt <= end_date):
                    continue

                if not category_id:
                    # Meta general: sumar el total de la orden
                    actual_income += od["total"]
                else:
                    # Meta por categoría: sumar por items que pertenezcan a esa categoría
                    for item in od["items"] or []:
                        prod_id = str(item.get('product_id')) if item.get('product_id') is not None else None
                        if prod_id and prod_id in associated_products:
                            amount = float(item.get('amount', 0) or 0)
                            price = float(item.get('product_price', 0) or 0.0)
                            actual_income += amount * price

            g['actualIncome'] = round(actual_income, 2)

            # Persistimos el cálculo
            db.collection('goals').document(goal_doc.id).update({'actualIncome': g['actualIncome']})

            out.append(g)

        return out

    except HTTPException:
        raise
    except Exception as e:
        # Muy importante: levantamos HTTPException para que el front lo trate como error
        raise HTTPException(status_code=500, detail=str(e))
