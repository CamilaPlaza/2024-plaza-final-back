from app.service.user_service import check_level, create_user, get_top_level_status, get_user_by_email, forgot_password, level, ranking, reset_monthly_points, rewards, user_by_id, delete_user
from app.models.user import TokenData, UserLogin, UserRegister, UserForgotPassword
from firebase_admin import auth
from fastapi import HTTPException

def login(user: UserLogin):
    try:
        user = auth.get_user_by_email(user.email)
        return {"message": "Usuario autenticado exitosamente", "user_id": user.uid}
    except firebase_admin.auth.AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def token(token_data: TokenData):
    try:
        decoded_token = auth.verify_id_token(token_data.id_token)
        uid = decoded_token['uid']
        return {"message": "Token verificado", "user_id": uid}
    except firebase_admin.auth.AuthError as e:
        raise HTTPException(status_code=400, detail="Token no válido o expirado")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def register(user: UserRegister, token_claims: dict):
    token_uid = token_claims.get("uid")
    if not token_uid:
        raise HTTPException(status_code=401, detail="Invalid token")

    if user.uid != token_uid:
        raise HTTPException(status_code=403, detail="Forbidden")

    resp = create_user(user)
    if "error" in resp:
        raise HTTPException(status_code=400, detail=resp["error"])
    return {"message": "User registered successfully"}


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
