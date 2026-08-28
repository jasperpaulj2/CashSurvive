import React from 'react';
import { WifiOff, RefreshCw, Zap } from 'lucide-react';
import { useFinancial } from '../../context/FinancialContext';

export default function OfflineBanner() {
  const { isOfflineMode, analyzing, checkHealth, executePipeline } = useFinancial();

  if (!isOfflineMode) return null;

  return (
    <div className="bg-gradient-to-r from-amber-950/70 via-slate-900 to-amber-950/70 border-b border-amber-500/30 px-4 py-2.5 text-xs text-amber-200 flex flex-wrap items-center justify-between gap-3 shadow-md">
      <div className="flex items-center gap-2">
        <span className="p-1 rounded bg-amber-500/20 text-amber-400">
          <WifiOff className="w-3.5 h-3.5" />
        </span>
        <span>
          <strong className="font-semibold text-amber-300">Offline Demo Mode Active:</strong> Operating with realistic simulation data for <em>Aarav Textiles Pvt Ltd</em>.
        </span>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={async () => {
            await checkHealth();
            await executePipeline();
          }}
          disabled={analyzing}
          className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-md bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 ${analyzing ? 'animate-spin' : ''}`} />
          <span>{analyzing ? 'Checking...' : 'Connect to Live FastAPI'}</span>
        </button>
      </div>
    </div>
  );
}
