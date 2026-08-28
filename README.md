# CashSurvive

Autonomous cash flow forecasting, stress scenario simulation, and risk engine backend for SMEs and startups.

---

## Problem Statement

Small and medium-sized businesses (SMEs) face frequent liquidity crunches not because they are unprofitable, but because of cash-flow timing misalignments:
- **Receivable Delays**: Invoices issued to customers are often collected late or default, leaving businesses with insufficient liquid capital.
- **Fixed Outflow Deadlines**: Payroll, taxes (GST/TDS), vendor payables, and loan repayments cannot be delayed without heavy penalties or operational disruption.
- **Unforeseen Shocks**: Sudden large expenses or supplier failures rapidly drain cash reserves below safe operating thresholds.
- **Lack of Forward-Looking Visibility**: Traditional accounting systems only record historical transactions rather than predicting future daily balances or stress testing against adverse financial events.

---

## Solution

**CashSurvive** provides an intelligent, automated financial survival engine:
1. **Aggregates Current Financial Position (Member 1)**: Tracks liquid cash, reserves, receivables, payables, obligations, suppliers, and credit facilities.
2. **Predicts Cash Flow & Collections with Uncertainty (Member 2)**: Runs customer payment profiling, DSO analytics, and Monte Carlo simulations to project daily balances and cash runway.
3. **Simulates Forward Stress Scenarios (Member 3)**: Stress-tests the business under receivable delays, unexpected cash shocks, supplier distress, and credit tightening.
4. **Calculates Transparent, Explainable Risk (Member 3)**: Produces an overall 0–100 risk score and identifies key risk drivers.
5. **Prepares for Autonomous Optimization (Member 4 - Future)**: Provides a clean extension interface for automated recommendation and liquidity optimization algorithms.

---

## Architecture

```
Financial State (Member 1)
       ↓
Forecasting Engine (Member 2)
       ↓
Scenario Generation (Member 3)
       ↓
Risk Evaluation (Member 3)
       ↓
Optimization Extension Hook (Member 4 - Future)
       ↓
Unified JSON Result
```

---

## Backend Structure

```
CashSurvive/
│
├── cashsurvive-Financial State/       # Member 1: Financial State & Database
│   └── backend/
│       ├── api/                      # Financial routes
│       ├── data/                     # SQLAlchemy models, schemas, SQLite DB, seed script
│       ├── services/                 # Current-state financial aggregation logic
│       └── tests/                    # Member 1 unit tests
│
├── cashsurive-forecasting/           # Member 2: Forecasting Engine
│   ├── receivable_forecast.py        # Customer payment profiling & collections forecast
│   ├── cash_forecast.py              # Daily cash flow walker, runway & summary
│   └── uncertainty.py                # Monte Carlo simulations, VaR, confidence intervals
│
├── CashSurvive_Scenario_Risk_Engine/ # Member 3: Scenario & Risk Engine
│   └── scenario_risk_engine/
│       ├── models.py                 # Dataclasses & Enums (Scenario, RiskResult, etc.)
│       ├── scenario_engine.py        # Stress scenario generation and evaluation
│       ├── risk_engine.py            # 5-factor weighted risk scoring
│       ├── shock_detector.py         # Material change and shock detection
│       ├── config.py                 # Risk weights, thresholds & parameters
│       └── tests/                    # Member 3 unit tests
│
├── integration/                      # Integration & Adapter Layer
│   ├── __init__.py                   # Package exports
│   ├── _path_setup.py                # Multi-directory path resolver
│   ├── financial_to_forecast.py      # Member 1 -> Member 2 adapter
│   ├── forecast_to_scenario.py       # Member 1 -> Member 3 adapter
│   ├── scenario_to_risk.py           # Scenario + Risk coordinator
│   ├── pipeline.py                   # Complete end-to-end pipeline orchestrator
│   └── adapters/
│       ├── __init__.py
│       └── optimization_adapter.py   # Member 4 Optimization extension point
│
├── api/                              # FastAPI REST Backend
│   ├── __init__.py
│   ├── main.py                       # FastAPI app, lifespan, CORS, exception handlers
│   ├── routes/
│   │   ├── health.py                 # GET / and GET /health
│   │   ├── financial_state.py        # GET /api/financial-state, POST /api/financial-state/seed
│   │   ├── forecast.py               # POST /api/forecast
│   │   ├── scenario.py               # POST /api/scenarios
│   │   ├── risk.py                   # POST /api/risk
│   │   └── pipeline.py               # POST /api/pipeline/run
│   └── schemas/
│       ├── requests.py               # Request validation models
│       └── responses.py              # Standard response models
│
├── tests/                            # Automated Backend Test Suite
│   ├── conftest.py                   # Test fixtures (in-memory DB, sample states)
│   ├── integration/                  # Adapter and pipeline integration tests
│   └── api/                          # FastAPI route and validation tests
│
├── requirements.txt                  # Python dependencies
├── .env.example                      # Configuration environment variables template
├── .gitignore                        # Git ignore rules
├── pytest.ini                        # Pytest configuration
└── README.md                         # Comprehensive documentation
```

