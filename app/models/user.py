from enum import Enum
from pydantic import BaseModel, Field, EmailStr, constr
from typing import Optional

class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=6, max_length=50)

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"

class ShiftName(str, Enum):
    MANANA = "mañana"
    TARDE = "tarde"
    NOCHE = "noche"

class UserRegisterInput(BaseModel):
    uid: constr(min_length=5)
    name: constr(min_length=2, max_length=50)
    birthday: constr(pattern=r"^\d{2}/\d{2}/\d{4}$")
    imageUrl: Optional[str] = None
    shift_name: ShiftName      # <<— NUEVO

class UserRegister(UserRegisterInput):
    role: UserRole = Field(default=UserRole.EMPLOYEE)

class UserForgotPassword(BaseModel):
    email: EmailStr

class TokenData(BaseModel):
    id_token: str
