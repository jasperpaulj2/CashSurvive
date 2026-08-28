import React, { useState, useEffect } from 'react';
import {
  Zap,
  Sliders,
  AlertTriangle,
  Flame,
  Shield,
  Clock,
  ArrowRight,
  Sparkles,
  TrendingDown,
  RefreshCw,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
  Legend,
} from 'recharts';
import { useFinancial } from '../context/FinancialContext';
import MetricCard from '../components/common/MetricCard';
import { RiskBadge, LiquidityBadge } from '../components/common/Badge';
import { formatCurrency, formatCurrencyDetailed, formatDate } from '../utils/formatters';

export default function ScenariosView() {
  const {
    pipelineData,
    customScenarioParams,
    setCustomScenarioParams,
    customScenarioResult,
    runCustomWhatIfScenario,
  } = useFinancial();

  const [selectedScenarioId, setSelectedScenarioId] = useState('baseline');

  const state = pipelineData?.financial_state || {};
  const scenarios = pipelineData?.scenarios || [];
  const currency = state?.currency || 'INR';
  const minReserve = state?.minimum_cash_reserve || 1500000;

  // Run custom simulation on mount and when params change
  useEffect(() => {
    runCustomWhatIfScenario(customScenarioParams);
  }, [customScenarioParams, runCustomWhatIfScenario]);

  const handleSliderChange = (field, value) => {
    setCustomScenarioParams((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const selectedScenario = scenarios.find((s) => s.scenario_id === selectedScenarioId) || scenarios[0];

  // Prepare comparison chart data (Baseline vs Custom Simulated)
  const baseProjections = pipelineData?.forecast?.projections || [];
  const simProjections = customScenarioResult?.projections || [];

  const comparisonChartData = baseProjections.map((p, idx) => {
    const simP = simProjections[idx];
    return {
      date: p.date,
      displayDate: formatDate(p.date),
      baseline: p.projected_balance,
      simulated: simP ? simP.simulated_balance : p.projected_balance,
    };
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Header Banner */}
      <div className="glass-panel rounded-xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-slate-100">
              Stress Testing & Scenario Simulation Engine
            </h3>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-mono">
              Member 3 Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Simulate liquidity shocks, delayed receivable velocity, vendor squeezes, and financing constraints
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 font-mono bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <span>Minimum Reserve Buffer:</span>
          <strong className="text-amber-400 font-bold">{formatCurrency(minReserve, currency)}</strong>
        </div>
      </div>

      {/* Interactive Custom What-If Simulator */}
      <div className="glass-panel rounded-2xl p-6 border border-emerald-500/30 bg-gradient-to-br from-navy-950 via-slate-900 to-navy-950 shadow-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4 mb-6">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/20 border border-emerald-500/30 text-emerald-400">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                Interactive "What-If" Stress Lab
              </h4>
              <p className="text-xs text-slate-400">
                Adjust shock variables to evaluate live survival impact & liquidity breach timeline
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              setCustomScenarioParams({
                delayDays: 14,
                defaultPct: 15,
                costSpikePct: 10,
                creditFreeze: false,
              });
            }}
            className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Defaults</span>
          </button>
        </div>

        {/* Sliders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          {/* Slider 1: AR Delay Days */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-slate-300">Receivable Delay</span>
              <span className="font-mono text-emerald-400 font-bold">
                +{customScenarioParams.delayDays} Days
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="45"
              step="1"
              value={customScenarioParams.delayDays}
              onChange={(e) => handleSliderChange('delayDays', Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
            <p className="text-[11px] text-slate-500">Delay customer invoice cash collections</p>
          </div>

          {/* Slider 2: Default Rate */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-slate-300">Default / Bad Debt Rate</span>
              <span className="font-mono text-amber-400 font-bold">
                {customScenarioParams.defaultPct}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="5"
              value={customScenarioParams.defaultPct}
              onChange={(e) => handleSliderChange('defaultPct', Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
            <p className="text-[11px] text-slate-500">% of uncollectible customer revenue</p>
          </div>

          {/* Slider 3: Operating Cost Spike */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-slate-300">Expense / Inflation Spike</span>
              <span className="font-mono text-rose-400 font-bold">
                +{customScenarioParams.costSpikePct}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="40"
              step="5"
              value={customScenarioParams.costSpikePct}
              onChange={(e) => handleSliderChange('costSpikePct', Number(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-rose-500"
            />
            <p className="text-[11px] text-slate-500">Raw material price & operational inflation</p>
          </div>

          {/* Toggle 4: Credit Line Freeze */}
          <div className="space-y-2 flex flex-col justify-between">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-slate-300">Credit Facility Freeze</span>
              <span className={`font-mono font-bold ${customScenarioParams.creditFreeze ? 'text-rose-400' : 'text-slate-400'}`}>
                {customScenarioParams.creditFreeze ? 'FROZEN' : 'ACTIVE'}
              </span>
            </div>
            <label className="flex items-center gap-3 p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 cursor-pointer">
              <input
                type="checkbox"
                checked={customScenarioParams.creditFreeze}
                onChange={(e) => handleSliderChange('creditFreeze', e.target.checked)}
                className="w-4 h-4 rounded text-rose-500 bg-slate-950 border-slate-700"
              />
              <span className="text-xs text-slate-300">Bank limits revolver access</span>
            </label>
            <p className="text-[11px] text-slate-500">Blocks ₹30 Lakhs emergency buffer</p>
          </div>
        </div>

        {/* Live Simulation Outcomes */}
        {customScenarioResult && (
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-navy-950/60 border border-slate-800/80">
                <span className="text-slate-400 text-[11px] block">Simulated Min Cash</span>
                <span className={`text-base font-bold font-mono ${customScenarioResult.min_cash < minReserve ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {formatCurrency(customScenarioResult.min_cash, currency)}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-navy-950/60 border border-slate-800/80">
                <span className="text-slate-400 text-[11px] block">Net Cash Impact</span>
                <span className="text-base font-bold font-mono text-rose-400">
                  {formatCurrency(customScenarioResult.cash_impact, currency)}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-navy-950/60 border border-slate-800/80">
                <span className="text-slate-400 text-[11px] block">Liquidity Status</span>
                <div className="mt-1">
                  <LiquidityBadge status={customScenarioResult.liquidity_status} />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-navy-950/60 border border-slate-800/80">
                <span className="text-slate-400 text-[11px] block">Stress Risk Score</span>
                <div className="mt-1 flex items-center gap-2">
                  <span className="font-bold text-slate-200 font-mono text-sm">
                    {customScenarioResult.risk_score}/100
                  </span>
                  <RiskBadge level={customScenarioResult.risk_level} />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-navy-950/60 border border-slate-800/80">
                <span className="text-slate-400 text-[11px] block">Reserve Breach Day</span>
                <span className="text-base font-bold font-mono text-amber-400">
                  {customScenarioResult.breach_day ? `Day ${customScenarioResult.breach_day}` : 'No Breach'}
                </span>
              </div>
            </div>

            {/* Comparison Chart: Baseline vs Simulated Stress Trajectory */}
            <div className="h-64 w-full pt-2">
              <p className="text-[11px] font-mono text-slate-400 mb-2">
                Trajectory Comparison: Baseline vs Custom Shock Path
              </p>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={comparisonChartData} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="displayDate" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis
                    stroke="#64748b"
                    tick={{ fontSize: 10 }}
                    tickFormatter={(val) => formatCurrency(val, currency)}
                  />
                  <Tooltip
                    formatter={(val) => [formatCurrencyDetailed(val, currency)]}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <ReferenceLine
                    y={minReserve}
                    stroke="#f59e0b"
                    strokeDasharray="4 4"
                    label={{ value: 'Min Reserve', fill: '#f59e0b', fontSize: 10, position: 'insideTopRight' }}
                  />
                  <ReferenceLine y={0} stroke="#f43f5e" strokeDasharray="3 3" />
                  <Line
                    type="monotone"
                    dataKey="baseline"
                    name="Baseline Projection"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="simulated"
                    name="Simulated Shock Trajectory"
                    stroke="#f43f5e"
                    strokeWidth={2.5}
                    strokeDasharray="4 2"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Pre-configured Stress Scenarios Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Standard Financial Stress Scenarios
          </h4>
          <span className="text-xs font-mono text-slate-500">
            Select a scenario to inspect recommendations
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {scenarios.map((s) => {
            const isSelected = selectedScenarioId === s.scenario_id;
            return (
              <div
                key={s.scenario_id}
                onClick={() => setSelectedScenarioId(s.scenario_id)}
                className={`glass-panel rounded-xl p-5 border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-emerald-500/50 bg-slate-900/90 shadow-lg glow-emerald'
                    : 'border-slate-800 hover:border-slate-700 bg-navy-950/40'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <h5 className="font-bold text-slate-100 text-sm">{s.name}</h5>
                  <RiskBadge level={s.results?.risk_level} />
                </div>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">{s.description}</p>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-3 border-t border-slate-800/80">
                  <div>
                    <span className="text-slate-500 text-[10px] block">Min Balance:</span>
                    <span className="text-slate-200 font-semibold">
                      {formatCurrency(s.results?.min_cash, currency)}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block">Cash Impact:</span>
                    <span className={s.results?.cash_impact < 0 ? 'text-rose-400 font-semibold' : 'text-slate-300'}>
                      {formatCurrency(s.results?.cash_impact, currency)}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block">Liquidity:</span>
                    <LiquidityBadge status={s.results?.liquidity_status} />
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block">Runway:</span>
                    <span className="text-slate-200">{s.results?.runway_days} days</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Scenario Actionable Recommendations */}
      {selectedScenario && (
        <div className="glass-panel rounded-xl p-5 border border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Preservation Playbook for {selectedScenario.name}
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {selectedScenario.recommendations && selectedScenario.recommendations.map((rec, i) => (
              <div
                key={i}
                className="p-3.5 rounded-lg bg-navy-950/70 border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5"
              >
                <span className="w-5 h-5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono font-bold flex items-center justify-center shrink-0 text-[10px]">
                  {i + 1}
                </span>
                <span className="leading-relaxed">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
