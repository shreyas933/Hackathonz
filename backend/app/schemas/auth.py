from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    role: str
    business_id: Optional[int] = None
    email: str
    full_name: str

class RegisterCustomerRequest(BaseModel):
    # User info
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    # Business info
    company_name: str = Field(..., min_length=2, max_length=255)
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None  # e.g. GSTIN
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: str = "India"
    contact_phone: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

