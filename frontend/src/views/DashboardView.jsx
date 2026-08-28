import React from 'react';
import {
  Wallet,
  Clock,
  TrendingDown,
  ShieldAlert,
  AlertTriangle,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  ChevronRight,
  Layers,
} from 'lucide-react';
import { useFinancial } from '../context/FinancialContext';
import MetricCard from '../components/common/MetricCard';
import { RiskBadge, LiquidityBadge } from '../components/common/Badge';
import ForecastChart from '../components/forecast/ForecastChart';
import { formatCurrency, formatPercentage } from '../utils/formatters';

export default function DashboardView() {
  const { pipelineData, analyzing, setActiveTab, horizonDays, setHorizonDays, executePipeline } = useFinancial();

  const state = pipelineData?.financial_state || {};
  const forecast = pipelineData?.forecast || {};
  const summary = forecast?.summary || {};
  const scenarios = pipelineData?.scenarios || [];
  const risk = pipelineData?.risk || {};
  const shocks = pipelineData?.shocks || [];
  const currency = state?.currency || 'INR';

  const currentCash = state.current_cash ?? 0;
  const minReserve = state.minimum_cash_reserve ?? 0;
  const runwayDays = summary.runway_days ?? 0;
  const shortfallPct = summary.probability_of_shortfall_pct ?? 0;
  const riskScore = risk.risk_score ?? 0;
  const riskLevel = risk.risk_level ?? 'LOW';

  // Highlight color for risk
  const getRiskHighlight = (score) => {
    if (score >= 70) return 'rose';
    if (score >= 40) return 'amber';
    return 'emerald';
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Executive KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Current Cash Buffer"
          value={formatCurrency(currentCash, currency)}
          subtitle={`Min Reserve: ${formatCurrency(minReserve, currency)}`}
          icon={Wallet}
          highlightColor={currentCash >= minReserve ? 'emerald' : 'rose'}
          badge={
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-semibold font-mono ${
                currentCash >= minReserve ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
              }`}
            >
              {currentCash >= minReserve ? 'HEALTHY' : 'BUFFER BREACH'}
            </span>
          }
        />

        <MetricCard
          title="Projected Cash Runway"
          value={`${runwayDays} Days`}
          subtitle="Until cash breaches minimum reserve"
          icon={Clock}
          highlightColor={runwayDays > 30 ? 'emerald' : runwayDays > 14 ? 'amber' : 'rose'}
          trend={runwayDays <= 30 ? '⚠️ High Burn' : 'Stable'}
          trendPositive={runwayDays > 30}
        />

        <MetricCard
          title="Shortfall Risk Probability"
          value={formatPercentage(shortfallPct / 100, 1)}
          subtitle={`Monte Carlo (90% Conf.)`}
          icon={TrendingDown}
          highlightColor={shortfallPct < 15 ? 'emerald' : shortfallPct < 35 ? 'amber' : 'rose'}
          trend={shortfallPct < 20 ? 'Controlled' : 'Elevated Risk'}
          trendPositive={shortfallPct < 20}
        />

        <MetricCard
          title="Overall Resilience Score"
          value={`${riskScore} / 100`}
          subtitle={`Status: ${riskLevel}`}
          icon={ShieldAlert}
          highlightColor={getRiskHighlight(riskScore)}
          badge={<RiskBadge level={riskLevel} />}
        />
      </div>

      {/* Active Financial Shock Alerts (If any) */}
      {shocks.length > 0 && (
        <div className="glass-panel rounded-xl p-4 border border-amber-500/30 bg-amber-950/20">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-amber-300 font-bold text-xs uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Active Shock Detector Warnings ({shocks.length})</span>
            </div>
            <button
              onClick={() => setActiveTab('risk')}
              className="text-xs text-amber-300 hover:text-amber-100 flex items-center gap-1 font-semibold"
            >
              View In Risk Engine <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {shocks.map((shock, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-navy-950/80 border border-slate-800 text-xs flex items-start gap-3"
              >
                <span className="w-2 h-2 rounded-full bg-amber-400 mt-1 shrink-0 animate-ping" />
                <div>
                  <div className="flex items-center gap-2">
                    <strong className="text-slate-200 font-semibold">{shock.type?.replace(/_/g, ' ')}</strong>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 font-mono">
                      {shock.severity}
                    </span>
                  </div>
                  <p className="text-slate-400 mt-1">{shock.description}</p>
                  <p className="text-emerald-400 mt-1.5 text-[11px] font-mono">
                    ↳ Action: {shock.recommended_action}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Forecast Chart Component */}
      <ForecastChart
        projections={forecast?.projections || []}
        minimumReserve={minReserve}
        currency={currency}
        horizonDays={horizonDays}
        onHorizonChange={(h) => {
          setHorizonDays(h);
          executePipeline({ horizon_days: h });
        }}
        isAnalyzing={analyzing}
      />

      {/* Grid: Stress Scenarios Preview & Risk Drivers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Stress Scenarios Overview */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-5 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Stress Testing & Scenario Resilience
                </h3>
              </div>
              <button
                onClick={() => setActiveTab('scenarios')}
                className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1"
              >
                Explore Lab <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                    <th className="pb-2.5 font-medium">Scenario</th>
                    <th className="pb-2.5 font-medium">Min Cash</th>
                    <th className="pb-2.5 font-medium">Impact</th>
                    <th className="pb-2.5 font-medium">Liquidity</th>
                    <th className="pb-2.5 font-medium">Runway</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {scenarios.slice(0, 4).map((s) => (
                    <tr key={s.scenario_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 font-semibold text-slate-200">
                        {s.name}
                        <span className="block text-[10px] text-slate-500 font-normal font-sans">
                          {s.category}
                        </span>
                      </td>
                      <td className="py-3 font-mono font-bold text-slate-300">
                        {formatCurrency(s.results?.min_cash, currency)}
                      </td>
                      <td className="py-3 font-mono">
                        <span className={s.results?.cash_impact < 0 ? 'text-rose-400' : 'text-slate-400'}>
                          {formatCurrency(s.results?.cash_impact, currency)}
                        </span>
                      </td>
                      <td className="py-3">
                        <LiquidityBadge status={s.results?.liquidity_status} />
                      </td>
                      <td className="py-3 font-mono text-slate-300">
                        {s.results?.runway_days ? `${s.results.runway_days}d` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Evaluated 5 forward stress shocks</span>
            <button
              onClick={() => setActiveTab('scenarios')}
              className="text-emerald-400 hover:text-emerald-300 font-medium"
            >
              Launch Custom What-If Simulator →
            </button>
          </div>
        </div>

        {/* Right 1 Col: Top Risk Drivers & AI Survival Strategy */}
        <div className="glass-panel rounded-xl p-5 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Key Risk Drivers
                </h3>
              </div>
              <RiskBadge level={riskLevel} />
            </div>

            <div className="space-y-3">
              {risk.explanations && risk.explanations.length > 0 ? (
                risk.explanations.slice(0, 3).map((exp, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-navy-950/60 border border-slate-800 text-xs text-slate-300 leading-relaxed"
                  >
                    <div className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                      <span>{exp}</span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 py-4 text-center">
                  No risk drivers computed. Run pipeline.
                </p>
              )}
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-slate-800/80">
            <button
              onClick={() => setActiveTab('optimizer')}
              className="w-full py-2.5 px-3 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-500 hover:to-teal-600 text-white text-xs font-bold shadow-lg shadow-emerald-950/50 flex items-center justify-center gap-2 transition-all"
            >
              <Sparkles className="w-4 h-4" />
              <span>View AI Survival Strategy</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
