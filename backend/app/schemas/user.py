from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any

class StaffProfileOut(BaseModel):
    id: int
    staff_role: str
    department: Optional[str] = None
    permissions_override: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    user_type: str
    is_active: bool
    created_at: datetime
    staff_profile: Optional[StaffProfileOut] = None

    class Config:
        from_attributes = True

class CreateStaffRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)
    staff_role: str = Field(..., pattern="^(sales|finance)$")
    department: Optional[str] = None
    permissions_override: Optional[str] = None

class UpdateStaffPermissionsRequest(BaseModel):
    staff_role: Optional[str] = Field(None, pattern="^(sales|finance)$")
    department: Optional[str] = None
    permissions_override: Optional[str] = None
    is_active: Optional[bool] = None

