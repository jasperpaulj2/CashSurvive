import React, { useState } from 'react';
import {
  Wallet,
  ArrowDownLeft,
  ArrowUpRight,
  Repeat,
  Landmark,
  PlusCircle,
  Search,
  Filter,
  AlertCircle,
  CheckCircle2,
  Clock,
  Sparkles,
} from 'lucide-react';
import { useFinancial } from '../context/FinancialContext';
import MetricCard from '../components/common/MetricCard';
import Modal from '../components/common/Modal';
import { formatCurrency, formatDate } from '../utils/formatters';

export default function FinancialStateView() {
  const { pipelineData, addInvoice, addBill, executePipeline, analyzing } = useFinancial();
  const [subTab, setSubTab] = useState('receivables');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState('invoice'); // 'invoice' | 'bill'
  const [formData, setFormData] = useState({
    customer_id: '',
    vendor_id: '',
    amount: '',
    due_date: new Date().toISOString().split('T')[0],
    category: 'RAW_MATERIALS',
    is_critical: true,
    payment_reliability: 'HIGH',
  });

  const state = pipelineData?.financial_state || {};
  const currency = state?.currency || 'INR';

  const receivables = state.receivables || [];
  const payables = state.payables || [];
  const recurring = state.recurring_costs || [];
  const creditFacilities = state.credit_facilities || [];

  const totalReceivables = receivables.reduce((sum, r) => sum + (Number(r.amount) || 0), 0);
  const totalPayables = payables.reduce((sum, p) => sum + (Number(p.amount) || 0), 0);
  const totalMonthlyRecurring = recurring.reduce((sum, r) => sum + (Number(r.amount) || 0), 0);

  // Filtered lists
  const filteredReceivables = receivables.filter((r) => {
    const matchesSearch = (r.customer_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (r.invoice_number || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredPayables = payables.filter((p) => {
    const matchesSearch = (p.vendor_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (p.bill_number || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleCreateTransaction = (e) => {
    e.preventDefault();
    if (!formData.amount || Number(formData.amount) <= 0) return;

    if (modalType === 'invoice') {
      addInvoice({
        customer_id: formData.customer_id || 'New Customer Ltd',
        amount: formData.amount,
        due_date: formData.due_date,
        payment_reliability: formData.payment_reliability,
      });
    } else {
      addBill({
        vendor_id: formData.vendor_id || 'New Vendor Enterprise',
        amount: formData.amount,
        due_date: formData.due_date,
        category: formData.category,
        is_critical: formData.is_critical,
      });
    }

    setIsModalOpen(false);
    setFormData({
      customer_id: '',
      vendor_id: '',
      amount: '',
      due_date: new Date().toISOString().split('T')[0],
      category: 'RAW_MATERIALS',
      is_critical: true,
      payment_reliability: 'HIGH',
    });
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Financial Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Current Cash in Hand"
          value={formatCurrency(state.current_cash, currency)}
          subtitle={`Reserve Target: ${formatCurrency(state.minimum_cash_reserve, currency)}`}
          icon={Wallet}
          highlightColor={state.current_cash >= state.minimum_cash_reserve ? 'emerald' : 'amber'}
        />

        <MetricCard
          title="Total Receivables (AR)"
          value={formatCurrency(totalReceivables, currency)}
          subtitle={`${receivables.length} Invoices Outstanding`}
          icon={ArrowDownLeft}
          highlightColor="emerald"
          trend={`${receivables.filter(r => r.status === 'OVERDUE').length} Overdue`}
          trendPositive={false}
        />

        <MetricCard
          title="Total Payables (AP)"
          value={formatCurrency(totalPayables, currency)}
          subtitle={`${payables.length} Supplier Bills Due`}
          icon={ArrowUpRight}
          highlightColor="rose"
        />

        <MetricCard
          title="Monthly Fixed Burn"
          value={formatCurrency(totalMonthlyRecurring, currency)}
          subtitle={`${recurring.length} Recurring Commitments`}
          icon={Repeat}
          highlightColor="indigo"
        />
      </div>

      {/* Main Financial State Inspector Card */}
      <div className="glass-panel rounded-xl border border-slate-800 p-6">
        {/* Header & Sub-tab Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <span>Financial Position & Ledgers</span>
              <span className="text-xs font-mono font-normal text-slate-400">
                (Member 1 — {state.company_name || 'Aarav Textiles Pvt Ltd'})
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Inspecting balance sheet working capital and commercial commitments as of {formatDate(state.as_of)}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Sub-tabs */}
            <div className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800 text-xs font-medium">
              <button
                onClick={() => setSubTab('receivables')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  subTab === 'receivables' ? 'bg-emerald-500/20 text-emerald-300 font-bold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Invoices (AR) ({receivables.length})
              </button>
              <button
                onClick={() => setSubTab('payables')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  subTab === 'payables' ? 'bg-rose-500/20 text-rose-300 font-bold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Payables (AP) ({payables.length})
              </button>
              <button
                onClick={() => setSubTab('recurring')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  subTab === 'recurring' ? 'bg-indigo-500/20 text-indigo-300 font-bold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Recurring Costs ({recurring.length})
              </button>
              <button
                onClick={() => setSubTab('credit')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  subTab === 'credit' ? 'bg-amber-500/20 text-amber-300 font-bold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Credit Facilities ({creditFacilities.length})
              </button>
            </div>

            {/* Simulate / Add Transaction Button */}
            <button
              onClick={() => {
                setModalType(subTab === 'payables' ? 'bill' : 'invoice');
                setIsModalOpen(true);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md transition-all"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Simulate {subTab === 'payables' ? 'Bill' : 'Invoice'}</span>
            </button>
          </div>
        </div>

        {/* Sub-view: Receivables (AR) */}
        {subTab === 'receivables' && (
          <div className="space-y-4">
            {/* Search & Filter Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="relative w-full sm:w-72">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search customer or invoice #..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-900/80 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center gap-2 self-end sm:self-auto text-xs">
                <span className="text-slate-500 text-[11px] font-mono">Status:</span>
                {['ALL', 'PENDING', 'OVERDUE'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-2.5 py-1 rounded-md text-xs font-mono transition-all ${
                      statusFilter === st ? 'bg-slate-700 text-slate-100 font-bold' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 font-mono text-[11px] border-b border-slate-800">
                  <tr>
                    <th className="p-3">Invoice #</th>
                    <th className="p-3">Customer</th>
                    <th className="p-3">Amount</th>
                    <th className="p-3">Due Date</th>
                    <th className="p-3">Days Overdue</th>
                    <th className="p-3">Payment Reliability</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-navy-950/40">
                  {filteredReceivables.map((r, i) => (
                    <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-3 font-mono text-slate-300 font-semibold">{r.invoice_number}</td>
                      <td className="p-3 font-semibold text-slate-200">{r.customer_id}</td>
                      <td className="p-3 font-mono font-bold text-emerald-400">
                        {formatCurrency(r.amount, currency)}
                      </td>
                      <td className="p-3 text-slate-400 font-mono">{formatDate(r.due_date)}</td>
                      <td className="p-3 font-mono">
                        {r.days_overdue > 0 ? (
                          <span className="text-rose-400 font-bold">+{r.days_overdue} days</span>
                        ) : (
                          <span className="text-emerald-400">On Time</span>
                        )}
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                            r.payment_reliability === 'HIGH'
                              ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                              : r.payment_reliability === 'MEDIUM'
                              ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30'
                              : 'bg-rose-500/10 text-rose-300 border border-rose-500/30'
                          }`}
                        >
                          {r.payment_reliability || 'MEDIUM'}
                        </span>
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            r.status === 'OVERDUE' ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Sub-view: Payables (AP) */}
        {subTab === 'payables' && (
          <div className="space-y-4">
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 font-mono text-[11px] border-b border-slate-800">
                  <tr>
                    <th className="p-3">Bill #</th>
                    <th className="p-3">Vendor</th>
                    <th className="p-3">Category</th>
                    <th className="p-3">Amount</th>
                    <th className="p-3">Due Date</th>
                    <th className="p-3">Terms</th>
                    <th className="p-3">Critical Priority</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-navy-950/40">
                  {filteredPayables.map((p, i) => (
                    <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-3 font-mono text-slate-300 font-semibold">{p.bill_number}</td>
                      <td className="p-3 font-semibold text-slate-200">{p.vendor_id}</td>
                      <td className="p-3 text-slate-400 font-mono text-[11px]">{p.category}</td>
                      <td className="p-3 font-mono font-bold text-rose-400">
                        {formatCurrency(p.amount, currency)}
                      </td>
                      <td className="p-3 text-slate-400 font-mono">{formatDate(p.due_date)}</td>
                      <td className="p-3 font-mono text-slate-400">{p.payment_terms || 'NET30'}</td>
                      <td className="p-3">
                        {p.is_critical ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[10px] font-bold">
                            <AlertCircle className="w-3 h-3" /> CRITICAL
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                            Standard
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Sub-view: Recurring Costs */}
        {subTab === 'recurring' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recurring.map((rec, i) => (
              <div key={i} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start justify-between">
                <div>
                  <h4 className="font-bold text-slate-200 text-sm">{rec.name}</h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Category: <span className="font-mono text-slate-300">{rec.category}</span>
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Due Day {rec.due_day} of every month ({rec.frequency})
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-base font-bold font-mono text-rose-400">
                    {formatCurrency(rec.amount, currency)}
                  </span>
                  <span className="block text-[10px] text-slate-400 mt-1">
                    {rec.is_critical ? (
                      <span className="text-rose-400 font-bold">Non-Negotiable</span>
                    ) : (
                      'Discretionary'
                    )}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Sub-view: Credit Facilities */}
        {subTab === 'credit' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {creditFacilities.map((facility, i) => {
              const utilPct = facility.total_limit > 0 ? (facility.drawn_amount / facility.total_limit) * 100 : 0;
              return (
                <div key={i} className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <Landmark className="w-4 h-4 text-emerald-400" />
                        <h4 className="font-bold text-slate-200 text-sm">{facility.institution}</h4>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">{facility.facility_type}</p>
                    </div>
                    <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                      {facility.interest_rate_pct}% p.a.
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div>
                    <div className="flex justify-between text-xs font-mono text-slate-400 mb-1">
                      <span>Utilized: {formatCurrency(facility.drawn_amount, currency)}</span>
                      <span>Limit: {formatCurrency(facility.total_limit, currency)}</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full"
                        style={{ width: `${Math.min(100, utilPct)}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex justify-between items-center text-xs pt-2 border-t border-slate-800/80 font-mono">
                    <span className="text-slate-400">Available Buffer:</span>
                    <span className="text-emerald-300 font-bold">
                      {formatCurrency(facility.available_limit, currency)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal for adding simulated transaction */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Simulate New ${modalType === 'invoice' ? 'Invoice (Receivable)' : 'Supplier Bill (Payable)'}`}
      >
        <form onSubmit={handleCreateTransaction} className="space-y-4 text-xs">
          {modalType === 'invoice' ? (
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Customer Name / Entity</label>
              <input
                type="text"
                required
                placeholder="e.g. Aditya Birla Fashion Ltd"
                value={formData.customer_id}
                onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
          ) : (
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Vendor Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Vardhman Textiles Ltd"
                value={formData.vendor_id}
                onChange={(e) => setFormData({ ...formData, vendor_id: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Amount ({currency})</label>
              <input
                type="number"
                required
                min="1000"
                placeholder="e.g. 500000"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 font-semibold mb-1">Due Date</label>
              <input
                type="date"
                required
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {modalType === 'invoice' ? (
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Payment Reliability</label>
              <select
                value={formData.payment_reliability}
                onChange={(e) => setFormData({ ...formData, payment_reliability: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="HIGH">High (90%+ On-Time)</option>
                <option value="MEDIUM">Medium (60-80% On-Time)</option>
                <option value="LOW">Low (Frequent Delays)</option>
              </select>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="RAW_MATERIALS">Raw Materials</option>
                  <option value="CHEMICALS">Chemicals & Dyes</option>
                  <option value="UTILITIES">Utilities</option>
                  <option value="FREIGHT">Freight & Logistics</option>
                  <option value="PACKAGING">Packaging</option>
                </select>
              </div>

              <div className="flex items-center pt-6">
                <label className="flex items-center gap-2 text-slate-300 font-semibold cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_critical}
                    onChange={(e) => setFormData({ ...formData, is_critical: e.target.checked })}
                    className="rounded border-slate-700 text-emerald-500 focus:ring-0 w-4 h-4 bg-slate-900"
                  />
                  <span>Critical (Non-negotiable)</span>
                </label>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold shadow-md"
            >
              Add to Simulation Ledger
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
