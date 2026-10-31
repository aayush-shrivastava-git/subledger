from decimal import Decimal


def create_customer(client):
    response = client.post("/customers", json={
        "name": "Test Customer",
        "email": "test@example.com",
        "company_name": "Test Company",
    })
    assert response.status_code == 201
    return response.json()["id"]


def create_plan(client, price=1000, status="active"):
    response = client.post("/plans", json={
        "name": "Premium",
        "billing_cycle": "monthly",
        "price": price,
        "currency": "INR",
    })
    assert response.status_code == 201

    if status == "inactive":
        client.patch(f"/plans/{response.json()['id']}", json={
            "status": "inactive"
        })

    return response.json()["id"]


def create_subscription(client):
    customer_id = create_customer(client)
    plan_id = create_plan(client)

    response = client.post("/subscriptions", json={
        "customer_id": customer_id,
        "plan_id": plan_id,
    })
    assert response.status_code == 201
    return response.json()


def create_invoice(client):
    subscription = create_subscription(client)
    response = client.post("/invoices/generate", json={
        "subscription_id": subscription["id"]
    })
    assert response.status_code == 201
    return response.json()


def test_plan_price_must_be_positive(client):
    response = client.post("/plans", json={
        "name": "Invalid Plan",
        "billing_cycle": "monthly",
        "price": 0,
        "currency": "INR",
    })
    assert response.status_code == 422


def test_customer_email_must_be_unique(client):
    create_customer(client)

    response = client.post("/customers", json={
        "name": "Another Customer",
        "email": "test@example.com",
    })
    assert response.status_code == 409


def test_inactive_plan_cannot_be_subscribed(client):
    customer_id = create_customer(client)
    plan_id = create_plan(client, status="inactive")

    response = client.post("/subscriptions", json={
        "customer_id": customer_id,
        "plan_id": plan_id,
    })
    assert response.status_code == 400


def test_duplicate_active_subscription_not_allowed(client):
    subscription = create_subscription(client)

    response = client.post("/subscriptions", json={
        "customer_id": subscription["customer_id"],
        "plan_id": subscription["plan_id"],
    })
    assert response.status_code == 409


def test_payment_cannot_exceed_invoice_amount(client):
    invoice = create_invoice(client)

    response = client.post("/payments/record", json={
        "invoice_id": invoice["id"],
        "amount": 1500,
        "currency": "INR",
        "status": "success",
        "provider_reference": "PAY-001",
    })

    assert response.status_code == 400


def test_failed_payment_does_not_increase_amount_paid(client):
    invoice = create_invoice(client)

    response = client.post("/payments/record", json={
        "invoice_id": invoice["id"],
        "amount": 500,
        "currency": "INR",
        "status": "failed",
        "provider_reference": "PAY-002",
        "failure_reason": "Insufficient funds",
    })

    assert response.status_code == 201

    updated_invoice = client.get(
        f"/invoices/{invoice['id']}"
    ).json()

    assert Decimal(str(updated_invoice["amount_paid"])) == Decimal("0.00")
    assert updated_invoice["status"] == "issued"