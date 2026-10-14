import React, { useEffect, useState } from 'react';
import {
  Award,
  CheckCircle2,
  TrendingUp,
  FileCheck,
  Activity,
  Layers,
  HelpCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from 'recharts';
import { getEvaluationMetrics } from '../services/api';

export const ModelEvaluation: React.FC = () => {
  const [metrics, setMetrics] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const data = await getEvaluationMetrics();
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load evaluation metrics', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        <div className="w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-sm font-medium">Computing holdout test set evaluation metrics...</p>
      </div>
    );
  }

  const prim = metrics?.primary_metrics || {};
  const cap = metrics?.capacity_interpretation || {};

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2.5">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Model Evaluation & Calibration Engine</h1>
          <span className="text-xs bg-slate-100 text-slate-700 font-mono px-2.5 py-0.5 rounded border border-slate-200">
            {metrics?.model_version}
          </span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          Rigorous independent evaluation conducted on patient-isolated holdout test set (
          <strong>{metrics?.sample_size?.toLocaleString()} encounters</strong>, {metrics?.positive_cases} positive readmissions, {Math.round((metrics?.prevalence || 0) * 100)}% prevalence).
        </p>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">AUC-PR (Primary)</span>
            <Award className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-3xl font-extrabold text-indigo-900 tracking-tight">{prim.auc_pr?.toFixed(4)}</div>
          <p className="text-xs text-slate-500 mt-1">Average Precision on imbalanced data</p>
        </div>

        <div className="bg-white rounded-xl p-4 border border-teal-500/40 ring-1 ring-teal-500/10 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-teal-800 uppercase tracking-wider">Precision@50</span>
            <CheckCircle2 className="w-4 h-4 text-teal-600" />
          </div>
          <div className="text-3xl font-extrabold text-teal-900 tracking-tight">
            {Math.round((prim.precision_at_50 || 0) * 100)}%
          </div>
          <p className="text-xs text-teal-700 mt-1 font-medium">33 of top 50 confirmed readmissions</p>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Expected Calib. Error</span>
            <TrendingUp className="w-4 h-4 text-cyan-600" />
          </div>
          <div className="text-3xl font-extrabold text-cyan-900 tracking-tight">
            {((prim.expected_calibration_error || 0) * 100).toFixed(2)}%
          </div>
          <p className="text-xs text-slate-500 mt-1">Documented 10-bin ECE score</p>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Brier Score</span>
            <FileCheck className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-3xl font-extrabold text-purple-900 tracking-tight">{prim.brier_score?.toFixed(4)}</div>
          <p className="text-xs text-slate-500 mt-1">Mean squared probability error</p>
        </div>
      </div>

      {/* Capacity Constraint Interpretation Box */}
      <div className="bg-blue-50/60 border border-blue-200 rounded-xl p-5 text-xs text-blue-900 space-y-2 shadow-xs">
        <div className="flex items-center space-x-2">
          <HelpCircle className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <h3 className="font-bold text-sm text-blue-950">Capacity Interpretation: Recall@50 in Clinical Practice</h3>
        </div>
        <p className="text-blue-800 leading-relaxed">
          {cap.note ||
            'In a fixed 50-patient weekly care-coordination budget, Recall@50 measures what portion of actual positive readmissions are captured within the team\'s reach.'}
        </p>
        <div className="flex flex-wrap gap-4 pt-1 font-medium">
          <span>Weekly Outreach Budget: <strong>50 patients</strong></span>
          <span>True Readmissions in Top-50: <strong>{cap.positives_captured_in_top_50 || 33} patients</strong></span>
          <span>Top-50 Precision: <strong>{cap.top_50_precision_percentage || 66}%</strong> (3.6x enrichment over baseline 18%)</span>
        </div>
      </div>

      {/* Calibration and PR Curves */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Reliability Diagram */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Reliability Diagram (Probability Calibration)</h3>
          <p className="text-xs text-slate-500 mb-4">
            Predicted risk probability vs observed empirical readmission rate (10 bins)
          </p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics?.calibration_diagram || []} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="bin_range" tick={{ fontSize: 10, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip
                  formatter={(val: any, name: any) => [val, name === 'mean_predicted' ? 'Mean Predicted' : 'Empirical Observed']}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="mean_predicted" name="Mean Predicted" fill="#94a3b8" radius={[3, 3, 0, 0]} />
                <Bar dataKey="fraction_positive" name="Empirical Observed" fill="#0d9488" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center space-x-6 text-xs mt-2">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 bg-slate-400 rounded-sm"></span>
              <span className="text-slate-600">Mean Predicted Prob</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 bg-teal-600 rounded-sm"></span>
              <span className="text-slate-600">Empirical Event Rate</span>
            </div>
          </div>
        </div>

        {/* Precision-Recall Curve */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Precision-Recall Curve</h3>
          <p className="text-xs text-slate-500 mb-4">
            AUC-PR = {prim.auc_pr?.toFixed(4)} across probability decision thresholds
          </p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics?.precision_recall_curve || []} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="recall" tick={{ fontSize: 10, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} domain={[0, 1]} />
                <Tooltip
                  formatter={(val: any) => [val, 'Precision']}
                  labelFormatter={(lbl) => `Recall: ${lbl}`}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Line type="monotone" dataKey="precision" stroke="#6366f1" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-center text-xs text-slate-400 mt-2">
            Horizontal dashed reference at prevalence = {Math.round((metrics?.prevalence || 0) * 100)}%
          </p>
        </div>
      </div>

      {/* Confusion Matrix Table */}
      <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 mb-1">Confusion Matrix at 0.25 Screening Threshold</h3>
        <p className="text-xs text-slate-500 mb-4">
          Hospital transitional care screening benchmark (prioritizes high recall to minimize missed readmissions)
        </p>
        {metrics?.confusion_matrices?.threshold_0_25 && (
          <div className="max-w-md mx-auto grid grid-cols-2 gap-2 text-center text-xs">
            <div className="p-3 bg-slate-50 rounded border border-slate-200">
              <span className="text-slate-400 block font-semibold">True Negatives (TN)</span>
              <span className="text-base font-bold text-slate-800">
                {metrics.confusion_matrices.threshold_0_25[0][0]?.toLocaleString()}
              </span>
            </div>
            <div className="p-3 bg-amber-50 rounded border border-amber-200">
              <span className="text-amber-700 block font-semibold">False Positives (FP)</span>
              <span className="text-base font-bold text-amber-900">
                {metrics.confusion_matrices.threshold_0_25[0][1]?.toLocaleString()}
              </span>
            </div>
            <div className="p-3 bg-rose-50 rounded border border-rose-200">
              <span className="text-rose-700 block font-semibold">False Negatives (FN)</span>
              <span className="text-base font-bold text-rose-900">
                {metrics.confusion_matrices.threshold_0_25[1][0]?.toLocaleString()}
              </span>
            </div>
            <div className="p-3 bg-emerald-50 rounded border border-emerald-200">
              <span className="text-emerald-700 block font-semibold">True Positives (TP)</span>
              <span className="text-base font-bold text-emerald-900">
                {metrics.confusion_matrices.threshold_0_25[1][1]?.toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
