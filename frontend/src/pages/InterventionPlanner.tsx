import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  TrendingDown,
  DollarSign,
  AlertCircle,
  Percent,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { getImpactAnalysis } from '../services/api';

export const InterventionPlanner: React.FC = () => {
  const [impactData, setImpactData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  // Custom interactive simulation state
  const [customReach, setCustomReach] = useState(75);
  const [customRRR, setCustomRRR] = useState(25);
  const [customCostPerReadmission, setCustomCostPerReadmission] = useState(15200);

  useEffect(() => {
    fetchImpact();
  }, []);

  const fetchImpact = async () => {
    setLoading(true);
    try {
      const data = await getImpactAnalysis(50, 0.42);
      setImpactData(data);
    } catch (err) {
      console.error('Failed to load impact analysis', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        <div className="w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-sm font-medium">Calculating readmission aversion scenarios...</p>
      </div>
    );
  }

  // Interactive custom scenario calculations
  const reachedPatients = 50 * (customReach / 100);
  const baselineReadmissionsInReached = reachedPatients * 0.42;
  const customAverted = baselineReadmissionsInReached * (customRRR / 100);
  const customGrossSavings = customAverted * customCostPerReadmission;
  const customProgramCost = 50 * 125;
  const customNetSavings = customGrossSavings - customProgramCost;
  const customROI = customProgramCost > 0 ? (customGrossSavings / customProgramCost) : 0;

  const scenarios = impactData?.scenarios || {};

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2.5">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Intervention Impact & Scenario Planner</h1>
          <span className="text-xs bg-teal-50 text-teal-800 border border-teal-300 font-bold px-2.5 py-0.5 rounded-full">
            Capacity: 50 Pts/Week
          </span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          Modeling potential 30-day readmissions averted, transitional care reach, and cost avoidance under explicit uncertainty boundaries.
        </p>
      </div>

      {/* Benchmark Scenarios Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Conservative */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Conservative Scenario</span>
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono font-bold">
              60% Reach • 15% RRR
            </span>
          </div>
          <div className="text-3xl font-extrabold text-slate-800 tracking-tight">
            ~{scenarios.conservative?.estimated_readmissions_averted} Averted
          </div>
          <p className="text-xs text-slate-500">{scenarios.conservative?.description}</p>
          <div className="pt-2 border-t border-slate-100 flex justify-between text-xs">
            <span className="text-slate-500">Net Cost Avoidance:</span>
            <span className="font-bold text-slate-800">
              ${Math.round(scenarios.conservative?.net_cost_avoidance || 0).toLocaleString()}
            </span>
          </div>
        </div>

        {/* Central */}
        <div className="bg-white rounded-xl p-5 border border-teal-500/40 ring-1 ring-teal-500/10 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-teal-800 uppercase tracking-wider">Central Scenario (Baseline)</span>
            <span className="text-xs bg-teal-50 text-teal-800 px-2 py-0.5 rounded font-mono font-bold border border-teal-200">
              75% Reach • 25% RRR
            </span>
          </div>
          <div className="text-3xl font-extrabold text-teal-900 tracking-tight">
            ~{scenarios.central?.estimated_readmissions_averted} Averted
          </div>
          <p className="text-xs text-slate-500">{scenarios.central?.description}</p>
          <div className="pt-2 border-t border-slate-100 flex justify-between text-xs">
            <span className="text-slate-500">Net Cost Avoidance:</span>
            <span className="font-bold text-teal-900">
              ${Math.round(scenarios.central?.net_cost_avoidance || 0).toLocaleString()}
            </span>
          </div>
        </div>

        {/* Optimistic */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">Optimistic Scenario</span>
            <span className="text-xs bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded font-mono font-bold border border-emerald-200">
              85% Reach • 35% RRR
            </span>
          </div>
          <div className="text-3xl font-extrabold text-emerald-900 tracking-tight">
            ~{scenarios.optimistic?.estimated_readmissions_averted} Averted
          </div>
          <p className="text-xs text-slate-500">{scenarios.optimistic?.description}</p>
          <div className="pt-2 border-t border-slate-100 flex justify-between text-xs">
            <span className="text-slate-500">Net Cost Avoidance:</span>
            <span className="font-bold text-emerald-900">
              ${Math.round(scenarios.optimistic?.net_cost_avoidance || 0).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Interactive Sensitivity Simulator */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div>
          <h2 className="text-base font-bold text-slate-900">Interactive Intervention Sensitivity Simulator</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Test custom assumptions on outreach reachability and intervention relative risk reduction (RRR).
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Sliders */}
          <div className="space-y-4 md:col-span-2">
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                <span>Successful Contact / Reach Rate</span>
                <span className="text-teal-700 font-bold">{customReach}% ({Math.round(50 * customReach / 100)} Patients)</span>
              </div>
              <input
                type="range"
                min="40"
                max="95"
                step="5"
                value={customReach}
                onChange={(e) => setCustomReach(Number(e.target.value))}
                className="w-full accent-teal-600"
              />
              <span className="text-[11px] text-slate-400">Fraction of the 50 prioritized patients successfully contacted by care team</span>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                <span>Intervention Relative Risk Reduction (RRR)</span>
                <span className="text-teal-700 font-bold">{customRRR}% Reduction</span>
              </div>
              <input
                type="range"
                min="10"
                max="45"
                step="5"
                value={customRRR}
                onChange={(e) => setCustomRRR(Number(e.target.value))}
                className="w-full accent-teal-600"
              />
              <span className="text-[11px] text-slate-400">Literature benchmark for multifaceted nurse call + med reconciliation</span>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                <span>Hospital Cost per Readmission (CMS Benchmark)</span>
                <span className="text-slate-900 font-bold">${customCostPerReadmission.toLocaleString()}</span>
              </div>
              <input
                type="range"
                min="10000"
                max="24000"
                step="1000"
                value={customCostPerReadmission}
                onChange={(e) => setCustomCostPerReadmission(Number(e.target.value))}
                className="w-full accent-teal-600"
              />
            </div>
          </div>

          {/* Real-time Simulated Outputs */}
          <div className="bg-slate-900 text-white rounded-xl p-5 flex flex-col justify-between space-y-4">
            <div>
              <span className="text-[11px] text-teal-400 font-mono uppercase tracking-wider block">Simulated Output</span>
              <div className="text-3xl font-extrabold text-white mt-1">
                ~{customAverted.toFixed(1)}
              </div>
              <span className="text-xs text-slate-400">Estimated Avoided Readmissions / Week</span>
            </div>

            <div className="space-y-2 text-xs border-t border-slate-800 pt-3">
              <div className="flex justify-between">
                <span className="text-slate-400">Gross Cost Avoidance:</span>
                <span className="font-bold text-white">${Math.round(customGrossSavings).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Care Program Cost ($125/pt):</span>
                <span className="font-bold text-slate-300">${customProgramCost.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-teal-300 font-bold border-t border-slate-800 pt-1">
                <span>Net Savings / Week:</span>
                <span>${Math.round(customNetSavings).toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Estimated Program ROI:</span>
                <span className="font-bold text-white">{customROI.toFixed(1)}x</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sensitivity Matrix Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
        <h3 className="text-sm font-bold text-slate-900">Sensitivity Matrix: Estimated Averted Readmissions</h3>
        <p className="text-xs text-slate-500 mb-2">
          Grid of avoided readmissions across combinations of patient reach rates and relative risk reductions.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-center border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-600 border-b border-slate-200">
                <th className="py-2.5 px-3 text-left">Reach Rate</th>
                <th className="py-2.5 px-3">10% RRR</th>
                <th className="py-2.5 px-3">20% RRR</th>
                <th className="py-2.5 px-3 bg-teal-50 text-teal-900 font-bold">25% RRR (Benchmark)</th>
                <th className="py-2.5 px-3">30% RRR</th>
                <th className="py-2.5 px-3">40% RRR</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {impactData?.sensitivity_matrix?.map((row: any) => (
                <tr key={row.reach_rate} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 text-left font-bold text-slate-900">{row.reach_rate}% Reach</td>
                  <td className="py-2.5 px-3 font-mono">{row.rrr_10}</td>
                  <td className="py-2.5 px-3 font-mono">{row.rrr_20}</td>
                  <td className="py-2.5 px-3 font-mono font-bold text-teal-800 bg-teal-50/50">{row.rrr_25}</td>
                  <td className="py-2.5 px-3 font-mono">{row.rrr_30}</td>
                  <td className="py-2.5 px-3 font-mono">{row.rrr_40}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Honest Uncertainty Disclaimer */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start space-x-3">
        <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
        <p className="leading-relaxed">{impactData?.uncertainty_disclaimer}</p>
      </div>
    </div>
  );
};
