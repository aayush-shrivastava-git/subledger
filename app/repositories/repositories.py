from sqlalchemy.orm import Session
from app.models.entities import (
    Plan, Customer, Subscription, Invoice,
    PaymentAttempt, LedgerEntry
)


class BaseRepository:
    def __init__(self, db: Session, model):
        self.db = db
        self.model = model

    def get(self, entity_id: int):
        return self.db.get(self.model, entity_id)

    def list(self):
        return self.db.query(self.model).all()

    def create(self, data: dict):
        obj = self.model(**data)
        self.db.add(obj)
        self.db.flush()
        return obj


class PlanRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Plan)


class CustomerRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Customer)

    def get_by_email(self, email):
        return self.db.query(Customer).filter(
            Customer.email == email
        ).first()


class SubscriptionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Subscription)

    def get_active(self, customer_id, plan_id):
        return self.db.query(Subscription).filter(
            Subscription.customer_id == customer_id,
            Subscription.plan_id == plan_id,
            Subscription.status == "active"
        ).first()


class InvoiceRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Invoice)


class PaymentAttemptRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, PaymentAttempt)


class LedgerRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, LedgerEntry)

    def get_customer_entries(self, customer_id):
        return self.db.query(LedgerEntry).filter(
            LedgerEntry.customer_id == customer_id
        ).order_by(LedgerEntry.created_at.desc()).all()