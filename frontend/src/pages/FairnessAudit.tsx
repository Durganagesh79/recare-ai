import React, { useEffect, useState } from 'react';
import {
  Scale,
  ShieldCheck,
  AlertTriangle,
  Users,
  CheckCircle2,
  Info,
} from 'lucide-react';
import { getFairnessReport } from '../services/api';

export const FairnessAudit: React.FC = () => {
  const [auditData, setAuditData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAttribute, setSelectedAttribute] = useState<'age_group' | 'sex' | 'payer_type'>('age_group');

  useEffect(() => {
    fetchFairness();
  }, []);

  const fetchFairness = async () => {
    setLoading(true);
    try {
      const data = await getFairnessReport();
      setAuditData(data);
    } catch (err) {
      console.error('Failed to load fairness audit', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        <div className="w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-sm font-medium">Auditing demographic calibration and disparate impact metrics...</p>
      </div>
    );
  }

  const auditedGroups = auditData?.audited_attributes?.[selectedAttribute] || [];

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2.5">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Algorithmic Fairness & Bias Audit</h1>
          <span className="text-xs bg-emerald-50 text-emerald-800 border border-emerald-300 font-bold px-2.5 py-0.5 rounded-full">
            Equity Monitored
          </span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          Evaluating calibration parity, false-negative disparities, and call-list representation across demographic cohorts.
        </p>
      </div>

      {/* Disparity Alerts if any */}
      {auditData?.key_disparities_identified?.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-900 space-y-2">
          <div className="flex items-center space-x-2 font-bold">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Representation Observation Flag</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-amber-800">
            {auditData.key_disparities_identified.map((disp: string, i: number) => (
              <li key={i}>{disp}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Attribute Tabs */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-5">
        <div className="flex items-center space-x-3 border-b border-slate-100 pb-4">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Audited Demographic Strata:</span>
          <button
            onClick={() => setSelectedAttribute('age_group')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              selectedAttribute === 'age_group'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Age Brackets
          </button>
          <button
            onClick={() => setSelectedAttribute('sex')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              selectedAttribute === 'sex'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Sex
          </button>
          <button
            onClick={() => setSelectedAttribute('payer_type')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              selectedAttribute === 'payer_type'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Payer / Insurance Type
          </button>
        </div>

        {/* Subgroup Metrics Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase font-semibold tracking-wider">
                <th className="py-3 px-4">Subgroup</th>
                <th className="py-3 px-4">Sample Size</th>
                <th className="py-3 px-4">Prevalence</th>
                <th className="py-3 px-4">AUC-PR</th>
                <th className="py-3 px-4">Calibration Error (ECE)</th>
                <th className="py-3 px-4">False Positive Rate (FPR)</th>
                <th className="py-3 px-4">False Negative Rate (FNR)</th>
                <th className="py-3 px-4">Share of Top-50 Call List</th>
                <th className="py-3 px-4">Audit Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {auditedGroups.map((group: any) => (
                <tr key={group.subgroup} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-bold text-slate-900">{group.subgroup}</td>
                  <td className="py-3 px-4">
                    <span>{group.sample_size?.toLocaleString()}</span>
                    {group.population_share && (
                      <span className="text-[11px] text-slate-400 block">
                        ({Math.round(group.population_share * 100)}% of cohort)
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-medium">
                    {group.prevalence ? `${(group.prevalence * 100).toFixed(1)}%` : 'N/A'}
                  </td>
                  <td className="py-3 px-4 font-mono font-bold text-indigo-900">
                    {group.auc_pr ? group.auc_pr.toFixed(4) : '—'}
                  </td>
                  <td className="py-3 px-4 font-mono">
                    {group.expected_calibration_error !== null && group.expected_calibration_error !== undefined
                      ? `${(group.expected_calibration_error * 100).toFixed(2)}%`
                      : '—'}
                  </td>
                  <td className="py-3 px-4">
                    {group.fpr_at_screening_threshold !== null && group.fpr_at_screening_threshold !== undefined
                      ? `${(group.fpr_at_screening_threshold * 100).toFixed(1)}%`
                      : '—'}
                  </td>
                  <td className="py-3 px-4">
                    {group.fnr_at_screening_threshold !== null && group.fnr_at_screening_threshold !== undefined
                      ? `${(group.fnr_at_screening_threshold * 100).toFixed(1)}%`
                      : '—'}
                  </td>
                  <td className="py-3 px-4 font-semibold text-teal-800">
                    {group.count_in_top_50} patients ({Math.round((group.selection_rate_in_call_list || 0) * 100)}%)
                  </td>
                  <td className="py-3 px-4">
                    {group.status === 'Evaluated' ? (
                      <span className="inline-flex items-center space-x-1 text-emerald-700 font-semibold text-[11px]">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Verified</span>
                      </span>
                    ) : (
                      <span className="text-amber-700 font-semibold text-[11px] bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        {group.status}
                      </span>
                    )}
                    {group.uncertainty_warning && (
                      <span className="text-[10px] text-slate-400 block mt-0.5">{group.uncertainty_warning}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Practical Bias Mitigation Analysis */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-5 h-5 text-teal-600" />
          <h2 className="text-base font-bold text-slate-900">Practical Bias Mitigation & Clinical Governance</h2>
        </div>
        <p className="text-xs text-slate-500">
          Rather than relying on superficial threshold adjustments, ReCare AI implements multi-tiered clinical safeguards.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          {auditData?.mitigation_analysis?.map((mit: any, idx: number) => (
            <div key={idx} className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 text-sm">{mit.strategy}</span>
                <span className="text-[10px] bg-teal-100 text-teal-800 px-2 py-0.5 rounded font-semibold">
                  {mit.status}
                </span>
              </div>
              <p className="text-slate-600">{mit.description}</p>
              <div className="p-2 bg-white rounded border border-slate-200 text-teal-900 font-medium">
                <strong>Impact Observed:</strong> {mit.impact_observed}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Persistent Ethical Notice */}
      <div className="p-4 bg-slate-100 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start space-x-3">
        <Info className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
        <p>{auditData?.ethical_disclaimer}</p>
      </div>
    </div>
  );
};
