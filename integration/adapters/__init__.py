"""
adapters package
================
Contains extension adapters for CashSurvive components.
"""

from integration.adapters.optimization_adapter import (
    OptimizationEngineExtension,
    NoOpOptimizationAdapter,
)

__all__ = [
    "OptimizationEngineExtension",
    "NoOpOptimizationAdapter",
]
