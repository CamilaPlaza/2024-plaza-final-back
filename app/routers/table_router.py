from fastapi import APIRouter, Depends
from typing import Dict, Union
from app.dependencies import verify_token
from app.controller.table_controller import (
    associate_order_with_table_controller, clean_table_controller,
    close_table_controller, get_table_by_id_controller,
    get_tables_controller, create_table_controller
)

router = APIRouter(prefix="/tables", tags=["Tables"])

@router.get("/")
async def tables(user_data=Depends(verify_token)):
    return get_tables_controller()

@router.get("/{table_id}")
async def get_table(table_id: str, user_data=Depends(verify_token)):
    return get_table_by_id_controller(table_id)

@router.put("/order/{table_id}")
async def associate_order_with_table(table_id: str, order_id: int, user_data=Depends(verify_token)):
    return associate_order_with_table_controller(table_id, order_id)

@router.put("/close/{table_id}")
async def close_table(table_id: str, body: Dict[str, Union[str, int]], user_data=Depends(verify_token)):
    return close_table_controller(table_id, body)

@router.put("/clean/{table_id}")
async def clean_table(table_id: str, body: Dict[str, Union[str, int]], user_data=Depends(verify_token)):
    return clean_table_controller(table_id, body)

@router.post("/create")
async def create_table(body: Dict[str, Union[str, int]], user_data=Depends(verify_token)):
    return create_table_controller(body)
