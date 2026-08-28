"""
_path_setup.py
==============
Configures Python path to ensure all three backend modules are importable:
- Member 1: Financial State (cashsurvive-Financial State/backend)
- Member 2: Forecasting Engine (cashsurive-forecasting)
- Member 3: Scenario & Risk Engine (CashSurvive_Scenario_Risk_Engine)
"""

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# Resolve candidate paths for each member
CANDIDATE_PATHS = [
    # Member 1
    PROJECT_ROOT / "cashsurvive-Financial State" / "backend",
    PROJECT_ROOT / "financial_state" / "backend",
    # Member 2
    PROJECT_ROOT / "cashsurive-forecasting",
    PROJECT_ROOT / "forecasting",
    # Member 3
    PROJECT_ROOT / "CashSurvive_Scenario_Risk_Engine",
    PROJECT_ROOT / "scenario_risk",
    PROJECT_ROOT,
]

for p in CANDIDATE_PATHS:
    p_str = str(p.resolve())
    if p.exists() and p_str not in sys.path:
        sys.path.insert(0, p_str)