---

## Data Flow

1. **Member 1 (Financial State)**: `get_financial_state(db)` queries the company's ledger and builds a Pydantic `FinancialState` containing `current_cash`, `minimum_cash_reserve`, `receivables`, `payables`, `obligations`, `suppliers`, and `financing_options`.
2. **Member 1 → Member 2 Adapter (`financial_to_forecast.py`)**:
   - Converts receivables into `Invoice` objects (inferring 30-day issue dates and status mapping).
   - Converts unpaid/overdue payables and upcoming obligations into `CashFlowItem` outflows (negative amounts).
   - Initializes `ReceivableForecaster` and `CashFlowForecaster` with attached receivables.
   - Executes Monte Carlo simulations to produce daily balance projections with 90% confidence bands and runway metrics.
3. **Member 1 → Member 3 Adapter (`forecast_to_scenario.py`)**:
   - Converts `FinancialState` to Member 3 `scenario_risk_engine.models.FinancialState` dataclass.
   - Calculates relative `expected_days` and `due_days` from `as_of`.
4. **Member 3 (Scenario & Risk Coordinator `scenario_to_risk.py`)**:
   - Generates standard scenarios: *Normal / Baseline*, *Receivable Delay*, *Cash Shock*, *Supplier Stress*, and *Financing Shock*.
   - Evaluates each scenario's projected cash balance, cash impact, liquidity ratio, liquidity status, and risk level.
   - Calculates 5-factor weighted baseline risk (Liquidity: 35%, Receivable: 20%, Supplier: 20%, Obligation: 15%, Financing: 10%).
5. **Member 4 Hook (`optimization_adapter.py`)**:
   - Passes the aggregated pipeline context to the extension point. Returns `{ "status": "ready_for_extension", "implemented": false }`.
6. **Unified Result**:
   - `pipeline.py` returns a single JSON-serializable dictionary with all data.

---

## Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Git

### 1. Clone & Navigate to Project Root
```bash
cd CashSurvive
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
```

### 3. Activate Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Backend

Start the FastAPI application from the project root:

```bash
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The server will automatically:
1. Initialize the SQLite database (`cashsurvive.db`).
2. Seed default demo data for *Aarav Textiles Pvt Ltd* if the database is fresh.
3. Serve OpenAPI documentation at `http://localhost:8000/docs`.

---

## Testing

Run all 68 automated tests (API tests, integration tests, and individual member tests):

```bash
python -m pytest
```

