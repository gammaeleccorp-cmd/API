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
    issue_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
    verify_password,
)
from ..config import settings
from ..database import get_db
from ..models import Admin, Company, User
from ..schemas import (
    LogoutRequest,
    RefreshRequest,
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





@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if admin is not None and verify_password(form_data.password, admin.password_hash):
        access_token = create_access_token(
            subject_id=admin.id, role="admin", username=admin.username, no_expiry=True,
        )
        return {
            "access_token": access_token,
            "refresh_token": None,
            "token_type": "bearer",
            "expires_in": None,
            "role": "admin",
        }

    company = db.query(Company).filter(Company.username == form_data.username).first()
    if company is not None and verify_password(form_data.password, company.password_hash):
        access_token = create_access_token(
            subject_id=company.id, role="company", username=company.username,
        )
        refresh_token = issue_refresh_token(db, "company", company.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "role": "company",
        }

    user = db.query(User).filter(User.mobile == form_data.username).first()
    if user is not None and verify_password(form_data.password, user.password_hash):
        access_token = create_access_token(
            subject_id=user.id, role="user", username=user.mobile,
        )
        refresh_token = issue_refresh_token(db, "user", user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "role": "user",
        }

    raise INVALID_CREDENTIALS_EXCEPTION




@router.post("/refresh", response_model=TokenResponse)
def refresh(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):

    new_access_token, new_refresh_token, role = rotate_refresh_token(
        db, data.refresh_token
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "role": role,
    }





@router.post("/logout", status_code=204)
def logout(
    data: LogoutRequest,
    db: Session = Depends(get_db),
):
    revoke_refresh_token(db, data.refresh_token)
    return None





@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user