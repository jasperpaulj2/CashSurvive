import React from 'react';
import { CheckCircle2, ArrowRight, Clock, AlertCircle } from 'lucide-react';
import { useFinancial } from '../../context/FinancialContext';

export default function PipelineIndicator() {
  const { pipelineData, analyzing } = useFinancial();

  const stages = [
    { name: 'Financial State', member: 'Member 1', completed: !!pipelineData?.financial_state },
    { name: 'Forecasting Engine', member: 'Member 2', completed: !!pipelineData?.forecast },
    { name: 'Scenario Generation', member: 'Member 3', completed: !!pipelineData?.scenarios },
    { name: 'Risk Evaluation', member: 'Member 3', completed: !!pipelineData?.risk },
    { name: 'Optimization Hook', member: 'Member 4 (Ext)', completed: !!pipelineData?.optimization_extension },
  ];

  return (
    <div className="glass-panel rounded-xl p-4 border border-slate-800">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Autonomous Pipeline Execution Flow
        </span>
        <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5">
          {analyzing ? (
            <>
              <Clock className="w-3.5 h-3.5 animate-spin" />
              Running Multi-Module Analysis...
            </>
          ) : pipelineData ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Pipeline Synchronized
            </>
          ) : (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
              Awaiting Execution
            </>
          )}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
        {stages.map((stage, idx) => {
          const isDone = stage.completed && !analyzing;
          return (
            <div
              key={stage.name}
              className={`p-2.5 rounded-lg border text-xs transition-all flex items-center justify-between ${
                isDone
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : analyzing
                  ? 'bg-slate-800/40 border-slate-700 text-slate-400 animate-pulse'
                  : 'bg-slate-900/40 border-slate-800 text-slate-500'
              }`}
            >
              <div>
                <p className="font-semibold">{stage.name}</p>
                <span className="text-[10px] text-slate-400">{stage.member}</span>
              </div>
              <div>
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-slate-700 block" />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
