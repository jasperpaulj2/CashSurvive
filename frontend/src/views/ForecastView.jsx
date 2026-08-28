import React, { useState } from 'react';
import {
  TrendingUp,
  Percent,
  Calendar,
  Layers,
  ArrowDownRight,
  ArrowUpRight,
  Filter,
  Search,
} from 'lucide-react';
import { useFinancial } from '../context/FinancialContext';
import MetricCard from '../components/common/MetricCard';
import ForecastChart from '../components/forecast/ForecastChart';
import AgingReportChart from '../components/forecast/AgingReportChart';
import CustomerRiskList from '../components/forecast/CustomerRiskList';
import { formatCurrency, formatCurrencyDetailed, formatDate, formatPercentage } from '../utils/formatters';

export default function ForecastView() {
  const {
    pipelineData,
    horizonDays,
    setHorizonDays,
    numSimulations,
    setNumSimulations,
    executePipeline,
    analyzing,
  } = useFinancial();

  const [tableSearch, setTableSearch] = useState('');
  const [onlyShortfalls, setOnlyShortfalls] = useState(false);

  const state = pipelineData?.financial_state || {};
  const forecast = pipelineData?.forecast || {};
  const summary = forecast.summary || {};
  const agingReport = forecast.aging_report || {};
  const customerRisk = forecast.customer_risk || {};
  const projections = forecast.projections || [];
  const currency = state?.currency || 'INR';

  const startingCash = summary.starting_cash ?? state.current_cash ?? 0;
  const endingBalance = summary.ending_balance ?? 0;
  const minBalance = summary.min_balance ?? 0;
  const shortfallProb = summary.probability_of_shortfall_pct ?? 0;

  // Filtered daily projections
  const filteredProjections = projections.filter((p) => {
    const matchesSearch = p.date.includes(tableSearch);
    const matchesShortfall = !onlyShortfalls || p.is_shortfall || p.projected_balance < (state.minimum_cash_reserve || 0);
    return matchesSearch && matchesShortfall;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Forecast Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Simulated Ending Balance"
          value={formatCurrency(endingBalance, currency)}
          subtitle={`Trajectory Horizon: ${horizonDays} Days`}
          icon={TrendingUp}
          highlightColor={endingBalance >= (state.minimum_cash_reserve || 0) ? 'emerald' : 'rose'}
          trend={endingBalance > startingCash ? 'Net Cash Accretive' : 'Net Cash Drawdown'}
          trendPositive={endingBalance > startingCash}
        />

        <MetricCard
          title="Minimum Projected Trough"
          value={formatCurrency(minBalance, currency)}
          subtitle={`Buffer Target: ${formatCurrency(state.minimum_cash_reserve, currency)}`}
          icon={Layers}
          highlightColor={minBalance >= (state.minimum_cash_reserve || 0) ? 'emerald' : 'amber'}
        />

        <MetricCard
          title="Shortfall Risk Probability"
          value={formatPercentage(shortfallProb / 100, 1)}
          subtitle={`Evaluated over ${numSimulations} Paths`}
          icon={Percent}
          highlightColor={shortfallProb < 15 ? 'emerald' : shortfallProb < 40 ? 'amber' : 'rose'}
        />

        <MetricCard
          title="Expected Net Cash Change"
          value={formatCurrency(summary.net_cash_change, currency)}
          subtitle={`Inflows: ${formatCurrency(summary.expected_inflows, currency)}`}
          icon={summary.net_cash_change >= 0 ? ArrowUpRight : ArrowDownRight}
          highlightColor={summary.net_cash_change >= 0 ? 'emerald' : 'rose'}
        />
      </div>

      {/* Main Forecast Chart */}
      <ForecastChart
        projections={projections}
        minimumReserve={state.minimum_cash_reserve || 0}
        currency={currency}
        horizonDays={horizonDays}
        onHorizonChange={(h) => {
          setHorizonDays(h);
          executePipeline({ horizon_days: h });
        }}
        numSimulations={numSimulations}
        onSimulationsChange={(s) => {
          setNumSimulations(s);
          executePipeline({ num_simulations: s });
        }}
        isAnalyzing={analyzing}
      />

      {/* Two Column Grid: AR Aging Distribution & Customer Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgingReportChart
          aging={agingReport.aging || {}}
          dso={agingReport.dso || 0}
          currency={currency}
        />

        <CustomerRiskList
          customerProfiles={customerRisk.profiles || []}
          highRiskCustomers={customerRisk.high_risk_customers || []}
        />
      </div>

      {/* Daily Projections Table Card */}
      <div className="glass-panel rounded-xl p-5 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Daily Projected Cash Flow Trajectory
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Deterministic scheduled net impact & Monte Carlo confidence intervals by day
            </p>
          </div>

          <div className="flex items-center gap-3 self-end sm:self-auto text-xs">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2" />
              <input
                type="text"
                placeholder="Search date..."
                value={tableSearch}
                onChange={(e) => setTableSearch(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-md pl-8 pr-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <label className="flex items-center gap-1.5 cursor-pointer text-slate-300 font-medium">
              <input
                type="checkbox"
                checked={onlyShortfalls}
                onChange={(e) => setOnlyShortfalls(e.target.checked)}
                className="rounded border-slate-700 text-rose-500 focus:ring-0 w-3.5 h-3.5 bg-slate-900"
              />
              <span>Only Below Reserve</span>
            </label>
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 font-mono text-[11px] border-b border-slate-800">
              <tr>
                <th className="p-2.5">Date</th>
                <th className="p-2.5">Projected Balance</th>
                <th className="p-2.5">90% CI Range</th>
                <th className="p-2.5">AR Inflow</th>
                <th className="p-2.5">Scheduled Outflows / Net</th>
                <th className="p-2.5">Reserve Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-navy-950/40 font-mono">
              {filteredProjections.map((row, idx) => {
                const isBelowMin = row.projected_balance < (state.minimum_cash_reserve || 0);
                const isZeroDeficit = row.projected_balance <= 0;
                return (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-2.5 font-semibold text-slate-300 font-sans">{formatDate(row.date)}</td>
                    <td className="p-2.5 font-bold text-emerald-400">
                      {formatCurrencyDetailed(row.projected_balance, currency)}
                    </td>
                    <td className="p-2.5 text-slate-400 text-[11px]">
                      {row.uncertainty?.lower_bound !== undefined ? (
                        <span>
                          [{formatCurrency(row.uncertainty.lower_bound, currency)} – {formatCurrency(row.uncertainty.upper_bound, currency)}]
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="p-2.5 text-emerald-300 font-semibold">
                      +{formatCurrency(row.receivable_inflow || 0, currency)}
                    </td>
                    <td className={`p-2.5 ${row.scheduled_net < 0 ? 'text-rose-400' : 'text-slate-300'}`}>
                      {formatCurrency(row.scheduled_net || 0, currency)}
                    </td>
                    <td className="p-2.5 font-sans">
                      {isZeroDeficit ? (
                        <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px] font-bold">
                          DEFICIT (₹0)
                        </span>
                      ) : isBelowMin ? (
                        <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-semibold">
                          BELOW RESERVE
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 text-[10px]">
                          ADEQUATE
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
