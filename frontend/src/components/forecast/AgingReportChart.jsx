import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { formatCurrency, formatCurrencyDetailed } from '../../utils/formatters';

export default function AgingReportChart({ aging = {}, dso = 0, currency = 'INR' }) {
  const agingData = [
    { bucket: 'Current', amount: aging['current'] || 0, color: '#10b981' },
    { bucket: '1-30 Days', amount: aging['1-30'] || 0, color: '#f59e0b' },
    { bucket: '31-60 Days', amount: aging['31-60'] || 0, color: '#f97316' },
    { bucket: '61-90 Days', amount: aging['61-90'] || 0, color: '#ef4444' },
    { bucket: '90+ Days', amount: aging['90+'] || 0, color: '#b91c1c' },
  ];

  const totalOutstanding = agingData.reduce((acc, item) => acc + item.amount, 0);

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    const data = payload[0].payload;
    const pct = totalOutstanding > 0 ? (data.amount / totalOutstanding) * 100 : 0;

    return (
      <div className="glass-panel p-3 rounded-lg border border-slate-700 shadow-xl text-xs space-y-1">
        <p className="font-semibold text-slate-200">{data.bucket} Overdue</p>
        <p className="font-mono text-emerald-400 font-bold">
          {formatCurrencyDetailed(data.amount, currency)}
        </p>
        <p className="text-[11px] text-slate-400">
          {pct.toFixed(1)}% of total receivables
        </p>
      </div>
    );
  };

  return (
    <div className="glass-panel rounded-xl p-5 border border-slate-800 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Accounts Receivable Aging Distribution
          </h4>
          <span className="text-xs font-mono bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
            DSO: <strong className="text-emerald-400">{dso} days</strong>
          </span>
        </div>
        <p className="text-xs text-slate-400 mb-4">
          Breakdown of outstanding invoices by delay bucket
        </p>

        {/* Bar Chart */}
        <div className="h-48 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={agingData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <XAxis dataKey="bucket" stroke="#64748b" tick={{ fontSize: 10 }} axisLine={{ stroke: '#334155' }} tickLine={false} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} axisLine={{ stroke: '#334155' }} tickLine={false} tickFormatter={(val) => formatCurrency(val, currency)} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                {agingData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800 text-xs flex justify-between items-center text-slate-400 font-mono">
        <span>Total Outstanding AR:</span>
        <span className="text-slate-100 font-bold text-sm">
          {formatCurrency(totalOutstanding, currency)}
        </span>
      </div>
    </div>
  );
}
