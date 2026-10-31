from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.catalog import (
    ProductCreate, ProductUpdate, ProductOut,
    ProductVariantCreate, ProductVariantOut,
    PlanCreate, PlanUpdate, PlanOut,
    TaxRateCreate, TaxRateOut,
    DiscountRuleCreate, DiscountRuleOut
)
from app.services.catalog_service import CatalogService
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User

router = APIRouter(prefix="/catalog", tags=["Catalog"])

# --- Products ---
@router.get("/products", response_model=List[ProductOut])
def list_products(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CatalogService.list_products(db, active_only=active_only)

@router.post("/products", response_model=ProductOut)
def create_product(
    data: ProductCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    ip = request.client.host if request.client else None
    return CatalogService.create_product(db, admin_user, data, ip_address=ip)

@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    ip = request.client.host if request.client else None
    return CatalogService.update_product(db, admin_user, product_id, data, ip_address=ip)

# --- Variants ---
@router.post("/products/{product_id}/variants", response_model=ProductVariantOut)
def create_variant(
    product_id: int,
    data: ProductVariantCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    ip = request.client.host if request.client else None
    return CatalogService.create_variant(db, admin_user, product_id, data, ip_address=ip)

# --- Plans ---
@router.get("/plans", response_model=List[PlanOut])
def list_plans(
    product_id: Optional[int] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CatalogService.list_plans(db, product_id=product_id, active_only=active_only)

@router.post("/plans", response_model=PlanOut)
def create_plan(
    data: PlanCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    ip = request.client.host if request.client else None
    return CatalogService.create_plan(db, admin_user, data, ip_address=ip)

# --- Taxes ---
@router.get("/taxes", response_model=List[TaxRateOut])
def list_taxes(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CatalogService.list_tax_rates(db, active_only=active_only)

@router.post("/taxes", response_model=TaxRateOut)
def create_tax(
    data: TaxRateCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    ip = request.client.host if request.client else None
    return CatalogService.create_tax_rate(db, admin_user, data, ip_address=ip)

# --- Discounts ---
@router.get("/discounts", response_model=List[DiscountRuleOut])
def list_discounts(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CatalogService.list_discount_rules(db, active_only=active_only)

@router.post("/discounts", response_model=DiscountRuleOut)
def create_discount(
    data: DiscountRuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    ip = request.client.host if request.client else None
    return CatalogService.create_discount_rule(db, admin_user, data, ip_address=ip)
