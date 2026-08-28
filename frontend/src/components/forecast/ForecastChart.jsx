import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import { formatCurrency, formatCurrencyDetailed, formatDate } from '../../utils/formatters';

export default function ForecastChart({
  projections = [],
  minimumReserve = 2000000,
  currency = 'INR',
  horizonDays = 30,
  onHorizonChange,
  numSimulations = 2000,
  onSimulationsChange,
  isAnalyzing = false,
}) {
  // Transform projections data for Recharts
  const chartData = projections.map((p) => ({
    date: p.date,
    displayDate: formatDate(p.date),
    projected_balance: p.projected_balance,
    lower_bound: p.uncertainty?.lower_bound ?? p.projected_balance,
    upper_bound: p.uncertainty?.upper_bound ?? p.projected_balance,
    range: [
      p.uncertainty?.lower_bound ?? p.projected_balance,
      p.uncertainty?.upper_bound ?? p.projected_balance,
    ],
    scheduled_net: p.scheduled_net,
    receivable_inflow: p.receivable_inflow,
    is_shortfall: p.is_shortfall,
  }));

  const horizons = [14, 30, 45, 60];
  const simOptions = [500, 1000, 2000, 5000];

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;
    const data = payload[0].payload;

    return (
      <div className="glass-panel p-3.5 rounded-xl border border-slate-700 shadow-2xl text-xs space-y-1.5 min-w-[220px]">
        <div className="flex items-center justify-between border-b border-slate-700/60 pb-1.5 font-semibold text-slate-200">
          <span>{data.displayDate}</span>
          {data.is_shortfall && (
            <span className="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/40 text-[10px]">
              SHORTFALL
            </span>
          )}
        </div>
        <div className="flex justify-between text-slate-300">
          <span className="text-slate-400">Projected Balance:</span>
          <span className="font-mono font-bold text-emerald-400">
            {formatCurrencyDetailed(data.projected_balance, currency)}
          </span>
        </div>
        {data.lower_bound !== undefined && (
          <div className="flex justify-between text-slate-400 text-[11px]">
            <span>90% CI Range:</span>
            <span className="font-mono text-slate-300">
              [{formatCurrency(data.lower_bound, currency)} - {formatCurrency(data.upper_bound, currency)}]
            </span>
          </div>
        )}
        <div className="flex justify-between text-slate-400 text-[11px] pt-1 border-t border-slate-800">
          <span>AR Inflows:</span>
          <span className="font-mono text-emerald-300">
            +{formatCurrency(data.receivable_inflow, currency)}
          </span>
        </div>
        <div className="flex justify-between text-slate-400 text-[11px]">
          <span>Scheduled Net:</span>
          <span className={`font-mono ${data.scheduled_net < 0 ? 'text-rose-400' : 'text-slate-300'}`}>
            {formatCurrency(data.scheduled_net, currency)}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="glass-panel rounded-xl p-5 border border-slate-800">
      {/* Header with Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <span>Projected Cash Runway & Uncertainty Envelope</span>
            {isAnalyzing && <span className="text-xs text-emerald-400 animate-pulse font-normal">(Recomputing...)</span>}
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Monte Carlo simulated trajectory with 90% confidence interval band
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3 self-end sm:self-auto">
          {/* Horizon Selector */}
          <div className="flex items-center bg-slate-900/80 p-1 rounded-lg border border-slate-800 text-xs">
            <span className="text-[11px] text-slate-500 px-2 font-mono hidden md:inline">Horizon:</span>
            {horizons.map((h) => (
              <button
                key={h}
                disabled={isAnalyzing}
                onClick={() => onHorizonChange && onHorizonChange(h)}
                className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                  horizonDays === h
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {h}d
              </button>
            ))}
          </div>

          {/* Simulations Selector */}
          {onSimulationsChange && (
            <div className="flex items-center bg-slate-900/80 p-1 rounded-lg border border-slate-800 text-xs">
              <span className="text-[11px] text-slate-500 px-2 font-mono hidden lg:inline">Paths:</span>
              {simOptions.map((s) => (
                <button
                  key={s}
                  disabled={isAnalyzing}
                  onClick={() => onSimulationsChange(s)}
                  className={`px-2 py-1 rounded-md text-[11px] font-mono transition-all ${
                    numSimulations === s
                      ? 'bg-slate-700 text-slate-100 font-bold'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {s >= 1000 ? `${s / 1000}k` : s}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-80 w-full">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <defs>
                <linearGradient id="uncertaintyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              
              <XAxis
                dataKey="displayDate"
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#334155' }}
              />
              
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#334155' }}
                tickFormatter={(val) => formatCurrency(val, currency)}
              />

              <Tooltip content={<CustomTooltip />} />

              {/* Shaded 90% Confidence Interval */}
              <Area
                type="monotone"
                dataKey="upper_bound"
                stroke="transparent"
                fill="url(#uncertaintyGradient)"
                name="90% Upper Bound"
              />
              <Area
                type="monotone"
                dataKey="lower_bound"
                stroke="transparent"
                fill="#0f172a"
                name="90% Lower Bound"
              />

              {/* Min Cash Reserve Reference Line */}
              {minimumReserve > 0 && (
                <ReferenceLine
                  y={minimumReserve}
                  stroke="#f59e0b"
                  strokeDasharray="4 4"
                  label={{
                    value: `Min Reserve (${formatCurrency(minimumReserve, currency)})`,
                    fill: '#f59e0b',
                    fontSize: 10,
                    position: 'insideTopRight',
                  }}
                />
              )}

              {/* Zero Balance Shortfall Reference Line */}
              <ReferenceLine
                y={0}
                stroke="#f43f5e"
                strokeDasharray="3 3"
                label={{
                  value: 'Cash Shortfall (₹0)',
                  fill: '#f43f5e',
                  fontSize: 10,
                  position: 'insideBottomRight',
                }}
              />

              {/* Deterministic Projection Line */}
              <Line
                type="monotone"
                dataKey="projected_balance"
                stroke="#10b981"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5, fill: '#10b981', stroke: '#ffffff', strokeWidth: 2 }}
                name="Projected Balance"
              />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-slate-500 text-xs">
            No forecast projections available. Run pipeline to generate.
          </div>
        )}
      </div>

      {/* Legend & Meta */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 bg-emerald-500 rounded" />
            <span>Point Forecast</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-2 bg-emerald-500/20 border border-emerald-500/40 rounded-sm" />
            <span>90% Confidence Interval</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 border-t border-dashed border-amber-500" />
            <span>Min Reserve Buffer</span>
          </div>
        </div>
        <div className="font-mono text-[11px] text-slate-500">
          Simulations: {numSimulations.toLocaleString()} iterations
        </div>
      </div>
    </div>
  );
}
