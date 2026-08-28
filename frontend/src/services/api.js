/**
 * api.js
 * ======
 * Centralized API service for communicating with the CashSurvive FastAPI backend.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 35000, // 35s timeout for Monte Carlo runs
});

// Response interceptor for consistent error extraction
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    let errorMessage = 'An unexpected network error occurred.';
    let errorDetail = null;
    let statusCode = 0;

    if (error.response) {
      statusCode = error.response.status;
      const data = error.response.data;
      if (data) {
        errorMessage = data.message || data.detail || `Server error (${statusCode})`;
        errorDetail = data.detail || null;
      }
    } else if (error.request) {
      errorMessage = `Cannot reach backend at ${API_BASE_URL}. Ensure FastAPI is running.`;
    } else {
      errorMessage = error.message;
    }

    const enhancedError = new Error(errorMessage);
    enhancedError.status = statusCode;
    enhancedError.detail = errorDetail;
    enhancedError.isNetworkError = !error.response;
    return Promise.reject(enhancedError);
  }
);

export const api = {
  // System Health
  getHealth: () => client.get('/health'),

  // Financial State (Member 1)
  getFinancialState: (asOf = null) => {
    const params = asOf ? { as_of: asOf } : {};
    return client.get('/api/financial-state', { params });
  },

  seedFinancialState: () => client.post('/api/financial-state/seed'),

  // Forecasting Engine (Member 2)
  getForecast: ({ horizon_days = 30, num_simulations = 2000, confidence_level = 0.9, as_of = null, financial_state = null } = {}) => {
    return client.post('/api/forecast', {
      horizon_days,
      num_simulations,
      confidence_level,
      as_of,
      financial_state,
    });
  },

  // Scenario Engine (Member 3)
  runScenarios: ({ as_of = null, financial_state = null } = {}) => {
    return client.post('/api/scenarios', {
      as_of,
      financial_state,
    });
  },

  // Risk Engine (Member 3)
  getRisk: ({ as_of = null, financial_state = null } = {}) => {
    return client.post('/api/risk', {
      as_of,
      financial_state,
    });
  },

  // Unified Pipeline (All Modules)
  runPipeline: ({ horizon_days = 30, num_simulations = 2000, confidence_level = 0.9, as_of = null, financial_state = null, previous_state = null } = {}) => {
    return client.post('/api/pipeline/run', {
      horizon_days,
      num_simulations,
      confidence_level,
      as_of,
      financial_state,
      previous_state,
    });
  },

  getBaseUrl: () => API_BASE_URL,
};

export default api;
