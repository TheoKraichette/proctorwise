from pydantic import BaseModel

class UserCreateRequest(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
