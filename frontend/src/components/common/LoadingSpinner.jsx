import React from 'react';
import { Loader2, Sparkles } from 'lucide-react';

export default function LoadingSpinner({ message = 'Analyzing financial control tower data...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-2 border-slate-700/50 border-t-emerald-500 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center text-emerald-400">
          <Sparkles className="w-6 h-6 animate-pulse" />
        </div>
      </div>
      <p className="mt-5 text-sm font-medium text-slate-300 tracking-wide animate-pulse">
        {message}
      </p>
      <p className="mt-1 text-xs text-slate-500">
        Running Monte Carlo simulations & stress scenarios...
      </p>
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="glass-panel rounded-xl p-5 border border-slate-700/40 animate-pulse">
      <div className="h-3.5 bg-slate-700/50 rounded w-1/3 mb-3" />
      <div className="h-7 bg-slate-700/70 rounded w-2/3 mb-4" />
      <div className="h-3 bg-slate-700/30 rounded w-full" />
    </div>
  );
}
