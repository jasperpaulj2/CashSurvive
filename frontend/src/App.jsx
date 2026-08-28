import React from 'react';
import { useFinancial } from './context/FinancialContext';
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';
import PipelineIndicator from './components/layout/PipelineIndicator';
import ErrorAlert from './components/common/ErrorAlert';
import LoadingSpinner from './components/common/LoadingSpinner';
import OfflineBanner from './components/common/OfflineBanner';

// Views
import DashboardView from './views/DashboardView';
import FinancialStateView from './views/FinancialStateView';
import ForecastView from './views/ForecastView';
import ScenariosView from './views/ScenariosView';
import RiskView from './views/RiskView';
import OptimizerView from './views/OptimizerView';

export default function App() {
  const { activeTab, loading, error, executePipeline } = useFinancial();

  const renderActiveView = () => {
    switch (activeTab) {
      case 'financial':
        return <FinancialStateView />;
      case 'forecast':
        return <ForecastView />;
      case 'scenarios':
        return <ScenariosView />;
      case 'risk':
        return <RiskView />;
      case 'optimizer':
        return <OptimizerView />;
      case 'dashboard':
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar />

      {/* Offline Demo Mode Notification Banner */}
      <OfflineBanner />

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar />

        {/* Center Content Canvas */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Multi-Module Pipeline Execution Indicator */}
          <PipelineIndicator />

          {/* Error Alert (if any active error) */}
          {error && <ErrorAlert error={error} onRetry={() => executePipeline()} />}

          {/* Initial Loading Screen */}
          {loading ? (
            <LoadingSpinner message="Initializing CashSurvive Control Tower..." />
          ) : (
            renderActiveView()
          )}
        </main>
      </div>
    </div>
  );
}
