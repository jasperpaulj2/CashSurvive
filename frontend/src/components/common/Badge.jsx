import React from 'react';
import { getRiskBadgeColor, getLiquidityStatusBadge } from '../../utils/formatters';

export function RiskBadge({ level }) {
  const { bg, text, border } = getRiskBadgeColor(level);
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${bg} ${text} ${border}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current animate-pulse" />
      {level || 'UNKNOWN'}
    </span>
  );
}

export function LiquidityBadge({ status }) {
  const { bg, text, border } = getLiquidityStatusBadge(status);
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${bg} ${text} ${border}`}>
      {status || 'UNKNOWN'}
    </span>
  );
}

export function StatusBadge({ text, variant = 'neutral' }) {
  const variants = {
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    danger: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    info: 'bg-sky-500/10 text-sky-400 border-sky-500/30',
    neutral: 'bg-slate-700/50 text-slate-300 border-slate-600',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${variants[variant] || variants.neutral}`}>
      {text}
    </span>
  );
}
