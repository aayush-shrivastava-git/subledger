
## 10. Service Responsibilities

| Service | Responsibility |
|---|---|
| PlanService | Plan creation, updates and validation |
| CustomerService | Customer creation and email uniqueness |
| SubscriptionService | Subscription lifecycle and plan validation |
| InvoiceService | Invoice generation and billing calculations |
| PaymentService | Payment validation and invoice updates |
| LedgerService | Financial event recording and retrieval |

## 11. Repository Responsibilities

| Repository | Responsibility |
|---|---|
| PlanRepository | Plan database operations |
| CustomerRepository | Customer database operations |
| SubscriptionRepository | Subscription database operations |
| InvoiceRepository | Invoice database operations |
| PaymentAttemptRepository | Payment attempt persistence |
| LedgerRepository | Ledger entry persistence and retrieval |

## 12. Business Rule Ownership

| Business Rule | Enforcement |
|---|---|
| Positive plan price | Pydantic schema and database constraint |
| Unique customer email | CustomerService and database constraint |
| Active plan required | SubscriptionService |
| Unique active subscription | SubscriptionService and partial unique index |
| Invoice price snapshot | InvoiceService |
| Payment cannot exceed balance | PaymentService |
| Failed payment does not update invoice | PaymentService |
| Invoice status calculation | PaymentService |
| Append-only ledger | LedgerService and application interface |

## 13. Invoice Generation Flow

1. API receives subscription ID.
2. InvoiceService retrieves the subscription.
3. Subscription status is validated.
4. Associated plan is retrieved.
5. Current billing period and plan price are determined.
6. Duplicate billing period is checked.
7. Invoice is created.
8. An invoice_created ledger entry is created.
9. Database transaction is committed.
10. Invoice response is returned.

## 14. Payment Recording Flow

1. API receives invoice ID, amount, currency and payment status.
2. PaymentService retrieves and locks the invoice.
3. Invoice existence and payment eligibility are validated.
4. Payment currency and amount are validated.
5. PaymentAttempt is created.
6. Successful payments update amount_paid and invoice status.
7. Failed payments leave amount_paid unchanged.
8. Corresponding ledger entry is created.
9. All changes are committed atomically.
10. Payment response is returned.

## 15. Transaction Management

SQLAlchemy database sessions are used to manage transactions.

Payment recording uses a database transaction and row-level locking to protect invoice balances from concurrent payment requests.

If any operation fails, the transaction is rolled back.

## 16. Design Patterns

### Repository Pattern

Database operations are isolated within repository classes.

### Service Layer Pattern

Business rules and workflows are implemented within service classes.

### Dependency Injection

FastAPI dependency injection provides database sessions to API endpoints.

## 17. Limitations

- No real payment gateway.
- No automated recurring billing.
- No subscription proration.
- No authentication or role-based authorization.
- Ledger immutability is enforced at application level, not through database permissions.
