from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreateRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "student"

class UserLoginRequest(BaseModel):
    email: str
    password: str
