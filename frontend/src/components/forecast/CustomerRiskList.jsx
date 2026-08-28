import React from 'react';
import { UserCheck, AlertTriangle } from 'lucide-react';
import { formatPercentage } from '../../utils/formatters';

export default function CustomerRiskList({ customerProfiles = [], highRiskCustomers = [] }) {
  const highRiskIds = new Set(highRiskCustomers.map((c) => c.customer_id));

  return (
    <div className="glass-panel rounded-xl p-5 border border-slate-800">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Customer Payment Behavior Profiles
          </h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Derived historical payment velocity and reliability scoring
          </p>
        </div>
        {highRiskCustomers.length > 0 && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/40 text-[10px] font-semibold">
            <AlertTriangle className="w-3 h-3" />
            {highRiskCustomers.length} High Risk
          </span>
        )}
      </div>

      {customerProfiles.length > 0 ? (
        <div className="space-y-3">
          {customerProfiles.map((p) => {
            const isHigh = highRiskIds.has(p.customer_id) || p.risk_score >= 40;
            return (
              <div
                key={p.customer_id}
                className={`p-3 rounded-lg border transition-all text-xs ${
                  isHigh
                    ? 'bg-rose-950/20 border-rose-500/30 text-slate-200'
                    : 'bg-slate-900/50 border-slate-800 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <UserCheck className={`w-3.5 h-3.5 ${isHigh ? 'text-rose-400' : 'text-emerald-400'}`} />
                    <span className="font-semibold text-slate-100">{p.customer_id}</span>
                  </div>
                  <span
                    className={`font-mono text-xs font-bold px-2 py-0.5 rounded ${
                      isHigh
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    }`}
                  >
                    Risk: {p.risk_score}/100
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-[11px] text-slate-400 font-mono pt-1.5 border-t border-slate-800/60">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Avg Days to Pay:</span>
                    <span className="text-slate-200">{p.avg_days_to_pay}d (±{p.std_days_to_pay}d)</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">On-Time Rate:</span>
                    <span className={p.on_time_rate >= 0.8 ? 'text-emerald-400' : 'text-amber-400'}>
                      {formatPercentage(p.on_time_rate)}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Paid Invoices:</span>
                    <span className="text-slate-300">{p.num_paid_invoices} records</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-xs text-slate-500 py-6 text-center">
          No customer profiles built yet. Run pipeline to profile receivables.
        </p>
      )}
    </div>
  );
}
