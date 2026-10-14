import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { TopNav } from './components/TopNav';
import { DisclaimerBanner } from './components/DisclaimerBanner';

// Pages
import { DashboardOverview } from './pages/DashboardOverview';
import { PatientRegistry } from './pages/PatientRegistry';
import { ReadmissionRisk } from './pages/ReadmissionRisk';
import { WeeklyCallList } from './pages/WeeklyCallList';
import { ModelEvaluation } from './pages/ModelEvaluation';
import { FairnessAudit } from './pages/FairnessAudit';
import { InterventionPlanner } from './pages/InterventionPlanner';
import { ReportsPage } from './pages/ReportsPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
        {/* Persistent Clinical Decision Support Disclaimer */}
        <DisclaimerBanner />

        <div className="flex-1 flex overflow-hidden">
          {/* Collapsible Clinical Navigation Sidebar */}
          <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

          {/* Main Work Area */}
          <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
            {/* Top Navigation Header */}
            <TopNav />

            {/* Application Routed Views */}
            <main className="flex-1 pb-16">
              <Routes>
                <Route path="/" element={<DashboardOverview />} />
                <Route path="/patients" element={<PatientRegistry />} />
                <Route path="/risk-prediction" element={<ReadmissionRisk />} />
                <Route path="/call-list" element={<WeeklyCallList />} />
                <Route path="/evaluation" element={<ModelEvaluation />} />
                <Route path="/fairness" element={<FairnessAudit />} />
                <Route path="/intervention-planner" element={<InterventionPlanner />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/datasets" element={<DatasetsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;
