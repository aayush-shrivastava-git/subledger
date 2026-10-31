
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.repositories import (
    PlanRepository,
    CustomerRepository,
    SubscriptionRepository,
    InvoiceRepository,
    PaymentAttemptRepository,
    LedgerRepository,
)

from app.models.entities import Plan, Customer, Subscription, Invoice


def now():
    return datetime.now(timezone.utc)


class PlanService:
    def __init__(self, db):
        self.db = db
        self.repo = PlanRepository(db)

    def create(self, data):
        try:
            obj = self.repo.create(data.model_dump())
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except Exception:
            self.db.rollback()
            raise

    def list(self):
        return self.repo.list()

    def update(self, plan_id, data):
        obj = self.repo.get(plan_id)
        if not obj:
            raise HTTPException(404, "Plan not found")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)

        self.db.commit()
        self.db.refresh(obj)
        return obj


class CustomerService:
    def __init__(self, db):
        self.db = db
        self.repo = CustomerRepository(db)

    def create(self, data):
        if self.repo.get_by_email(str(data.email)):
            raise HTTPException(409, "Customer email already exists")

        try:
            obj = self.repo.create(data.model_dump())
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except Exception:
            self.db.rollback()
            raise

    def list(self):
        return self.repo.list()

    def get(self, customer_id):
        obj = self.repo.get(customer_id)
        if not obj:
            raise HTTPException(404, "Customer not found")
        return obj


class SubscriptionService:
    def __init__(self, db):
        self.db = db
        self.repo = SubscriptionRepository(db)
        self.plans = PlanRepository(db)
        self.customers = CustomerRepository(db)

    def create(self, data):
        customer = self.customers.get(data.customer_id)
        plan = self.plans.get(data.plan_id)

        if not customer:
            raise HTTPException(404, "Customer not found")
        if customer.status != "active":
            raise HTTPException(400, "Customer is inactive")
        if not plan or plan.status != "active":
            raise HTTPException(400, "Plan is missing or inactive")

        if self.repo.get_active(data.customer_id, data.plan_id):
            raise HTTPException(409, "Active subscription already exists")

        start = now()
        days = {"monthly": 30, "quarterly": 90, "yearly": 365}.get(
            plan.billing_cycle
        )
        if not days:
            raise HTTPException(400, "Invalid billing cycle")

        try:
            obj = self.repo.create({
                "customer_id": data.customer_id,
                "plan_id": data.plan_id,
                "status": "active",
                "start_date": start,
                "current_period_start": start,
                "current_period_end": start + timedelta(days=days),
            })
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except Exception:
            self.db.rollback()
            raise

    def list(self):
        return self.repo.list()

    def cancel(self, subscription_id):
        obj = self.repo.get(subscription_id)
        if not obj:
            raise HTTPException(404, "Subscription not found")
        if obj.status != "active":
            raise HTTPException(400, "Subscription is not active")

        obj.status = "cancelled"
        obj.cancelled_at = now()
        self.db.commit()
        self.db.refresh(obj)
        return obj


class LedgerService:
    def __init__(self, db):
        self.db = db
        self.repo = LedgerRepository(db)

    def create(self, customer_id, invoice_id, entry_type,
               amount, currency, reference_id, description=None):
        return self.repo.create({
            "customer_id": customer_id,
            "invoice_id": invoice_id,
            "entry_type": entry_type,
            "amount": amount,
            "currency": currency,
            "reference_id": reference_id,
            "description": description,
        })

    def get_customer_ledger(self, customer_id):
        return self.repo.get_customer_entries(customer_id)


class InvoiceService:
    def __init__(self, db):
        self.db = db
        self.invoices = InvoiceRepository(db)
        self.subscriptions = SubscriptionRepository(db)
        self.plans = PlanRepository(db)
        self.ledger = LedgerService(db)

    def generate(self, subscription_id):
        subscription = self.subscriptions.get(subscription_id)

        if not subscription:
            raise HTTPException(404, "Subscription not found")
        if subscription.status != "active":
            raise HTTPException(400, "Subscription is not active")

        plan = self.plans.get(subscription.plan_id)
        if not plan:
            raise HTTPException(404, "Plan not found")

        start = subscription.current_period_start
        end = subscription.current_period_end

        existing = self.db.query(Invoice).filter(
            Invoice.subscription_id == subscription_id,
            Invoice.period_start == start,
            Invoice.period_end == end,
        ).first()

        if existing:
            raise HTTPException(409, "Invoice already exists for this period")

        try:
            invoice = self.invoices.create({
                "subscription_id": subscription.id,
                "customer_id": subscription.customer_id,
                "amount_due": plan.price,
                "amount_paid": Decimal("0.00"),
                "currency": plan.currency,
                "status": "issued",
                "period_start": start,
                "period_end": end,
                "due_date": now() + timedelta(days=7),
            })

            self.ledger.create(
                subscription.customer_id,
                invoice.id,
                "invoice_created",
                plan.price,
                plan.currency,
                f"invoice-{invoice.id}",
                "Invoice generated",
            )

            self.db.commit()
            self.db.refresh(invoice)
            return invoice
        except Exception:
            self.db.rollback()
            raise


class PaymentService:
    def __init__(self, db):
        self.db = db
        self.invoices = InvoiceRepository(db)
        self.payments = PaymentAttemptRepository(db)
        self.ledger = LedgerService(db)

    def record(self, data):
        try:
            invoice = (
                self.db.query(Invoice)
                .filter(Invoice.id == data.invoice_id)
                .with_for_update()
                .first()
            )

            if not invoice:
                raise HTTPException(404, "Invoice not found")

            if invoice.status in ("void", "paid"):
                raise HTTPException(400, "Invoice cannot accept payments")

            if data.currency != invoice.currency:
                raise HTTPException(400, "Payment currency mismatch")

            if data.status not in ("success", "failed"):
                raise HTTPException(400, "Status must be success or failed")

            if data.status == "success":
                remaining = invoice.amount_due - invoice.amount_paid
                if data.amount > remaining:
                    raise HTTPException(400, "Payment exceeds outstanding amount")

            payment = self.payments.create({
                "invoice_id": invoice.id,
                "amount": data.amount,
                "currency": data.currency,
                "status": data.status,
                "provider_reference": data.provider_reference,
                "failure_reason": data.failure_reason,
            })

            if data.status == "success":
                invoice.amount_paid += data.amount

                invoice.status = (
                    "paid" if invoice.amount_paid == invoice.amount_due
                    else "partially_paid"
                )

                entry_type = "payment_success"
            else:
                entry_type = "payment_failure"

            self.ledger.create(
                invoice.customer_id,
                invoice.id,
                entry_type,
                data.amount,
                data.currency,
                data.provider_reference,
                data.failure_reason or "Payment recorded",
            )

            self.db.commit()
            self.db.refresh(payment)
            return payment, invoice.status

        except Exception:
            self.db.rollback()
            raise
