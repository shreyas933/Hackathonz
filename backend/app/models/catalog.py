from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), unique=True, index=True, nullable=False)
    product_type = Column(String(50), default="saas", nullable=False)  # saas, addon, service
    sales_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_name = Column(String(255), nullable=False)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    price_adjustment = Column(Numeric(12, 2), default=0.00, nullable=False)
    attributes_json = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product", back_populates="variants")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(100), unique=True, index=True, nullable=False)
    billing_frequency = Column(String(50), default="monthly", nullable=False)  # daily, weekly, monthly, yearly
    base_price = Column(Numeric(12, 2), nullable=False)
    min_quantity = Column(Integer, default=1, nullable=False)
    availability_start = Column(DateTime(timezone=True), nullable=True)
    availability_end = Column(DateTime(timezone=True), nullable=True)
    
    # Lifecycle options per PRD FR-CAT-3 & FR-SUB-5
    can_pause = Column(Boolean, default=False, nullable=False)
    can_early_close = Column(Boolean, default=True, nullable=False)
    auto_close_at_end = Column(Boolean, default=False, nullable=False)
    auto_renew = Column(Boolean, default=True, nullable=False)
    trial_days = Column(Integer, default=0, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="plans")


class TaxRate(Base):
    __tablename__ = "tax_rates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    rate_percent = Column(Numeric(5, 2), nullable=False)
    is_compound = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DiscountRule(Base):
    __tablename__ = "discount_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    discount_type = Column(String(50), default="percentage", nullable=False)  # percentage, fixed_amount
    value = Column(Numeric(10, 2), nullable=False)
    min_seats = Column(Integer, default=1, nullable=False)
    min_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    max_allowed_sales_discount = Column(Numeric(10, 2), default=10.00, nullable=False)
    requires_admin_approval = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

