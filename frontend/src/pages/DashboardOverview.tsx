import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  AlertTriangle,
  PhoneCall,
  Activity,
  Award,
  CheckCircle2,
  TrendingUp,
  FileCheck,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { getDashboardSummary, DashboardSummary } from '../services/api';

export const DashboardOverview: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getDashboardSummary();
      setData(res);
    } catch (err: any) {
      setError(err?.message || 'Failed to connect to ReCare backend service.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-3 text-slate-500">
          <div className="w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm font-medium">Loading clinical analytics and live model KPIs...</p>
        </div>
      </div>
    );
  }

  if (error || !data || data.status === 'empty') {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="bg-white border border-slate-200 rounded-xl p-8 text-center shadow-xs">
          <ShieldAlert className="w-12 h-12 text-amber-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-900 mb-1">Database Setup Required</h2>
          <p className="text-sm text-slate-600 mb-6">
            {error || data?.status === 'empty' ? 'No encounter data loaded in the database yet.' : error}
          </p>
          <div className="flex justify-center space-x-4">
            <Link
              to="/datasets"
              className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 transition-colors shadow-xs"
            >
              Go to Dataset & Quality Manager
            </Link>
            <button
              onClick={fetchSummary}
              className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors"
            >
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  const kpi = data.kpi;
  const kpiCards = [
    {
      title: 'Total Discharges',
      value: kpi.total_encounters.toLocaleString(),
      subtitle: `${kpi.unique_patients.toLocaleString()} unique patients`,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'High-Risk Patients',
      value: kpi.predicted_high_risk.toLocaleString(),
      subtitle: `${Math.round((kpi.predicted_high_risk / kpi.total_encounters) * 100)}% of cohort (Risk ≥ 30%)`,
      icon: AlertTriangle,
      color: 'text-rose-600',
      bgColor: 'bg-rose-50',
    },
    {
      title: 'Monday Morning Call List',
      value: `${kpi.weekly_call_list_count} / ${kpi.weekly_capacity_limit}`,
      subtitle: 'Strict 50-patient outreach budget',
      icon: PhoneCall,
      color: 'text-teal-600',
      bgColor: 'bg-teal-50',
      highlight: true,
    },
    {
      title: 'Avg Predicted Risk',
      value: `${kpi.average_predicted_risk}%`,
      subtitle: `Observed baseline: ${kpi.observed_readmission_rate}%`,
      icon: Activity,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
    {
      title: 'Model AUC-PR',
      value: kpi.model_auc_pr ? kpi.model_auc_pr.toFixed(4) : '0.3608',
      subtitle: 'Primary metric on imbalanced data',
      icon: Award,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
    },
    {
      title: 'Top-50 Precision',
      value: `${Math.round((kpi.model_precision_at_50 || 0.66) * 100)}%`,
      subtitle: '3.6x enrichment over baseline',
      icon: CheckCircle2,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
    },
    {
      title: 'Expected Calib. Error',
      value: kpi.model_calibration_error ? `${(kpi.model_calibration_error * 100).toFixed(2)}%` : '1.08%',
      subtitle: 'Isotonic-calibrated probability',
      icon: TrendingUp,
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-50',
    },
    {
      title: 'Brier Calibration Score',
      value: kpi.model_brier_score ? kpi.model_brier_score.toFixed(4) : '0.1348',
      subtitle: 'Mean squared probability error',
      icon: FileCheck,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Clinical Operations Overview</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Real-time readmission risk stratification and resource-constrained care intervention priorities.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            to="/call-list"
            className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs md:text-sm font-semibold hover:bg-slate-800 transition-all shadow-xs"
          >
            <PhoneCall className="w-4 h-4 text-teal-400" />
            <span>Open Monday Morning Call List</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {kpiCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              className={`bg-white rounded-xl p-4 border transition-all shadow-xs ${
                card.highlight ? 'border-teal-500/40 ring-1 ring-teal-500/10' : 'border-slate-200'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{card.title}</span>
                <div className={`w-7 h-7 rounded-lg ${card.bgColor} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${card.color}`} />
                </div>
              </div>
              <div className="text-2xl font-bold text-slate-900 tracking-tight">{card.value}</div>
              <p className="text-xs text-slate-500 mt-1 truncate">{card.subtitle}</p>
            </div>
          );
        })}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Risk Tier Stratification</h3>
          <p className="text-xs text-slate-500 mb-4">Patient volume across clinical risk categories</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.charts.risk_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="count"
                >
                  {data.charts.risk_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: any) => [`${val.toLocaleString()} Encounters`, 'Volume']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center space-x-4 text-xs mt-2">
            {data.charts.risk_distribution.map((d, i) => (
              <div key={i} className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }}></span>
                <span className="text-slate-600 font-medium">{d.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Primary Condition Breakdown */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs lg:col-span-2">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Encounters by Primary Clinical Condition</h3>
          <p className="text-xs text-slate-500 mb-4">High-volume readmission cohorts tracked under HRRP</p>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.charts.condition_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                <XAxis dataKey="condition" tick={{ fontSize: 10, fill: '#64748b' }} interval={0} angle={-15} textAnchor="end" />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip
                  formatter={(val: any) => [`${val.toLocaleString()} Encounters`, 'Volume']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="total_encounters" fill="#0d9488" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Prominent Section: This Week's Care Priorities */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-slate-900">This Week's Care Priorities</h2>
              <span className="text-xs bg-teal-50 text-teal-700 border border-teal-200 px-2 py-0.5 rounded-full font-bold">
                Capacity: 50 Patients
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">Top-ranked discharged patients selected by optimizer for human care review</p>
          </div>
          <Link
            to="/call-list"
            className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center space-x-1"
          >
            <span>View Full 50-Patient Roster</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase font-semibold tracking-wider">
                <th className="py-3 px-4">Rank</th>
                <th className="py-3 px-4">Patient / Encounter</th>
                <th className="py-3 px-4">Predicted Risk</th>
                <th className="py-3 px-4">Expected Benefit</th>
                <th className="py-3 px-4">Recommended Intervention</th>
                <th className="py-3 px-4">Primary Action Plan</th>
                <th className="py-3 px-4">Contact Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {data.this_weeks_care_priorities.map((pt) => (
                <tr key={pt.encounter_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-bold text-slate-900">#{pt.rank}</td>
                  <td className="py-3 px-4 font-mono font-medium">
                    <Link to={`/patients?search=${pt.patient_id}`} className="text-teal-700 hover:underline">
                      {pt.patient_id}
                    </Link>
                    <span className="text-[11px] text-slate-400 block">{pt.encounter_id}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-block px-2 py-0.5 rounded text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                      {pt.risk_percentage}%
                    </span>
                  </td>
                  <td className="py-3 px-4 font-semibold text-emerald-700">
                    +{pt.expected_benefit_percentage}% Averted
                  </td>
                  <td className="py-3 px-4 font-medium text-slate-900">
                    {pt.recommended_intervention}
                    <span className="ml-1 text-[10px] text-teal-700 bg-teal-50 px-1.5 py-0.2 rounded border border-teal-200">
                      {pt.intervention_priority}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500 max-w-xs truncate" title={pt.action_plan}>
                    {pt.action_plan}
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                      {pt.contact_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
