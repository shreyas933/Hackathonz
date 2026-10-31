from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.commercial import SubscriptionRequest, RequestActivity
from app.models.user import User
from app.schemas.commercial import SubscriptionRequestCreate, SubscriptionRequestUpdate, RequestActivityCreate
from app.services.audit_service import AuditService

class RequestService:
    @staticmethod
    def _generate_reference(db: Session) -> str:
        count = db.query(SubscriptionRequest).count() + 1
        year = datetime.now(timezone.utc).year
        return f"REQ-{year}-{count:04d}"

    @staticmethod
    def create_request(
        db: Session,
        business_id: int,
        creator: User,
        data: SubscriptionRequestCreate,
        ip_address: Optional[str] = None
    ) -> SubscriptionRequest:
        reference = RequestService._generate_reference(db)

        req = SubscriptionRequest(
            reference=reference,
            business_id=business_id,
            request_type=data.request_type,
            related_subscription_id=data.related_subscription_id,
            product_id=data.product_id,
            plan_id=data.plan_id,
            variant_id=data.variant_id,
            requested_quantity=data.requested_quantity,
            notes=data.notes,
            status="new",
            created_by_user_id=creator.id
        )
        db.add(req)
        db.flush()

        # Add initial activity
        activity = RequestActivity(
            request_id=req.id,
            actor_user_id=creator.id,
            activity_type="status_change",
            message=f"Request submitted for {data.request_type.replace('_', ' ')} with {data.requested_quantity} seat(s)."
        )
        db.add(activity)

        AuditService.log(
            db=db,
            action="create_subscription_request",
            entity_type="subscription_request",
            entity_id=str(req.id),
            actor_user_id=creator.id,
            actor_email=creator.email,
            actor_role=creator.user_type,
            after_state={"reference": req.reference, "type": req.request_type, "seats": req.requested_quantity},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def list_requests_for_customer(db: Session, business_id: int) -> List[SubscriptionRequest]:
        return db.query(SubscriptionRequest).filter(
            SubscriptionRequest.business_id == business_id
        ).order_by(SubscriptionRequest.created_at.desc()).all()

    @staticmethod
    def list_requests_for_staff(
        db: Session,
        request_type: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[SubscriptionRequest]:
        query = db.query(SubscriptionRequest)
        if request_type:
            query = query.filter(SubscriptionRequest.request_type == request_type)
        if status_filter:
            query = query.filter(SubscriptionRequest.status == status_filter)
        return query.order_by(SubscriptionRequest.created_at.desc()).all()

    @staticmethod
    def get_request(db: Session, request_id: int, business_id: Optional[int] = None) -> SubscriptionRequest:
        query = db.query(SubscriptionRequest).filter(SubscriptionRequest.id == request_id)
        if business_id is not None:
            # Enforce tenant isolation
            query = query.filter(SubscriptionRequest.business_id == business_id)
        req = query.first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription request not found or access denied."
            )
        return req

    @staticmethod
    def update_request_by_staff(
        db: Session,
        request_id: int,
        actor: User,
        data: SubscriptionRequestUpdate,
        ip_address: Optional[str] = None
    ) -> SubscriptionRequest:
        req = RequestService.get_request(db, request_id)
        before_state = {"status": req.status, "assigned_sales": req.assigned_sales_user_id}

        if data.status and data.status != req.status:
            req.status = data.status
            activity = RequestActivity(
                request_id=req.id,
                actor_user_id=actor.id,
                activity_type="status_change",
                message=f"Status changed to {data.status.replace('_', ' ')} by {actor.full_name}."
            )
            db.add(activity)

        if data.assigned_sales_user_id is not None:
            req.assigned_sales_user_id = data.assigned_sales_user_id

        if data.notes:
            req.notes = data.notes

        AuditService.log(
            db=db,
            action="update_subscription_request",
            entity_type="subscription_request",
            entity_id=str(req.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            before_state=before_state,
            after_state={"status": req.status, "assigned_sales": req.assigned_sales_user_id},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def add_activity(
        db: Session,
        request_id: int,
        actor: User,
        data: RequestActivityCreate,
        business_id: Optional[int] = None
    ) -> RequestActivity:
        req = RequestService.get_request(db, request_id, business_id=business_id)
        activity = RequestActivity(
            request_id=req.id,
            actor_user_id=actor.id,
            activity_type=data.activity_type,
            message=data.message
        )
        db.add(activity)

        # If sales requested clarification, update status
        if data.activity_type == "clarification_request" and actor.user_type in ["admin", "staff"]:
            req.status = "clarification_required"
        elif data.activity_type == "customer_response" and actor.user_type == "customer":
            req.status = "under_review"

        db.commit()
        db.refresh(activity)
        return activity

