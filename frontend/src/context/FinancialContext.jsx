/**
 * FinancialContext.jsx
 * ====================
 * Global state management for CashSurvive control tower.
 * Supports live backend communication with automatic fallback to realistic demo state.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { MOCK_PIPELINE_DATA } from '../services/mockData';

const FinancialContext = createContext(null);

export function FinancialProvider({ children }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [healthStatus, setHealthStatus] = useState(null);
  const [financialState, setFinancialState] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState(null);
  const [isOfflineMode, setIsOfflineMode] = useState(false);

  // Forecast settings
  const [horizonDays, setHorizonDays] = useState(30);
  const [numSimulations, setNumSimulations] = useState(2000);

  // Custom What-If Scenario State
  const [customScenarioParams, setCustomScenarioParams] = useState({
    delayDays: 14,
    defaultPct: 15,
    costSpikePct: 10,
    creditFreeze: false,
  });
  const [customScenarioResult, setCustomScenarioResult] = useState(null);

  // Enable offline fallback demo
  const enableOfflineDemo = useCallback(() => {
    setIsOfflineMode(true);
    setError(null);
    setFinancialState(MOCK_PIPELINE_DATA.financial_state);
    setPipelineData(MOCK_PIPELINE_DATA);
  }, []);

  // Check health
  const checkHealth = useCallback(async () => {
    try {
      const data = await api.getHealth();
      setHealthStatus(data);
      if (data?.status === 'healthy') {
        setIsOfflineMode(false);
      }
      return data;
    } catch (err) {
      setHealthStatus({ status: 'unreachable', error: err.message });
      return null;
    }
  }, []);

  // Fetch financial state from DB
  const loadFinancialState = useCallback(async () => {
    try {
      setError(null);
      const data = await api.getFinancialState();
      setFinancialState(data);
      return data;
    } catch (err) {
      setError(err);
      return null;
    }
  }, []);

  // Execute full pipeline
  const executePipeline = useCallback(async (customOverrides = {}) => {
    setAnalyzing(true);
    setError(null);
    try {
      const payload = {
        horizon_days: customOverrides.horizon_days || horizonDays,
        num_simulations: customOverrides.num_simulations || numSimulations,
        confidence_level: customOverrides.confidence_level || 0.90,
        financial_state: customOverrides.financial_state || financialState || undefined,
        previous_state: customOverrides.previous_state || undefined,
      };

      const result = await api.runPipeline(payload);
      setPipelineData(result);
      if (result.financial_state) {
        setFinancialState(result.financial_state);
      }
      setIsOfflineMode(false);
      return result;
    } catch (err) {
      console.warn('API runPipeline failed, evaluating fallback options:', err.message);
      setError(err);
      // If we don't have pipeline data yet, switch to offline demo so user is not stuck
      if (!pipelineData) {
        enableOfflineDemo();
      }
      return null;
    } finally {
      setAnalyzing(false);
    }
  }, [horizonDays, numSimulations, financialState, pipelineData, enableOfflineDemo]);

  // Seed demo data
  const seedDemoData = useCallback(async () => {
    setSeeding(true);
    setError(null);
    try {
      await api.seedFinancialState();
      // Re-run pipeline after seeding
      const res = await executePipeline();
      return res;
    } catch (err) {
      console.warn('Seed API failed, falling back to local demo state:', err.message);
      enableOfflineDemo();
      return MOCK_PIPELINE_DATA;
    } finally {
      setSeeding(false);
    }
  }, [executePipeline, enableOfflineDemo]);

  // Client-side / What-if Stress Simulator
  const runCustomWhatIfScenario = useCallback((params) => {
    const activeData = pipelineData || MOCK_PIPELINE_DATA;
    const baseProjections = activeData?.forecast?.projections || [];
    const baseSummary = activeData?.forecast?.summary || {};
    const baseCash = activeData?.financial_state?.current_cash || 2500000;
    const minReserve = activeData?.financial_state?.minimum_cash_reserve || 1500000;

    const delay = Number(params.delayDays || 0);
    const defPct = Number(params.defaultPct || 0) / 100;
    const costSpike = Number(params.costSpikePct || 0) / 100;
    const freeze = Boolean(params.creditFreeze);

    // Compute simulated projection trajectory
    let runningBalance = baseCash;
    let minBalance = baseCash;
    let breachDay = null;

    const simulatedProjections = baseProjections.map((p, idx) => {
      // Inflow reduced by default % and delayed
      const delayedInflow = idx >= delay ? p.receivable_inflow * (1 - defPct) : 0;
      // Scheduled outflow increased by cost spike
      const scheduledOut = p.scheduled_net < 0 ? p.scheduled_net * (1 + costSpike) : p.scheduled_net;
      
      runningBalance += scheduledOut + delayedInflow;
      if (runningBalance < minBalance) {
        minBalance = runningBalance;
      }
      if (runningBalance < minReserve && breachDay === null) {
        breachDay = idx + 1;
      }

      return {
        ...p,
        simulated_balance: Math.round(runningBalance),
        is_simulated_shortfall: runningBalance < minReserve,
      };
    });

    const endingBalance = simulatedProjections.length > 0
      ? simulatedProjections[simulatedProjections.length - 1].simulated_balance
      : runningBalance;

    const cashImpact = endingBalance - (baseSummary.ending_balance || baseCash);

    let liquidityStatus = 'HEALTHY';
    let riskLevel = 'LOW';
    let riskScore = 30;

    if (minBalance < 0) {
      liquidityStatus = 'NEGATIVE';
      riskLevel = 'CRITICAL';
      riskScore = 85 + Math.min(15, Math.abs(minBalance) / 100000);
    } else if (minBalance < minReserve) {
      liquidityStatus = 'BELOW_MINIMUM';
      riskLevel = 'HIGH';
      riskScore = 65 + (1 - minBalance / minReserve) * 20;
    } else if (minBalance < minReserve * 1.3) {
      liquidityStatus = 'TIGHT';
      riskLevel = 'MEDIUM';
      riskScore = 45;
    }

    if (freeze) {
      riskScore = Math.min(100, riskScore + 15);
      if (riskLevel === 'MEDIUM') riskLevel = 'HIGH';
    }

    const result = {
      params: { delayDays: delay, defaultPct: defPct * 100, costSpikePct: costSpike * 100, creditFreeze: freeze },
      projections: simulatedProjections,
      min_cash: Math.round(minBalance),
      projected_cash: Math.round(endingBalance),
      cash_impact: Math.round(cashImpact),
      liquidity_status: liquidityStatus,
      risk_score: Math.min(100, Math.round(riskScore)),
      risk_level: riskLevel,
      breach_day: breachDay,
      runway_days: breachDay ? Math.max(1, breachDay) : baseSummary.runway_days || 42,
    };

    setCustomScenarioResult(result);
    return result;
  }, [pipelineData]);

  // Add invoice simulation
  const addInvoice = useCallback((newInvoice) => {
    setFinancialState((prev) => {
      const currentState = prev || MOCK_PIPELINE_DATA.financial_state;
      const updated = {
        ...currentState,
        receivables: [
          ...currentState.receivables,
          {
            invoice_number: newInvoice.invoice_number || `INV-${Date.now().toString().slice(-4)}`,
            customer_id: newInvoice.customer_id,
            amount: Number(newInvoice.amount),
            due_date: newInvoice.due_date,
            status: 'PENDING',
            days_overdue: 0,
            expected_payment_date: newInvoice.expected_payment_date || newInvoice.due_date,
            payment_reliability: newInvoice.payment_reliability || 'HIGH',
          },
        ],
      };
      return updated;
    });
  }, []);

  // Add bill simulation
  const addBill = useCallback((newBill) => {
    setFinancialState((prev) => {
      const currentState = prev || MOCK_PIPELINE_DATA.financial_state;
      const updated = {
        ...currentState,
        payables: [
          ...currentState.payables,
          {
            bill_number: newBill.bill_number || `BILL-${Date.now().toString().slice(-4)}`,
            vendor_id: newBill.vendor_id,
            amount: Number(newBill.amount),
            due_date: newBill.due_date,
            category: newBill.category || 'OPERATIONAL',
            is_critical: Boolean(newBill.is_critical),
            status: 'PENDING',
            payment_terms: newBill.payment_terms || 'NET30',
          },
        ],
      };
      return updated;
    });
  }, []);

  // Initial mount: check health, then run pipeline
  useEffect(() => {
    let isMounted = true;
    async function init() {
      setLoading(true);
      const health = await checkHealth();
      if (isMounted) {
        if (health && health.status === 'healthy') {
          await executePipeline();
        } else {
          enableOfflineDemo();
        }
        setLoading(false);
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, [checkHealth, executePipeline, enableOfflineDemo]);

  const value = {
    activeTab,
    setActiveTab,
    healthStatus,
    checkHealth,
    financialState,
    setFinancialState,
    pipelineData: pipelineData || MOCK_PIPELINE_DATA,
    loading,
    analyzing,
    seeding,
    error,
    setError,
    clearError: () => setError(null),
    isOfflineMode,
    enableOfflineDemo,
    horizonDays,
    setHorizonDays,
    numSimulations,
    setNumSimulations,
    executePipeline,
    loadFinancialState,
    seedDemoData,
    customScenarioParams,
    setCustomScenarioParams,
    customScenarioResult,
    runCustomWhatIfScenario,
    addInvoice,
    addBill,
  };

  return (
    <FinancialContext.Provider value={value}>
      {children}
    </FinancialContext.Provider>
  );
}

export function useFinancial() {
  const context = useContext(FinancialContext);
  if (!context) {
    throw new Error('useFinancial must be used within a FinancialProvider');
  }
  return context;
}
