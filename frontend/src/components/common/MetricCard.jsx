import React from 'react';

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendPositive,
  highlightColor = 'emerald',
  badge,
}) {
  const getGlow = () => {
    if (highlightColor === 'rose') return 'border-rose-500/30 hover:border-rose-500/50';
    if (highlightColor === 'amber') return 'border-amber-500/30 hover:border-amber-500/50';
    if (highlightColor === 'indigo') return 'border-indigo-500/30 hover:border-indigo-500/50';
    return 'border-emerald-500/30 hover:border-emerald-500/50';
  };

  const getIconColor = () => {
    if (highlightColor === 'rose') return 'text-rose-400 bg-rose-500/10';
    if (highlightColor === 'amber') return 'text-amber-400 bg-amber-500/10';
    if (highlightColor === 'indigo') return 'text-indigo-400 bg-indigo-500/10';
    return 'text-emerald-400 bg-emerald-500/10';
  };

  return (
    <div className={`glass-panel rounded-xl p-5 transition-all duration-200 border ${getGlow()}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
          <h3 className="mt-2 text-2xl font-bold text-slate-100 tracking-tight">{value}</h3>
        </div>
        {Icon && (
          <div className={`p-2.5 rounded-lg border border-slate-700/50 ${getIconColor()}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {(subtitle || trend || badge) && (
        <div className="mt-3 flex items-center justify-between text-xs text-slate-400 border-t border-slate-700/30 pt-2.5">
          <span className="truncate">{subtitle}</span>
          {badge}
          {trend && (
            <span className={`font-medium ${trendPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
              {trend}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
