import React from 'react';
import {
  LayoutDashboard,
  Wallet,
  TrendingUp,
  Zap,
  ShieldAlert,
  Sparkles,
  Cpu,
  Building2,
} from 'lucide-react';
import { useFinancial } from '../../context/FinancialContext';
import { formatCurrency } from '../../utils/formatters';

export default function Sidebar() {
  const { activeTab, setActiveTab, pipelineData } = useFinancial();

  const navItems = [
    { id: 'dashboard', label: 'Control Tower', icon: LayoutDashboard, badge: 'Overview' },
    { id: 'financial', label: 'Financial State', icon: Wallet, badge: 'Member 1' },
    { id: 'forecast', label: 'Cash Forecast', icon: TrendingUp, badge: 'Member 2' },
    { id: 'scenarios', label: 'Stress Testing', icon: Zap, badge: 'Member 3' },
    { id: 'risk', label: 'Risk Analytics', icon: ShieldAlert, badge: 'Member 3' },
    { id: 'optimizer', label: 'Survival Optimizer', icon: Sparkles, badge: 'Member 4' },
  ];

  const state = pipelineData?.financial_state;
  const companyName = state?.company_name || 'Aarav Textiles Pvt Ltd';
  const currency = state?.currency || 'INR';

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-navy-950/70 backdrop-blur-md flex flex-col justify-between p-4 shrink-0">
      {/* Nav List */}
      <div className="space-y-5">
        <div>
          <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
            Control Tower Navigation
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                    <span className="font-semibold">{item.label}</span>
                  </div>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                      isActive
                        ? 'bg-emerald-500/20 text-emerald-300 font-bold'
                        : 'bg-slate-800 text-slate-500'
                    }`}
                  >
                    {item.badge}
                  </span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Company Quick Summary */}
        {state && (
          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80 text-xs">
            <div className="flex items-center gap-2 text-slate-300 font-semibold mb-2">
              <Building2 className="w-4 h-4 text-emerald-400" />
              <span className="truncate">{companyName}</span>
            </div>
            <div className="space-y-1.5 text-[11px] text-slate-400">
              <div className="flex justify-between">
                <span>Current Cash:</span>
                <span className="font-mono text-slate-200 font-bold">
                  {formatCurrency(state.current_cash, currency)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Min Reserve:</span>
                <span className="font-mono text-slate-400">
                  {formatCurrency(state.minimum_cash_reserve, currency)}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Module Status */}
      <div className="pt-4 border-t border-slate-800/60">
        <div className="flex items-center gap-2 text-[11px] text-slate-400 mb-2 font-mono">
          <Cpu className="w-3.5 h-3.5 text-slate-500" />
          <span>System Architecture</span>
        </div>
        <div className="grid grid-cols-2 gap-1.5 text-[10px] font-mono">
          <div className="bg-slate-900/60 p-1.5 rounded border border-slate-800">
            <span className="text-emerald-400 block font-bold">M1: State</span>
            Active (DB)
          </div>
          <div className="bg-slate-900/60 p-1.5 rounded border border-slate-800">
            <span className="text-emerald-400 block font-bold">M2: Forecast</span>
            Monte Carlo
          </div>
          <div className="bg-slate-900/60 p-1.5 rounded border border-slate-800">
            <span className="text-emerald-400 block font-bold">M3: Stress & Risk</span>
            5-Factor Engine
          </div>
          <div className="bg-slate-900/60 p-1.5 rounded border border-slate-800">
            <span className="text-emerald-400 block font-bold">M4: Optimizer</span>
            AI Hook
          </div>
        </div>
      </div>
    </aside>
  );
}
