from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from ..auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

from ..config import settings

from ..database import get_db

from ..models import Admin, Company, User

from ..schemas import (
    RegisterRequest,
    TokenResponse,
    UserResponse,
)





router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


INVALID_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)




@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):

    existing_mobile = (
        db.query(User)
        .filter(User.mobile == data.mobile)
        .first()
    )

    if existing_mobile:
        raise HTTPException(
            status_code=409,
            detail="Mobile already registered",
        )

    existing_national_id = (
        db.query(User)
        .filter(User.national_id == data.national_id)
        .first()
    )

    if existing_national_id:
        raise HTTPException(
            status_code=409,
            detail="National ID already registered",
        )

    user = User(
        mobile=data.mobile,
        national_id=data.national_id,
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user





@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    admin = (
        db.query(Admin)
        .filter(Admin.username == form_data.username)
        .first()
    )

    if admin is not None and verify_password(
        form_data.password, admin.password_hash
    ):
        access_token = create_access_token(
            subject_id=admin.id,
            role="admin",
            username=admin.username,
            expire_minutes=settings.ADMIN_TOKEN_EXPIRE_MINUTES,
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ADMIN_TOKEN_EXPIRE_MINUTES * 60,
            "role": "admin",
        }

    company = (
        db.query(Company)
        .filter(Company.username == form_data.username)
        .first()
    )

    if company is not None and verify_password(
        form_data.password, company.password_hash
    ):
        access_token = create_access_token(
            subject_id=company.id,
            role="company",
            username=company.username,
            expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "role": "company",
        }

    user = (
        db.query(User)
        .filter(User.mobile == form_data.username)
        .first()
    )

    if user is not None and verify_password(
        form_data.password, user.password_hash
    ):
        access_token = create_access_token(
            subject_id=user.id,
            role="user",
            username=user.mobile,
            expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "role": "user",
        }

    raise INVALID_CREDENTIALS_EXCEPTION





@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
