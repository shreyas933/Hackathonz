from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.catalog import Product, ProductVariant, Plan, TaxRate, DiscountRule
from app.models.user import User
from app.schemas.catalog import (
    ProductCreate, ProductUpdate,
    ProductVariantCreate,
    PlanCreate, PlanUpdate,
    TaxRateCreate,
    DiscountRuleCreate
)
from app.services.audit_service import AuditService

class CatalogService:
    # --- Products ---
    @staticmethod
    def create_product(db: Session, actor: User, data: ProductCreate, ip_address: Optional[str] = None) -> Product:
        existing = db.query(Product).filter(Product.code == data.code.strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with code '{data.code}' already exists."
            )

        product = Product(
            name=data.name,
            code=data.code.strip(),
            product_type=data.product_type,
            sales_price=data.sales_price,
            cost_price=data.cost_price,
            description=data.description,
            notes=data.notes,
            is_active=data.is_active
        )
        db.add(product)
        db.flush()

        AuditService.log(
            db=db,
            action="create_product",
            entity_type="product",
            entity_id=str(product.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            after_state={"name": product.name, "code": product.code, "sales_price": str(product.sales_price)},
            ip_address=ip_address
        )
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def list_products(db: Session, active_only: bool = False) -> List[Product]:
        query = db.query(Product)
        if active_only:
            query = query.filter(Product.is_active == True)
        return query.order_by(Product.name.asc()).all()

    @staticmethod
    def get_product(db: Session, product_id: int) -> Product:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return product

    @staticmethod
    def update_product(db: Session, actor: User, product_id: int, data: ProductUpdate, ip_address: Optional[str] = None) -> Product:
        product = CatalogService.get_product(db, product_id)
        before_state = {"name": product.name, "sales_price": str(product.sales_price), "is_active": product.is_active}

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)

        after_state = {"name": product.name, "sales_price": str(product.sales_price), "is_active": product.is_active}
        AuditService.log(
            db=db,
            action="update_product",
            entity_type="product",
            entity_id=str(product.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address
        )
        db.commit()
        db.refresh(product)
        return product

    # --- Variants ---
    @staticmethod
    def create_variant(db: Session, actor: User, product_id: int, data: ProductVariantCreate, ip_address: Optional[str] = None) -> ProductVariant:
        # Check product exists
        product = CatalogService.get_product(db, product_id)
        existing = db.query(ProductVariant).filter(ProductVariant.sku == data.sku.strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Variant with SKU '{data.sku}' already exists."
            )

        variant = ProductVariant(
            product_id=product.id,
            variant_name=data.variant_name,
            sku=data.sku.strip(),
            price_adjustment=data.price_adjustment,
            attributes_json=data.attributes_json,
            is_active=data.is_active
        )
        db.add(variant)
        db.flush()

        AuditService.log(
            db=db,
            action="create_product_variant",
            entity_type="product_variant",
            entity_id=str(variant.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            after_state={"variant_name": variant.variant_name, "sku": variant.sku, "price_adjustment": str(variant.price_adjustment)},
            ip_address=ip_address
        )
        db.commit()
        db.refresh(variant)
        return variant

    # --- Plans ---
    @staticmethod
    def create_plan(db: Session, actor: User, data: PlanCreate, ip_address: Optional[str] = None) -> Plan:
        CatalogService.get_product(db, data.product_id)
        existing = db.query(Plan).filter(Plan.code == data.code.strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with code '{data.code}' already exists."
            )

        plan = Plan(
            product_id=data.product_id,
            name=data.name,
            code=data.code.strip(),
            billing_frequency=data.billing_frequency,
            base_price=data.base_price,
            min_quantity=data.min_quantity,
            availability_start=data.availability_start,
            availability_end=data.availability_end,
            can_pause=data.can_pause,
            can_early_close=data.can_early_close,
            auto_close_at_end=data.auto_close_at_end,
            auto_renew=data.auto_renew,
            trial_days=data.trial_days,
            is_active=data.is_active
        )
        db.add(plan)
        db.flush()

        AuditService.log(
            db=db,
            action="create_plan",
            entity_type="plan",
            entity_id=str(plan.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            after_state={"name": plan.name, "code": plan.code, "base_price": str(plan.base_price), "billing_frequency": plan.billing_frequency},
            ip_address=ip_address
        )
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def list_plans(db: Session, product_id: Optional[int] = None, active_only: bool = False) -> List[Plan]:
        query = db.query(Plan)
        if product_id:
            query = query.filter(Plan.product_id == product_id)
        if active_only:
            query = query.filter(Plan.is_active == True)
        return query.order_by(Plan.base_price.asc()).all()

    # --- Taxes ---
    @staticmethod
    def create_tax_rate(db: Session, actor: User, data: TaxRateCreate, ip_address: Optional[str] = None) -> TaxRate:
        tax = TaxRate(
            name=data.name,
            rate_percent=data.rate_percent,
            is_compound=data.is_compound,
            is_active=data.is_active
        )
        db.add(tax)
        db.flush()

        AuditService.log(
            db=db,
            action="create_tax_rate",
            entity_type="tax_rate",
            entity_id=str(tax.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            after_state={"name": tax.name, "rate_percent": str(tax.rate_percent)},
            ip_address=ip_address
        )
        db.commit()
        db.refresh(tax)
        return tax

    @staticmethod
    def list_tax_rates(db: Session, active_only: bool = False) -> List[TaxRate]:
        query = db.query(TaxRate)
        if active_only:
            query = query.filter(TaxRate.is_active == True)
        return query.order_by(TaxRate.rate_percent.asc()).all()

    # --- Discounts ---
    @staticmethod
    def create_discount_rule(db: Session, actor: User, data: DiscountRuleCreate, ip_address: Optional[str] = None) -> DiscountRule:
        rule = DiscountRule(
            name=data.name,
            discount_type=data.discount_type,
            value=data.value,
            min_seats=data.min_seats,
            min_amount=data.min_amount,
            max_allowed_sales_discount=data.max_allowed_sales_discount,
            requires_admin_approval=data.requires_admin_approval,
            is_active=data.is_active
        )
        db.add(rule)
        db.flush()

        AuditService.log(
            db=db,
            action="create_discount_rule",
            entity_type="discount_rule",
            entity_id=str(rule.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            after_state={"name": rule.name, "discount_type": rule.discount_type, "value": str(rule.value)},
            ip_address=ip_address
        )
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def list_discount_rules(db: Session, active_only: bool = False) -> List[DiscountRule]:
        query = db.query(DiscountRule)
        if active_only:
            query = query.filter(DiscountRule.is_active == True)
        return query.order_by(DiscountRule.created_at.desc()).all()
