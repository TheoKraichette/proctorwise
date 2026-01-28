from fastapi import APIRouter, HTTPException
from application.use_cases.register_user import RegisterUser
from application.use_cases.login_user import LoginUser
from application.use_cases.get_user import GetUser
from infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from interface.api.schemas.user_request import UserCreateRequest, UserLoginRequest
from interface.api.schemas.user_response import UserResponse, TokenResponse

router = APIRouter(prefix="/users", tags=["Users"])
repo = SQLAlchemyUserRepository()

@router.post("/register", response_model=UserResponse)
def register_user(request: UserCreateRequest):
    use_case = RegisterUser(repo)
    try:
        user = use_case.execute(
            name=request.name,
            email=request.email,
            password=request.password,
            role=request.role
        )
        return UserResponse(
            user_id=user.user_id,
            name=user.name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
def login_user(request: UserLoginRequest):
    use_case = LoginUser(repo)
    try:
        token, user = use_case.execute(
            email=request.email,
            password=request.password
        )
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    use_case = GetUser(repo)
    user = use_case.execute(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at
    )