Run specific test suites:
```bash
# Run integration tests
python -m pytest tests/integration

# Run API tests
python -m pytest tests/api

# Run Member 1 tests
python -m pytest "cashsurvive-Financial State/backend/tests"

# Run Member 3 tests
python -m pytest "CashSurvive_Scenario_Risk_Engine/scenario_risk_engine/tests"
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root service metadata and documentation links |
| `GET` | `/health` | Fast module availability check |
| `GET` | `/api/financial-state` | Fetch current company financial state from DB |
| `POST` | `/api/financial-state/seed` | Seed default demo company records |
| `POST` | `/api/forecast` | Run standalone cash flow & receivables forecast |
| `POST` | `/api/scenarios` | Run standalone stress scenario simulation |
| `POST` | `/api/risk` | Run standalone risk evaluation and factor breakdown |
| `POST` | `/api/pipeline/run` | **Primary Unified Pipeline Endpoint** |

---

## API Contract & Examples

### 1. Run Complete Pipeline (`POST /api/pipeline/run`)

#### Request Body
```json
{
  "horizon_days": 30,
  "num_simulations": 2000,
  "confidence_level": 0.90
}
```

*Note: You can also pass a custom `financial_state` object to run the pipeline on custom numbers without writing to the database.*

#### Response Body (200 OK)
```json
{
  "status": "success",
  "financial_state": {
    "as_of": "2026-08-28",
    "currency": "INR",
    "current_cash": 5000000.0,
    "minimum_cash_reserve": 2000000.0,
    "cash_above_reserve": 3000000.0,
    "total_receivables": 5500000.0,
    "total_payables": 2800000.0,
    "total_obligations": 1450000.0,
    "overdue_payables_count": 1,
    "delayed_receivables_count": 1,
    "receivables": [...],
    "payables": [...],
    "suppliers": [...],
    "obligations": [...],
    "financing_options": [...]
  },
  "forecast": {
    "summary": {
      "starting_balance": 5000000.0,
      "ending_balance": 5250000.0,
      "lowest_balance": 3900000.0,
      "lowest_balance_date": "2026-09-07",
      "runway_days": null,
      "probability_of_shortfall_pct": 0.0,
      "scenario": {
        "best_case": 5375000.0,
        "likely_case": 5250000.0,
        "worst_case": 5125000.0
      },
      "recommendations": [
        "Cash position looks stable over the forecast horizon. No immediate action needed.",
        "Follow up with high-risk customers identified in the receivables aging report to pull forward collections."
      ]
    },
    "projections": [
      {
        "date": "2026-08-29",
        "scheduled_net": 0.0,
        "receivable_inflow": 0.0,
        "projected_balance": 5000000.0,
        "is_shortfall": false,
        "line_items": [],
        "uncertainty": {
          "mean": 5000000.0,
          "std_dev": 1500.0,
          "lower_bound": 4997500.0,
          "upper_bound": 5002500.0,
          "confidence_level": 0.90,
          "var_95": 2467.0
        }
      }
    ],
    "receivable_aging": {
      "current": 4500000.0,
      "1-30": 1000000.0,
      "31-60": 0.0,
      "61-90": 0.0,
      "90+": 0.0
    },
    "days_sales_outstanding": 30.0,
    "customer_profiles": [...]
  },
  "scenarios": [
    {
      "scenario_id": "scn-normal-a1b2c3d4",
      "name": "Normal / Baseline",
      "scenario_type": "NORMAL",
      "severity": "LOW",
      "projected_cash": 5400000.0,
      "cash_impact": 0.0,
      "liquidity_ratio": 2.7,
      "liquidity_status": "HEALTHY",
      "risk_score": 38.5,
      "risk_level": "MEDIUM",
      "affected_items": [],
      "description": "Business-as-usual projection assuming receivables arrive on schedule and no unexpected obligations occur."
    },
    {
      "scenario_id": "scn-recv-delay-e5f6g7h8",
      "name": "Receivable Delay (15 days)",
      "scenario_type": "RECEIVABLE_DELAY",
      "severity": "MEDIUM",
      "projected_cash": 3900000.0,
      "cash_impact": -1500000.0,
      "liquidity_ratio": 1.95,
      "liquidity_status": "HEALTHY",
      "risk_score": 52.0,
      "risk_level": "MEDIUM",
      "affected_items": ["AR-1", "AR-2", "AR-3"],
      "description": "Simulates a 15-day delay affecting all receivables, including a corresponding drop in collection probability."
    },
    {
      "scenario_id": "scn-cash-shock-i9j0k1l2",
      "name": "Unexpected Cash Shock",
      "scenario_type": "CASH_SHOCK",
      "severity": "MEDIUM",
      "projected_cash": 4400000.0,
      "cash_impact": -1000000.0,
      "liquidity_ratio": 2.2,
      "liquidity_status": "HEALTHY",
      "risk_score": 48.2,
      "risk_level": "MEDIUM",
      "affected_items": ["obl-shock-m3n4o5p6"],
      "description": "Simulates an unexpected obligation of 1,000,000.00 hitting the business immediately."
    }
  ],
  "risk": {
    "risk_score": 38.5,
    "risk_level": "MEDIUM",
    "risk_factors": [
      "Liquidity buffer is approaching the minimum reserve level.",
      "A significant portion of expected receivables carry low collection probability."
    ],
    "explanation": "Overall risk score is 38.5/100 (MEDIUM), driven primarily by receivable risk.",
    "factor_breakdown": {
      "liquidity": 15.0,
      "receivable": 42.5,
      "supplier": 28.0,
      "obligation": 35.0,
      "financing": 20.0
    }
  },
  "shocks": null,
  "reoptimization_required": false,
  "optimization_extension": {
    "status": "ready_for_extension",
    "implemented": false,
    "message": "Optimization Engine (Member 4) is NOT implemented. Architectural extension hook is ready.",
    "recommended_actions": []
  }
}
```

---

## Frontend Integration

The backend is pre-configured with CORS for modern frontend frameworks (e.g. React + Vite on `http://localhost:5173`).

### Example React API Hook
```typescript
// src/api/cashsurvive.ts
const API_BASE = 'http://localhost:8000';

export async function fetchPipelineResults(horizonDays: number = 30) {
  const response = await fetch(`${API_BASE}/api/pipeline/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ horizon_days: horizonDays, num_simulations: 2000 })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || 'Pipeline execution failed');
  }

  return response.json();
}
```

---

## Team & Module Ownership

- **Member 1** → Financial State Ledger & Aggregation (`cashsurvive-Financial State`)
- **Member 2** → Cash Flow & AR Forecasting Engine (`cashsurive-forecasting`)
- **Member 3** → Scenario Generation, Stress Testing & Risk Engine (`CashSurvive_Scenario_Risk_Engine`)
- **Member 4** → Optimization Engine — **FUTURE / NOT IMPLEMENTED**
  *(Clean architectural extension point provided in `integration/adapters/optimization_adapter.py`)*

---

## Future Work

1. **Member 4 Optimization Engine**: Connect linear programming / constraint optimization algorithms to generate actionable payment schedules and credit line draws.
2. **Autonomous Recommendation Engine**: Dynamic early payment discount acceptance vs late payment penalty trade-offs.
3. **Automated Shock Detection & Webhooks**: Continuous monitoring for unexpected outflows and automatic alert triggers.
