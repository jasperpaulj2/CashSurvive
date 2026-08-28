import React from 'react';
import { ShieldAlert, Database, ExternalLink, Sparkles, RefreshCw, Radio } from 'lucide-react';
import { useFinancial } from '../../context/FinancialContext';
import api from '../../services/api';

export default function Navbar() {
  const {
    healthStatus,
    analyzing,
    seeding,
    isOfflineMode,
    seedDemoData,
    executePipeline,
    checkHealth,
  } = useFinancial();

  const baseUrl = api.getBaseUrl();
  const isOnline = healthStatus?.status === 'healthy' && !isOfflineMode;

  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-navy-950/90 backdrop-blur-md px-6 py-3.5 flex items-center justify-between shadow-lg">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-950/50 border border-emerald-400/30">
          <ShieldAlert className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-extrabold tracking-tight text-slate-100 flex items-center gap-1.5">
              CASH <span className="text-emerald-400 font-black">SURVIVE</span>
            </h1>
            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              Control Tower
            </span>
          </div>
          <p className="text-xs text-slate-400">Autonomous Financial Resilience & Stress Testing</p>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Backend Status Indicator */}
        <button
          onClick={async () => {
            await checkHealth();
            await executePipeline();
          }}
          title="Click to re-check API health"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono bg-slate-900/80 border border-slate-800 hover:border-slate-700 text-slate-300 transition-colors"
        >
          <span className="relative flex h-2 w-2">
            {isOnline ? (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </>
            ) : (
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            )}
          </span>
          <span className="hidden sm:inline">
            {isOnline ? 'FastAPI Connected' : 'Offline Demo'}
          </span>
        </button>

        {/* Seed Demo Button */}
        <button
          onClick={seedDemoData}
          disabled={seeding || analyzing}
          title="Reset and populate database with Aarav Textiles Pvt Ltd demo records"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all disabled:opacity-50"
        >
          <Database className={`w-3.5 h-3.5 ${seeding ? 'animate-spin text-emerald-400' : 'text-slate-400'}`} />
          <span>{seeding ? 'Seeding...' : 'Seed Demo Data'}</span>
        </button>

        {/* Analyze Health / Re-run Pipeline */}
        <button
          onClick={() => executePipeline()}
          disabled={analyzing || seeding}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-950/50 transition-all disabled:opacity-50 glow-emerald"
        >
          <Sparkles className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
          <span>{analyzing ? 'Analyzing...' : 'Run Pipeline'}</span>
        </button>

        {/* API Docs Link */}
        <a
          href={`${baseUrl}/docs`}
          target="_blank"
          rel="noreferrer"
          title="Open FastAPI Swagger Documentation"
          className="hidden md:inline-flex items-center gap-1 px-2.5 py-1.5 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 rounded-lg transition-colors"
        >
          <span>Docs</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </header>
  );
}
