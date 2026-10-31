from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.commercial import Quotation, QuotationVersion
from app.schemas.billing import (
    InvoiceOut,
    GenerateInvoiceFromQuotationRequest,
    InvoiceStatusUpdate,
    RecordPaymentRequest,
    PaymentOut,
    RecurringBillingRunRequest,
    RecurringBillingRunResult
)
from app.services.billing_service import BillingService
from app.services.payment_service import PaymentService
from app.services.pdf_service import PDFService
from app.api.deps import get_current_staff, get_current_customer, get_current_admin

router = APIRouter(tags=["Billing & Invoicing"])

# ==========================================
# Finance & Staff Invoicing Endpoints
# ==========================================

@router.post("/finance/invoices/generate-from-quotation", response_model=InvoiceOut)
def generate_invoice_from_quotation(
    data: GenerateInvoiceFromQuotationRequest,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return BillingService.generate_from_quotation(db, staff_user, data, ip_address=ip)

@router.post("/finance/invoices/run-recurring", response_model=RecurringBillingRunResult)
def trigger_recurring_billing_run(
    data: Optional[RecurringBillingRunRequest] = None,
    request: Request = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request and request.client else None
    target_dt = data.target_date if data else None
    return BillingService.run_recurring_billing(db, staff_user, target_date=target_dt, ip_address=ip)

@router.get("/finance/invoices", response_model=List[InvoiceOut])
def list_finance_invoices(
    business_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    subscription_id: Optional[int] = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return BillingService.list_invoices(
        db,
        business_id=business_id,
        status=status_filter,
        subscription_id=subscription_id
    )

@router.get("/finance/invoices/{invoice_id}", response_model=InvoiceOut)
def get_finance_invoice(
    invoice_id: int,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return BillingService.get_invoice(db, invoice_id)

@router.patch("/finance/invoices/{invoice_id}/status", response_model=InvoiceOut)
def update_invoice_status(
    invoice_id: int,
    data: InvoiceStatusUpdate,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return BillingService.update_invoice_status(
        db=db,
        invoice_id=invoice_id,
        new_status=data.status,
        notes=data.notes,
        user=staff_user,
        ip_address=ip
    )

@router.get("/finance/invoices/{invoice_id}/pdf")
def download_finance_invoice_pdf(
    invoice_id: int,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    invoice = BillingService.get_invoice(db, invoice_id)
    pdf_bytes = PDFService.generate_invoice_pdf(invoice)
    filename = f"Invoice-{invoice.invoice_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# ==========================================
# Finance & Staff Payments Endpoints
# ==========================================

@router.post("/finance/payments", response_model=PaymentOut)
def record_payment(
    data: RecordPaymentRequest,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return PaymentService.record_manual_payment(db, staff_user, data, ip_address=ip)

@router.get("/finance/payments", response_model=List[PaymentOut])
def list_finance_payments(
    business_id: Optional[int] = None,
    reconciliation_status: Optional[str] = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return PaymentService.list_payments(
        db,
        business_id=business_id,
        reconciliation_status=reconciliation_status
    )

@router.get("/finance/payments/{payment_id}", response_model=PaymentOut)
def get_finance_payment(
    payment_id: int,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return PaymentService.get_payment(db, payment_id)

# ==========================================
# Customer Invoicing & Payment Endpoints
# ==========================================

@router.get("/customer/invoices", response_model=List[InvoiceOut])
def list_customer_invoices(
    status_filter: Optional[str] = None,
    customer_info: tuple[User, int, str] = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    _, business_id, _ = customer_info
    return BillingService.list_invoices(db, business_id=business_id, status=status_filter)

@router.get("/customer/invoices/{invoice_id}", response_model=InvoiceOut)
def get_customer_invoice(
    invoice_id: int,
    customer_info: tuple[User, int, str] = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    _, business_id, _ = customer_info
    return BillingService.get_invoice(db, invoice_id, business_id=business_id)

@router.get("/customer/invoices/{invoice_id}/pdf")
def download_customer_invoice_pdf(
    invoice_id: int,
    customer_info: tuple[User, int, str] = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    _, business_id, _ = customer_info
    invoice = BillingService.get_invoice(db, invoice_id, business_id=business_id)
    pdf_bytes = PDFService.generate_invoice_pdf(invoice)
    filename = f"Invoice-{invoice.invoice_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/customer/payments", response_model=List[PaymentOut])
def list_customer_payments(
    customer_info: tuple[User, int, str] = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    _, business_id, _ = customer_info
    return PaymentService.list_payments(db, business_id=business_id)

@router.get("/customer/payments/{payment_id}", response_model=PaymentOut)
def get_customer_payment(
    payment_id: int,
    customer_info: tuple[User, int, str] = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    _, business_id, _ = customer_info
    return PaymentService.get_payment(db, payment_id, business_id=business_id)

# ==========================================
# Quotation PDF Endpoints
# ==========================================

@router.get("/staff/quotations/{quotation_id}/pdf")
def download_staff_quotation_pdf(
    quotation_id: int,
    version_number: Optional[int] = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found.")

    if version_number:
        version = db.query(QuotationVersion).filter(
            QuotationVersion.quotation_id == quotation_id,
            QuotationVersion.version_number == version_number
        ).first()
    else:
        version = db.query(QuotationVersion).filter(
            QuotationVersion.quotation_id == quotation_id,
            QuotationVersion.is_latest == True
        ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Quotation version not found.")

    pdf_bytes = PDFService.generate_quotation_pdf(quotation, version)
    filename = f"Quotation-{quotation.quotation_number}-v{version.version_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/customer/quotations/{quotation_id}/pdf")
def download_customer_quotation_pdf(
    quotation_id: int,
    version_number: Optional[int] = None,
    customer_info: tuple[User, int, str] = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    _, business_id, _ = customer_info
    quotation = db.query(Quotation).filter(
        Quotation.id == quotation_id,
        Quotation.business_id == business_id
    ).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found.")

    if version_number:
        version = db.query(QuotationVersion).filter(
            QuotationVersion.quotation_id == quotation_id,
            QuotationVersion.version_number == version_number
        ).first()
    else:
        version = db.query(QuotationVersion).filter(
            QuotationVersion.quotation_id == quotation_id,
            QuotationVersion.is_latest == True
        ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Quotation version not found.")

    pdf_bytes = PDFService.generate_quotation_pdf(quotation, version)
    filename = f"Quotation-{quotation.quotation_number}-v{version.version_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

