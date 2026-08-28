import React, { useState } from 'react';
import {
  Sparkles,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  Sliders,
  DollarSign,
  TrendingUp,
  Cpu,
} from 'lucide-react';
import { useFinancial } from '../context/FinancialContext';
import MetricCard from '../components/common/MetricCard';
import { formatCurrency } from '../utils/formatters';

export default function OptimizerView() {
  const { pipelineData } = useFinancial();

  const state = pipelineData?.financial_state || {};
  const optimizer = pipelineData?.optimization_extension || {};
  const currency = state?.currency || 'INR';

  const defaultSteps = [
    {
      id: 1,
      step: 1,
      action: 'Negotiate 14-day deferral with Apex Logistics & Freight',
      category: 'PAYABLE_DEFERRAL',
      cash_unlocked: 185000,
      risk: 'LOW',
      impact: 'Avoids Day 9 cash dip with zero supply disruption',
      completed: false,
    },
    {
      id: 2,
      step: 2,
      action: 'Split Gujarat Cotton Yarn Mill invoice into 2 installments',
      category: 'VENDOR_NEGOTIATION',
      cash_unlocked: 460000,
      risk: 'MEDIUM',
      impact: 'Preserves ₹4.60 L buffer ahead of Sep 10 loan EMI',
      completed: false,
    },
    {
      id: 3,
      step: 3,
      action: 'Discount Raymond Apparel invoice (₹11.0 L) via HDFC factoring line',
      category: 'INVOICE_FACTORING',
      cash_unlocked: 1045000,
      risk: 'LOW',
      impact: 'Provides immediate 95% liquidity at 10.5% annualized discount',
      completed: false,
    },
    {
      id: 4,
      step: 4,
      action: 'Freeze non-essential IT software upgrades & discretionary travel',
      category: 'DISCRETIONARY_FREEZE',
      cash_unlocked: 35000,
      risk: 'MINIMAL',
      impact: 'Reduces monthly recurring overheads',
      completed: false,
    },
  ];

  const [steps, setSteps] = useState(defaultSteps);

  const toggleStep = (id) => {
    setSteps((prev) =>
      prev.map((s) => (s.id === id ? { ...s, completed: !s.completed } : s))
    );
  };

  const completedCash = steps
    .filter((s) => s.completed)
    .reduce((acc, s) => acc + s.cash_unlocked, 0);

  const totalPotential = steps.reduce((acc, s) => acc + s.cash_unlocked, 0);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="glass-panel rounded-2xl p-6 border border-emerald-500/30 bg-gradient-to-br from-navy-950 via-slate-900 to-navy-950 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-100">
              Autonomous Liquidity Optimization Engine
            </h3>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-mono">
              Member 4 Hook
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-xl leading-relaxed">
            AI-driven dynamic sequencing of payable deferrals, invoice discounting, and discretionary freezes designed to bridge cash shortfalls without damaging vendor relationships.
          </p>
        </div>

        <div className="bg-slate-900/90 p-4 rounded-xl border border-slate-800 text-center min-w-[200px]">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-mono block mb-1">
            Total Unlocked Buffer
          </span>
          <span className="text-2xl font-extrabold font-mono text-emerald-400">
            {formatCurrency(totalPotential, currency)}
          </span>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Potential Liquidity Unlocked"
          value={formatCurrency(totalPotential, currency)}
          subtitle="From 4 strategic survival actions"
          icon={TrendingUp}
          highlightColor="emerald"
        />

        <MetricCard
          title="Simulated Cash Unlocked"
          value={formatCurrency(completedCash, currency)}
          subtitle={`${steps.filter(s => s.completed).length} of ${steps.length} Actions Activated`}
          icon={DollarSign}
          highlightColor={completedCash > 0 ? 'emerald' : 'indigo'}
        />

        <MetricCard
          title="Optimizer Status"
          value="Engine Synchronized"
          subtitle="Extension hook connected & ready"
          icon={Cpu}
          highlightColor="emerald"
          badge={
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-mono">
              ONLINE
            </span>
          }
        />
      </div>

      {/* Interactive Optimization Roadmap */}
      <div className="glass-panel rounded-xl p-6 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Interactive Liquidity Preservation Roadmap
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Click checkboxes to simulate immediate execution and track preserved working capital
            </p>
          </div>

          <span className="text-xs font-mono text-emerald-400">
            Simulated Buffer Added: {formatCurrency(completedCash, currency)}
          </span>
        </div>

        <div className="space-y-3">
          {steps.map((step) => (
            <div
              key={step.id}
              onClick={() => toggleStep(step.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all flex items-start justify-between gap-4 ${
                step.completed
                  ? 'bg-emerald-950/20 border-emerald-500/40 shadow-md'
                  : 'bg-navy-950/50 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start gap-3.5">
                <input
                  type="checkbox"
                  checked={step.completed}
                  onChange={() => {}}
                  className="mt-1 w-4 h-4 rounded text-emerald-500 bg-slate-900 border-slate-700 focus:ring-0 cursor-pointer"
                />
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      STEP {step.step}
                    </span>
                    <span className="text-[10px] font-mono uppercase text-slate-500">
                      {step.category}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                        step.risk === 'LOW' || step.risk === 'MINIMAL'
                          ? 'bg-emerald-500/10 text-emerald-400'
                          : 'bg-amber-500/10 text-amber-400'
                      }`}
                    >
                      {step.risk} RISK
                    </span>
                  </div>

                  <h5 className="font-bold text-slate-100 text-sm">{step.action}</h5>
                  <p className="text-xs text-slate-400 mt-1">{step.impact}</p>
                </div>
              </div>

              <div className="text-right shrink-0">
                <span className="text-base font-bold font-mono text-emerald-400 block">
                  +{formatCurrency(step.cash_unlocked, currency)}
                </span>
                <span className="text-[10px] text-slate-500 uppercase font-mono">
                  {step.completed ? 'ACTIVATED' : 'AVAILABLE'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
