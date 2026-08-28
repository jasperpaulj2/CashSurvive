# CashSurvive AI — Financial Data & Financial State Module (Member 1)

This is the financial data foundation for **CashSurvive AI**, an autonomous
working-capital management system. This module owns:

- Data models (Company, Receivable, Payable, Supplier, Obligation, FinancingOption)
- Database (SQLite via SQLAlchemy 2.x)
- Validation (Pydantic v2)
- The **FinancialState** — the single source of truth for the rest of the backend
- Seed data for one demo company
- Read API endpoints
- Tests

It deliberately does **not** forecast, generate scenarios, optimize, or make
autonomous decisions — those belong to Members 2, 3, and 4.

## Folder structure

```
backend/
├── data/
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic schemas + FinancialState contract
│   ├── database.py       # engine, session factory, Base, init_db()
│   ├── repository.py     # all DB access lives here
│   └── seed_data.py       # demo data for one fictional company
├── services/
│   └── financial_state.py  # get_financial_state()
├── api/
│   └── financial_routes.py # GET endpoints
├── tests/
│   ├── conftest.py
│   ├── test_schemas.py
│   ├── test_repository.py
│   └── test_financial_state.py
├── main.py
├── requirements.txt
└── README.md
```

## Data model relationships

- `Company` — single row for the demo; holds `current_cash` and `minimum_cash_reserve`.
- `Supplier` — has many `Payable`s (`Payable.supplier_id` → `Supplier.id`).
- `Receivable` — standalone; money owed *to* the company by customers.
- `Payable` — money owed *by* the company to a supplier; carries invoice/due/early-payment dates and discount/penalty percentages.
- `Obligation` — non-supplier cash outflows (payroll, tax, rent, loan repayment, utilities), each with a `priority` (1 = highest).
- `FinancingOption` — external capital sources (line of credit, invoice factoring, etc.) available if needed.

None of these reference forecasts, scenarios, or optimization decisions — those are computed by other modules *from* this data.

## The `FinancialState` contract

`GET /financial-state` returns the current snapshot of the company's finances.
This is the object the rest of the team builds on:

| Consumer | Uses |
|---|---|
| **Member 2 — Forecasting** | `current_cash`, `receivables`, `payables`, `obligations` to project future cash |
| **Member 3 — Scenario/Risk** | `suppliers`, `payables`, `obligations`, `cash_above_reserve` to stress-test the position |
| **Member 4 — Optimization** | The full `FinancialState`, plus Member 2 and 3's outputs, to allocate capital |

Example response shape:

```json
{
  "as_of": "2026-08-28",
  "currency": "INR",
  "current_cash": 5000000,
  "minimum_cash_reserve": 2000000,
  "cash_above_reserve": 3000000,
  "total_receivables": 5500000,
  "total_payables": 2800000,
  "total_obligations": 1450000,
  "overdue_payables_count": 1,
  "delayed_receivables_count": 1,
  "receivables": [ { "id": 1, "customer": "ABC Ltd", "amount": 3000000, "expected_date": "2026-09-12", "payment_probability": 0.9, "status": "expected" }, ... ],
  "payables": [ { "id": 1, "supplier_id": 1, "amount": 1000000, "invoice_date": "2026-08-08", "due_date": "2026-09-07", "early_payment_date": "2026-08-31", "discount_percent": 2.0, "late_penalty_percent": 1.5, "status": "unpaid" }, ... ],
  "suppliers": [ { "id": 1, "name": "Supplier A - Raw Cotton Co", "strategic_importance": 0.9, "liquidity_risk": 0.2, "dependency_score": 0.8 }, ... ],
  "obligations": [ { "id": 1, "name": "Monthly Payroll", "obligation_type": "payroll", "amount": 900000, "due_date": "2026-09-02", "priority": 1 }, ... ],
  "financing_options": [ { "id": 1, "provider": "HDFC Bank", "financing_type": "line_of_credit", "maximum_amount": 3000000, "annual_interest_rate": 0.12, "available": true }, ... ]
}
```

**Design decision (documented per spec):** `minimum_cash_reserve` is allowed to
exceed `current_cash`. This isn't a bug — it's a valid, meaningful state (the
company is already below its target reserve) that Member 3's risk engine needs
to be able to see. Only non-negativity is enforced on both fields.

## Setup (VS Code / local)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Initialize the database + load seed data

```bash
python -m data.seed_data
```

This creates `cashsurvive.db` (SQLite) in the `backend/` folder and inserts
one demo company ("Aarav Textiles Pvt Ltd") with receivables, payables,
suppliers, obligations, and financing options in INR.

Re-running this will insert duplicate rows — delete `cashsurvive.db` first
if you want a clean reseed.

## Run the API

```bash
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000/docs for interactive Swagger docs, or call:

- `GET /financial-state`
- `GET /company`
- `GET /receivables`
- `GET /payables`
- `GET /suppliers`
- `GET /obligations`
- `GET /financing-options`

## Run tests

```bash
pytest -v
```

Tests use an isolated in-memory SQLite database (via fixtures in
`tests/conftest.py`), so they never touch `cashsurvive.db`.

## How Members 2, 3, 4 should consume this module

1. Call `GET /financial-state` (or, if working in-process, import and call
   `services.financial_state.get_financial_state(db)` directly) to get a
   `FinancialState` object/JSON payload.
2. Treat it as read-only, current-state input — do not mutate it.
3. Build your forecast / scenario / optimization output as a **separate**
   object that references this `FinancialState` (e.g. by embedding it or an
   `as_of` timestamp), rather than modifying these schemas. If you need a new
   field on `FinancialState` itself, coordinate with Member 1 rather than
   patching the API response ad hoc — it's the shared contract every module
   depends on.
