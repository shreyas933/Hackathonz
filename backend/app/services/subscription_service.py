from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.commercial import Subscription
from app.models.user import User
from app.services.audit_service import AuditService

class SubscriptionService:
    @staticmethod
    def list_for_customer(db: Session, business_id: int) -> List[Subscription]:
        return db.query(Subscription).filter(
            Subscription.business_id == business_id
        ).order_by(Subscription.created_at.desc()).all()

    @staticmethod
    def list_for_staff(db: Session, status_filter: Optional[str] = None) -> List[Subscription]:
        query = db.query(Subscription)
        if status_filter:
            query = query.filter(Subscription.status == status_filter)
        return query.order_by(Subscription.created_at.desc()).all()

    @staticmethod
    def get_subscription(db: Session, subscription_id: int, business_id: Optional[int] = None) -> Subscription:
        query = db.query(Subscription).filter(Subscription.id == subscription_id)
        if business_id is not None:
            query = query.filter(Subscription.business_id == business_id)
        sub = query.first()
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found or access denied.")
        return sub

    @classmethod
    def pause_subscription(
        cls,
        db: Session,
        subscription_id: int,
        actor: User,
        business_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Subscription:
        sub = cls.get_subscription(db, subscription_id, business_id)
        if sub.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only active subscriptions can be paused. Current status is {sub.status}."
            )

        # Validate plan capability
        for line in sub.lines:
            if line.plan and not line.plan.can_pause:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Subscription plan '{line.plan.name}' does not allow pausing."
                )

        before = {"status": sub.status}
        sub.status = "paused"
        
        AuditService.log(
            db=db,
            action="subscription_paused",
            entity_type="subscription",
            entity_id=str(sub.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            before_state=before,
            after_state={"status": "paused"},
            ip_address=ip_address
        )
        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def resume_subscription(
        cls,
        db: Session,
        subscription_id: int,
        actor: User,
        business_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Subscription:
        sub = cls.get_subscription(db, subscription_id, business_id)
        if sub.status != "paused":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only paused subscriptions can be resumed. Current status is {sub.status}."
            )

        before = {"status": sub.status}
        sub.status = "active"

        AuditService.log(
            db=db,
            action="subscription_resumed",
            entity_type="subscription",
            entity_id=str(sub.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            before_state=before,
            after_state={"status": "active"},
            ip_address=ip_address
        )
        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def cancel_subscription(
        cls,
        db: Session,
        subscription_id: int,
        actor: User,
        reason: Optional[str] = None,
        business_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Subscription:
        sub = cls.get_subscription(db, subscription_id, business_id)
        if sub.status in ["cancelled", "expired"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subscription is already {sub.status}."
            )

        # Check early close permission if initiated by customer
        if actor.user_type == "customer":
            for line in sub.lines:
                if line.plan and not line.plan.can_early_close:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Subscription plan '{line.plan.name}' does not allow customer early termination."
                    )

        before = {"status": sub.status}
        sub.status = "cancelled"

        AuditService.log(
            db=db,
            action="subscription_cancelled",
            entity_type="subscription",
            entity_id=str(sub.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            before_state=before,
            after_state={"status": "cancelled", "reason": reason},
            ip_address=ip_address
        )
        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def update_status(
        cls,
        db: Session,
        subscription_id: int,
        actor: User,
        new_status: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Subscription:
        sub = cls.get_subscription(db, subscription_id)
        before_state = {"status": sub.status}
        sub.status = new_status

        AuditService.log(
            db=db,
            action="update_subscription_status",
            entity_type="subscription",
            entity_id=str(sub.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            before_state=before_state,
            after_state={"status": sub.status, "reason": reason},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(sub)
        return sub
