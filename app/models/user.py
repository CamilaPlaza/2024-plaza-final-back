from datetime import date
from enum import Enum
from pydantic import BaseModel, Field

# Modelo para iniciar sesión
class UserLogin(BaseModel):
    email: str
    password: str

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"

class UserRegisterInput(BaseModel):
    uid: str
    name: str
    birthday: str
    imageUrl: str

class UserRegister(UserRegisterInput):
    role: UserRole = Field(default=UserRole.EMPLOYEE)


class UserForgotPassword(BaseModel):
    email: str

class TokenData(BaseModel):
    id_token: str

