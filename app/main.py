
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db import database
from app import models

from app.db.database import get_db
from app.services.services import (
    PlanService, CustomerService, SubscriptionService,
    InvoiceService, PaymentService, LedgerService
)
from app.schemas.common import (
    PlanCreate, PlanUpdate, PlanResponse,
    CustomerCreate, CustomerResponse,
    SubscriptionCreate, SubscriptionResponse,
    InvoiceGenerate, InvoiceResponse,
    PaymentCreate, PaymentResponse, LedgerResponse
)

app = FastAPI(
    title="SubLedger API",
    description="SaaS Subscription Billing Backend",
    version="1.0.0",
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=database.engine)

@app.get("/")
def health():
    return {"message": "SubLedger API is running"}


# PLANS

@app.post("/plans", response_model=PlanResponse, status_code=201)
def create_plan(data: PlanCreate, db: Session = Depends(get_db)):
    return PlanService(db).create(data)


@app.get("/plans", response_model=list[PlanResponse])
def list_plans(db: Session = Depends(get_db)):
    return PlanService(db).list()


@app.patch("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: int, data: PlanUpdate, db: Session = Depends(get_db)):
    return PlanService(db).update(plan_id, data)


# CUSTOMERS

@app.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    return CustomerService(db).create(data)


@app.get("/customers", response_model=list[CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    return CustomerService(db).list()


@app.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return CustomerService(db).get(customer_id)


# SUBSCRIPTIONS

@app.post("/subscriptions", response_model=SubscriptionResponse, status_code=201)
def create_subscription(data: SubscriptionCreate, db: Session = Depends(get_db)):
    return SubscriptionService(db).create(data)


@app.get("/subscriptions", response_model=list[SubscriptionResponse])
def list_subscriptions(db: Session = Depends(get_db)):
    return SubscriptionService(db).list()


@app.patch("/subscriptions/{subscription_id}/cancel")
def cancel_subscription(subscription_id: int, db: Session = Depends(get_db)):
    return SubscriptionService(db).cancel(subscription_id)


# INVOICES

@app.post("/invoices/generate", response_model=InvoiceResponse, status_code=201)
def generate_invoice(data: InvoiceGenerate, db: Session = Depends(get_db)):
    return InvoiceService(db).generate(data.subscription_id)


@app.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    from app.repositories.repositories import InvoiceRepository
    invoice = InvoiceRepository(db).get(invoice_id)

    if not invoice:
        from fastapi import HTTPException
        raise HTTPException(404, "Invoice not found")

    return invoice


# PAYMENTS

@app.post("/payments/record", status_code=201)
def record_payment(data: PaymentCreate, db: Session = Depends(get_db)):
    payment, invoice_status = PaymentService(db).record(data)
    return {
        "payment": PaymentResponse.model_validate(payment),
        "invoice_status": invoice_status,
    }


# LEDGER

@app.get("/customers/{customer_id}/ledger", response_model=list[LedgerResponse])
def get_customer_ledger(customer_id: int, db: Session = Depends(get_db)):
    return LedgerService(db).get_customer_ledger(customer_id)
