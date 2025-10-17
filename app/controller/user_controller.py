from typing import Any, Dict, List
from app.service.user_service import check_level, create_user, get_top_level_status, get_user_by_email, forgot_password, level, list_employees_with_shift_service, ranking, reset_monthly_points, rewards, user_by_id, delete_user
from app.models.user import TokenData, UserLogin, UserRegister, UserForgotPassword
from firebase_admin import auth
from fastapi import HTTPException
from app.service.shift_service import assign_employee_to_shift, find_shift_id_by_name

def login(user: UserLogin):
    try:
        u = auth.get_user_by_email(user.email)
        return {"message": "Usuario autenticado exitosamente", "user_id": u.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def token(token_data: TokenData):
    try:
        decoded_token = auth.verify_id_token(token_data.id_token)
        uid = decoded_token.get("uid") or decoded_token.get("sub")
        if not uid:
            raise HTTPException(status_code=400, detail="Token inválido: uid ausente")
        return {"message": "Token verificado", "user_id": uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Token no válido o expirado")

def register(user: UserRegister, token_claims: dict):
    token_uid = token_claims.get("uid") or token_claims.get("user_id") or token_claims.get("sub")
    if not token_uid:
        raise HTTPException(status_code=401, detail="Invalid token")
    if user.uid != token_uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    resp = create_user(user)
    if "error" in resp:
        raise HTTPException(status_code=400, detail=resp["error"])
    id_shift = find_shift_id_by_name(user.shift_name.value)
    assign_payload = {"id_employee": user.uid, "id_shift": id_shift, "tasks": []}
    assign_result = assign_employee_to_shift(assign_payload)
    return {
        "message": "User registered successfully and shift assigned",
        "uid": user.uid,
        "role": resp.get("role"),
        "shift_assignment": assign_result
    }

def handle_forgot_password(user: UserForgotPassword):
    db_user = get_user_by_email(user.email)
    if db_user:
        return forgot_password(user.email)
    else:
        raise HTTPException(status_code=404, detail="Email not found")

def get_user_by_id(uid: str):
    response = user_by_id(uid)
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    return response

def delete_user_by_id(uid: str):
    response = delete_user(uid)
    if "error" in response:
        raise HTTPException(status_code=404, detail=response["error"])
    return {"message": "User deleted successfully"}

def ranking_controller():
    try:
        response = ranking()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def rewards_controller(level_id: str):
    try:
        response = rewards(level_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def level_controller(level_id: str):
    try:
        response = level(level_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def check_level_controller(uid: str):
    try:
        response = check_level(uid)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_top_level_status_controller(level_id: str):
    try:
        response = get_top_level_status(level_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def reset_monthly_points_controller():
    try:
        response = reset_monthly_points()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def employees_with_shift_controller() -> List[Dict[str, Any]]:
    return list_employees_with_shift_service()
