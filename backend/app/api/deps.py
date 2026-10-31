from typing import Optional, Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User, StaffProfile
from app.models.customer import CustomerMembership

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive."
        )

    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privilege required."
        )
    return current_user

def get_current_staff(current_user: User = Depends(get_current_user)) -> User:
    if current_user.user_type not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff privilege required."
        )
    return current_user

def get_current_customer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> tuple[User, int, str]:
    """
    Returns (user, business_id, customer_role).
    Guarantees server-side tenant isolation.
    """
    if current_user.user_type != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account required."
        )

    membership = db.query(CustomerMembership).filter(
        CustomerMembership.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No customer business associated with this account."
        )

    return current_user, membership.business_id, membership.role

