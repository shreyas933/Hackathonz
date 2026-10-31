from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class CustomerMemberOut(BaseModel):
    id: int
    user_id: int
    email: EmailStr
    full_name: str
    role: str  # owner, finance_contact, subscription_manager
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CustomerBusinessOut(BaseModel):
    id: int
    company_name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: str
    contact_email: str
    contact_phone: Optional[str] = None
    status: str
    created_at: datetime
    members: Optional[List[CustomerMemberOut]] = None

    class Config:
        from_attributes = True

class UpdateCustomerBusinessRequest(BaseModel):
    company_name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None

class AddCustomerMemberRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(owner|finance_contact|subscription_manager)$")

