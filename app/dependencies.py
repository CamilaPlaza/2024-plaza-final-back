# app/dependencies.py
from fastapi import Header, HTTPException, Depends
from firebase_admin import auth

def verify_token(authorization: str = Header(...)):
    
    try:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Esquema de autenticación inválido.")
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token no válido o expirado: {str(e)}")
