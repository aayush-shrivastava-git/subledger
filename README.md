
# SubLedger – SaaS Billing Backend

SubLedger is a simplified SaaS subscription billing backend built using Python, FastAPI, SQLAlchemy, and PostgreSQL.

It manages subscription plans, customers, subscriptions, invoices, payment attempts, and financial ledger entries.

## Features

- Plan creation, listing, and updating.
- Customer registration and retrieval.
- Subscription creation and cancellation.
- Invoice generation with billing period validation.
- Payment recording with partial and full payment support.
- Financial ledger tracking.
- Transaction-based payment processing.
- REST API documentation using Swagger.
- Automated business-rule tests.

## Technology Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL 16
- Pydantic
- Pytest
- Docker

## Project Structure

```text
subledger/
├── app/
│   ├── main.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── core/
│   └── db/
├── tests/
├── DESIGN.md
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Local Setup

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd subledger
```

### 2. Create virtual environment

```bash
python -m venv .venv
```

Activate on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create a `.env` file:

```env
DATABASE_URL=postgresql+psycopg2://subledger:subledger123@localhost:5432/subledger
```

### 5. Start PostgreSQL

```bash
docker compose up -d db
```

### 6. Start application

```bash
uvicorn app.main:app --reload
```

Application URL:

http://127.0.0.1:8000

Swagger documentation:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /plans | Create plan |
| GET | /plans | List plans |
| PATCH | /plans/{plan_id} | Update plan |
| POST | /customers | Create customer |
| GET | /customers | List customers |
| GET | /customers/{customer_id} | Get customer |
| POST | /subscriptions | Create subscription |
| GET | /subscriptions | List subscriptions |
| PATCH | /subscriptions/{subscription_id}/cancel | Cancel subscription |
| POST | /invoices/generate | Generate invoice |
| GET | /invoices/{invoice_id} | Get invoice |
| POST | /payments/record | Record payment |
| GET | /customers/{customer_id}/ledger | Get customer ledger |

## Business Rules

- Plan price must be positive.
- Customer email must be unique.
- Inactive plans cannot be subscribed to.
- Duplicate active subscriptions are prevented.
- Invoice amounts use the plan price at generation time.
- Successful payments cannot exceed outstanding balances.
- Failed payments do not change invoice paid amounts.
- Invoice status reflects payment progress.
- Ledger entries are append-only through the application interface.

## Testing

Run automated tests:

```bash
pytest -v
```

The test suite covers plan validation, customer uniqueness, subscription validation, payment limits, and failed payment handling.

## Assumptions and Limitations

- Payment processing is simulated.
- No external payment gateway is integrated.
- Subscription renewal is not automated.
- Complex taxation and proration are outside scope.
- Authentication and authorization are not included.
- Billing periods are calculated using simplified fixed-day durations.

## Design Documentation

Refer to DESIGN.md for entity relationships, architecture, service responsibilities, repository responsibilities, business rules, and core workflows.
