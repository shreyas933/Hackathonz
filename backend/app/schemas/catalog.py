from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, List

# Product Variant schemas
class ProductVariantBase(BaseModel):
    variant_name: str
    sku: str
    price_adjustment: Decimal = Decimal("0.00")
    attributes_json: Optional[str] = None
    is_active: bool = True

class ProductVariantCreate(ProductVariantBase):
    product_id: Optional[int] = None

class ProductVariantOut(ProductVariantBase):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Plan schemas
class PlanBase(BaseModel):
    name: str
    code: str
    billing_frequency: str = Field(..., pattern="^(daily|weekly|monthly|yearly)$")
    base_price: Decimal
    min_quantity: int = 1
    availability_start: Optional[datetime] = None
    availability_end: Optional[datetime] = None
    can_pause: bool = False
    can_early_close: bool = True
    auto_close_at_end: bool = False
    auto_renew: bool = True
    trial_days: int = 0
    is_active: bool = True

class PlanCreate(PlanBase):
    product_id: int

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    base_price: Optional[Decimal] = None
    billing_frequency: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|yearly)$")
    min_quantity: Optional[int] = None
    can_pause: Optional[bool] = None
    can_early_close: Optional[bool] = None
    auto_close_at_end: Optional[bool] = None
    auto_renew: Optional[bool] = None
    trial_days: Optional[int] = None
    is_active: Optional[bool] = None

class PlanOut(PlanBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Product schemas
class ProductBase(BaseModel):
    name: str
    code: str
    product_type: str = Field("saas", pattern="^(saas|addon|service)$")
    sales_price: Decimal
    cost_price: Decimal = Decimal("0.00")
    description: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sales_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class ProductOut(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    variants: List[ProductVariantOut] = []
    plans: List[PlanOut] = []

    class Config:
        from_attributes = True

# Tax Rate schemas
class TaxRateBase(BaseModel):
    name: str
    rate_percent: Decimal
    is_compound: bool = False
    is_active: bool = True

class TaxRateCreate(TaxRateBase):
    pass

class TaxRateOut(TaxRateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Discount Rule schemas
class DiscountRuleBase(BaseModel):
    name: str
    discount_type: str = Field("percentage", pattern="^(percentage|fixed_amount)$")
    value: Decimal
    min_seats: int = 1
    min_amount: Decimal = Decimal("0.00")
    max_allowed_sales_discount: Decimal = Decimal("10.00")
    requires_admin_approval: bool = False
    is_active: bool = True

class DiscountRuleCreate(DiscountRuleBase):
    pass

class DiscountRuleOut(DiscountRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
