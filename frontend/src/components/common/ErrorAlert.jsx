import React from 'react';
import { AlertTriangle, RefreshCw, ServerOff, ExternalLink, Play } from 'lucide-react';
import api from '../../services/api';
import { useFinancial } from '../../context/FinancialContext';

export default function ErrorAlert({ error, onRetry }) {
  const { enableOfflineDemo, clearError } = useFinancial();
  if (!error) return null;

  const isNetwork = error.isNetworkError || error.status === 0;
  const baseUrl = api.getBaseUrl();

  return (
    <div className="rounded-xl border border-rose-500/30 bg-rose-950/30 p-5 backdrop-blur-md shadow-xl my-4">
      <div className="flex items-start gap-4">
        <div className="p-2.5 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-400 shrink-0">
          {isNetwork ? <ServerOff className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-rose-300">
              {isNetwork ? 'FastAPI Backend Disconnected' : 'Pipeline Execution Notice'}
            </h4>
            <button
              onClick={clearError}
              className="text-xs text-slate-400 hover:text-slate-200 px-2 py-0.5 rounded hover:bg-slate-800"
            >
              Dismiss
            </button>
          </div>
          <p className="mt-1 text-xs text-rose-200/90 leading-relaxed">
            {error.message || 'An unexpected error occurred while communicating with the backend.'}
          </p>

          {isNetwork && (
            <div className="mt-3 p-3 rounded-lg bg-navy-950/80 border border-slate-800 text-xs font-mono text-slate-300">
              <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
                <span>BACKEND TARGET:</span>
                <span className="text-emerald-400 font-semibold">{baseUrl}</span>
              </div>
              <p className="mt-2 text-slate-400 text-[11px]">
                To run the FastAPI server locally, execute in terminal:
              </p>
              <code className="block mt-1 text-slate-200 bg-slate-900 p-2 rounded border border-slate-700 select-all">
                python -m uvicorn api.main:app --reload --port 8000
              </code>
            </div>
          )}

          {error.detail && Array.isArray(error.detail) && (
            <div className="mt-3 space-y-1">
              <p className="text-xs font-medium text-rose-300">Validation Details:</p>
              {error.detail.map((d, i) => (
                <div key={i} className="text-xs font-mono text-rose-200/70 bg-rose-950/50 px-2.5 py-1 rounded border border-rose-900/50">
                  {d.loc ? d.loc.join(' → ') : ''}: {d.msg}
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-3">
            {onRetry && (
              <button
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retry Connection
              </button>
            )}

            <button
              onClick={enableOfflineDemo}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              Load Interactive Demo Sandbox
            </button>

            <a
              href={`${baseUrl}/docs`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 underline ml-auto"
            >
              API Swagger Docs
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
