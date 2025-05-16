from fastapi import APIRouter
from application.use_cases.register_user import RegisterUser
from application.use_cases.get_user import GetUser
from infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from interface.api.schemas.user_request import UserCreateRequest
from interface.api.schemas.user_response import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])
repo = SQLAlchemyUserRepository()

@router.post("/", response_model=UserResponse)
def create_user(request: UserCreateRequest):
    use_case = RegisterUser(repo)
    user = use_case.execute(request.dict())
    return UserResponse(**user.__dict__)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    use_case = GetUser(repo)
    user = use_case.execute(user_id)
    return UserResponse(**user.__dict__)
