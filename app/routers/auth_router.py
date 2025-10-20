from fastapi import APIRouter
from app.models.user import UserLogin, TokenData
from app.controller.user_controller import login, token

router = APIRouter()

@router.post("/verify-token/")
async def verify_token_route(token_data: TokenData):
    return token(token_data)
