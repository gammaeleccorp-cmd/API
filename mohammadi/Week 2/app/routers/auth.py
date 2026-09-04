from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from ..auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

from ..database import get_db

from ..models import User

from ..schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
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
        .filter(
            User.mobile == data.mobile
        )
        .first()
    )

    if existing_mobile:

        raise HTTPException(
            status_code=409,
            detail="Mobile already registered",
        )

    existing_national_id = (
        db.query(User)
        .filter(
            User.national_id
            == data.national_id
        )
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
        password_hash=hash_password(
            data.password
        ),
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
    data: LoginRequest,
    db: Session = Depends(get_db),
):

    user = (
        db.query(User)
        .filter(
            User.mobile == data.username
        )
        .first()
    )

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        user_id=user.id,
        username=user.mobile,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": (
            ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ),
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):

    return current_user