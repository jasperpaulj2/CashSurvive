import React from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Activity,
  Layers,
  ArrowRight,
  Sparkles,
  Info,
} from 'lucide-react';
import { useFinancial } from '../context/FinancialContext';
import MetricCard from '../components/common/MetricCard';
import { RiskBadge, StatusBadge } from '../components/common/Badge';

export default function RiskView() {
  const { pipelineData } = useFinancial();

  const risk = pipelineData?.risk || {};
  const factors = risk.factors || {};
  const explanations = risk.explanations || [];
  const recommendations = risk.actionable_recommendations || [];
  const shocks = pipelineData?.shocks || [];

  const riskScore = risk.risk_score ?? 40;
  const riskLevel = risk.risk_level ?? 'MEDIUM';

  const factorItems = [
    {
      key: 'liquidity_risk',
      name: 'Liquidity & Cash Reserve Risk',
      score: factors.liquidity_risk ?? 42,
      desc: 'Risk of cash dropping below minimum statutory operating threshold',
    },
    {
      key: 'runway_risk',
      name: 'Runway & Burn Velocity Risk',
      score: factors.runway_risk ?? 36,
      desc: 'Cash drain acceleration based on fixed operational burn',
    },
    {
      key: 'receivable_delay_risk',
      name: 'Receivable Delay & Concentration Risk',
      score: factors.receivable_delay_risk ?? 58,
      desc: 'Exposure to key client payment delays and overdue aging drag',
    },
    {
      key: 'supplier_pressure_risk',
      name: 'Supplier & Payable Pressure Risk',
      score: factors.supplier_pressure_risk ?? 38,
      desc: 'Immediate critical supplier bill commitments and payment terms',
    },
    {
      key: 'financing_risk',
      name: 'Financing & Debt Obligation Risk',
      score: factors.financing_risk ?? 45,
      desc: 'Credit line utilization headroom and debt service obligations',
    },
  ];

  const getBarColor = (score) => {
    if (score >= 70) return 'from-rose-600 to-rose-400';
    if (score >= 40) return 'from-amber-500 to-amber-400';
    return 'from-emerald-500 to-teal-400';
  };

  const getPriorityVariant = (priority) => {
    switch (priority?.toUpperCase()) {
      case 'CRITICAL':
        return 'danger';
      case 'HIGH':
        return 'warning';
      case 'MEDIUM':
        return 'info';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Banner with Risk Score Gauge */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 bg-gradient-to-br from-navy-950 via-slate-900 to-navy-950 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-slate-100">
              Deterministic Financial Risk Intelligence
            </h3>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-mono">
              Member 3 Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-xl leading-relaxed">
            Multi-dimensional risk evaluation combining working capital liquidity, customer receivable default likelihood, fixed cost burn velocity, and financing buffer headroom.
          </p>
        </div>

        {/* Circular Score Display */}
        <div className="flex items-center gap-4 bg-slate-900/90 p-4 rounded-xl border border-slate-800 shadow-xl">
          <div className="text-center">
            <span className="text-3xl font-extrabold font-mono text-slate-100 block">
              {riskScore} <span className="text-sm font-normal text-slate-500">/ 100</span>
            </span>
            <span className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">
              Risk Index
            </span>
          </div>
          <div className="h-10 w-px bg-slate-800" />
          <div className="space-y-1">
            <RiskBadge level={riskLevel} />
            <span className="text-[11px] text-slate-400 block font-mono">
              Deterministic
            </span>
          </div>
        </div>
      </div>

      {/* Grid: 5-Factor Breakdown & Risk Explanations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: 5-Factor Risk Breakdown */}
        <div className="glass-panel rounded-xl p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              5-Factor Risk Decomposition
            </h4>
            <span className="text-xs font-mono text-slate-500">Normalized 0-100</span>
          </div>

          <div className="space-y-4 pt-1">
            {factorItems.map((factor) => (
              <div key={factor.key} className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-200">{factor.name}</span>
                  <span className="font-mono font-bold text-slate-300">
                    {factor.score}/100
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full bg-gradient-to-r ${getBarColor(factor.score)} rounded-full transition-all duration-500`}
                    style={{ width: `${Math.min(100, factor.score)}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-500">{factor.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Explainable Risk Drivers */}
        <div className="glass-panel rounded-xl p-6 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Explainable Risk Rationales & Drivers
              </h4>
              <Info className="w-4 h-4 text-slate-500" />
            </div>

            <div className="space-y-3">
              {explanations.map((exp, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-lg bg-navy-950/70 border border-slate-800/90 text-xs text-slate-300 leading-relaxed flex items-start gap-3"
                >
                  <span className="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <span>{exp}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 font-mono">
            Evaluated deterministically based on balance sheet & cash flow timeline.
          </div>
        </div>
      </div>

      {/* Actionable Recommendations Playbook */}
      <div className="glass-panel rounded-xl p-6 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Prioritized Mitigation & Survival Playbook
            </h4>
          </div>
          <span className="text-xs text-slate-500 font-mono">{recommendations.length} Action Items</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {recommendations.map((rec, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-navy-950/80 border border-slate-800 space-y-2.5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <StatusBadge text={rec.priority} variant={getPriorityVariant(rec.priority)} />
                  <span className="text-[10px] font-mono text-slate-500 uppercase">{rec.category}</span>
                </div>
                <h5 className="font-bold text-slate-200 text-sm">{rec.title}</h5>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{rec.description}</p>
              </div>

              <div className="pt-2 border-t border-slate-800/80 text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                <span>Actionable mitigation</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Shock Detector Log */}
      {shocks.length > 0 && (
        <div className="glass-panel rounded-xl p-6 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Financial Shock Detector Anomaly History
            </h4>
          </div>

          <div className="space-y-2">
            {shocks.map((s, i) => (
              <div key={i} className="p-3 rounded-lg bg-navy-950/60 border border-slate-800 text-xs flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-200 font-mono mr-2">{s.type}</span>
                  <span className="text-slate-400">{s.description}</span>
                </div>
                <span className="text-amber-400 font-mono text-[11px] bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
                  {s.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
