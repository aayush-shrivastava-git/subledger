from pydantic import BaseModel, ConfigDict, EmailStr, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# PLAN
class PlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    billing_cycle: str
    price: Decimal = Field(gt=0)
    currency: str = "INR"


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    billing_cycle: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, gt=0)
    status: Optional[str] = None


class PlanResponse(ORMBase):
    id: int
    name: str
    billing_cycle: str
    price: Decimal
    currency: str
    status: str


# CUSTOMER
class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    company_name: Optional[str] = None


class CustomerResponse(ORMBase):
    id: int
    name: str
    email: str
    company_name: Optional[str]
    status: str


# SUBSCRIPTION
class SubscriptionCreate(BaseModel):
    customer_id: int
    plan_id: int


class SubscriptionResponse(ORMBase):
    id: int
    customer_id: int
    plan_id: int
    status: str
    current_period_start: datetime
    current_period_end: datetime


# INVOICE
class InvoiceGenerate(BaseModel):
    subscription_id: int


class InvoiceResponse(ORMBase):
    id: int
    subscription_id: int
    customer_id: int
    amount_due: Decimal
    amount_paid: Decimal
    currency: str
    status: str
    period_start: datetime
    period_end: datetime
    due_date: datetime


# PAYMENT
class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal = Field(gt=0)
    currency: str = "INR"
    status: str
    provider_reference: str
    failure_reason: Optional[str] = None


class PaymentResponse(ORMBase):
    id: int
    invoice_id: int
    amount: Decimal
    currency: str
    status: str
    provider_reference: Optional[str]
    failure_reason: Optional[str]


# LEDGER
class LedgerResponse(ORMBase):
    id: int
    customer_id: int
    invoice_id: Optional[int]
    entry_type: str
    amount: Decimal
    currency: str
    reference_id: str
    description: Optional[str]
    created_at: datetime