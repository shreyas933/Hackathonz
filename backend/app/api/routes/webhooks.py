from typing import Optional
from fastapi import APIRouter, Request, Header, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.automation import WebhookResponse
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/payments", response_model=WebhookResponse)
async def handle_payment_gateway_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    db: Session = Depends(get_db)
):
    raw_body = await request.body()
    ip = request.client.host if request.client else None
    return WebhookService.handle_payment_webhook(
        db=db,
        raw_body=raw_body,
        signature_header=x_webhook_signature,
        ip_address=ip
    )

