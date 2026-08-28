"""
exceptions.py
=============
Custom exceptions for the Scenario & Risk Engine module.
"""


class ScenarioRiskEngineError(Exception):
    """Base exception for all errors raised by this module."""


class InvalidFinancialStateError(ScenarioRiskEngineError):
    """Raised when a FinancialState is missing required data or contains
    logically invalid values (e.g. negative minimum_cash_reserve)."""


class InvalidScenarioError(ScenarioRiskEngineError):
    """Raised when a Scenario is malformed, references data that does not
    exist (e.g. an unknown receivable_id), or has invalid parameters."""


class InvalidRiskInputError(ScenarioRiskEngineError):
    """Raised when inputs supplied to the RiskEngine cannot be used to
    produce a valid risk assessment."""
