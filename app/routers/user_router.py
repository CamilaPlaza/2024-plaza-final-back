from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from app.models.user import UserRegisterInput, UserRegister, UserForgotPassword
from app.controller.user_controller import (
    check_level_controller, employees_with_shift_controller, get_top_level_status_controller, level_controller,
    register, handle_forgot_password, ranking_controller,
    get_user_by_id, delete_user_by_id, reset_monthly_points_controller, rewards_controller
)
from app.dependencies import verify_token
from fastapi import HTTPException

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register/")
async def register_user(user_input: UserRegisterInput, user_data=Depends(verify_token)):
    user = UserRegister(**user_input.dict())
    return register(user, user_data)

@router.post("/forgot-password/")
async def forgot_password_user(user: UserForgotPassword):
    return handle_forgot_password(user)

@router.get("/ranking/")
async def ranking(user_data=Depends(verify_token)):
    return ranking_controller()


@router.get("/getByID/{uid}")
async def get_user(uid: str, user_data=Depends(verify_token)):
    token_uid = user_data.get("uid")
    if uid != token_uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    return get_user_by_id(uid)

@router.delete("/deleteByID/{uid}")
async def delete_user(uid: str, user_data=Depends(verify_token)):
    return delete_user_by_id(uid)

@router.get("/rewards/{level_id}")
async def rewards(level_id: str, user_data=Depends(verify_token)):
    return rewards_controller(level_id)

@router.get("/check-level/{uid}")
async def check_level(uid: str, user_data=Depends(verify_token)):
    return check_level_controller(uid)

@router.get("/top-level-status/{level_id}")
async def get_top_level_status(level_id: str, user_data=Depends(verify_token)):
    return get_top_level_status_controller(level_id)

@router.get("/reset-monthly-points")
async def reset_monthly_points(user_data=Depends(verify_token)):
    return reset_monthly_points_controller()

@router.get("/level/{level_id}")
async def level(level_id: str, user_data=Depends(verify_token)):
    return level_controller(level_id)

@router.get("/employees-with-shift")
def employees_with_shift(user_data=Depends(verify_token)) -> Dict[str, Any]:
    role = (user_data or {}).get("role")
    if role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin role required")

    employees = employees_with_shift_controller()
    return {"employees": employees}