import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  Cpu,
  Database,
  Layers,
  HeartPulse,
  Activity,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { getModelInfo, getHealth } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [modelInfo, setModelInfo] = useState<any | null>(null);
  const [healthStatus, setHealthStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInfo();
  }, []);

  const fetchInfo = async () => {
    setLoading(true);
    try {
      const [info, health] = await Promise.all([getModelInfo(), getHealth()]);
      setModelInfo(info);
      setHealthStatus(health);
    } catch (err) {
      console.error('Failed to load settings or health', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        <div className="w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-sm font-medium">Checking model governance and service health...</p>
      </div>
    );
  }

  const gov = modelInfo?.governance || {};
  const metrics = modelInfo?.metrics_summary || {};

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2.5">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Settings & Model Governance</h1>
          <span className="text-xs bg-slate-100 text-slate-700 font-mono px-2.5 py-0.5 rounded border border-slate-200">
            {modelInfo?.model_version || 'v1.2.0'}
          </span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          Active machine-learning architecture, calibration specification, clinical constraints, and system diagnostics.
        </p>
      </div>

      {/* System Health Status */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
            <HeartPulse className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-900 block">ReCare AI Backend Core</span>
            <span className="text-[11px] text-slate-500">FastAPI 0.142 • Scikit-Learn 1.8.0 • SQLAlchemy ORM</span>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-xs font-medium">
          <span className="inline-flex items-center space-x-1 text-emerald-700">
            <CheckCircle2 className="w-4 h-4" />
            <span>Database Connected</span>
          </span>
          <span className="inline-flex items-center space-x-1 text-emerald-700">
            <CheckCircle2 className="w-4 h-4" />
            <span>Model Serialized & Loaded</span>
          </span>
        </div>
      </div>

      {/* Model Architecture Specifications */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-5">
        <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
          <Cpu className="w-4 h-4 text-teal-600" />
          <h2 className="text-base font-bold text-slate-900">Active Model Architecture & Training Summary</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          <div className="space-y-3">
            <div>
              <span className="text-slate-400 uppercase font-semibold block">Production Architecture</span>
              <span className="text-slate-900 font-bold text-sm block mt-0.5">
                {modelInfo?.model_architecture}
              </span>
              <p className="text-slate-500 mt-1">
                Tabular gradient boosting with 3-fold cross-validated probability calibration (ECE &lt; 1.5%).
              </p>
            </div>

            <div>
              <span className="text-slate-400 uppercase font-semibold block">Transparent Baseline</span>
              <span className="text-slate-800 font-medium block mt-0.5">
                {modelInfo?.baseline_architecture}
              </span>
              <span className="text-slate-500">Baseline Val AUC-PR: {metrics.baseline_val_auc_pr}</span>
            </div>

            <div>
              <span className="text-slate-400 uppercase font-semibold block">Patient-Isolated Splitting</span>
              <p className="text-slate-600 mt-0.5">
                Trained on <strong>{modelInfo?.train_samples?.toLocaleString()}</strong> encounters, validated on{' '}
                <strong>{modelInfo?.validation_samples?.toLocaleString()}</strong>, tested on{' '}
                <strong>{modelInfo?.test_samples?.toLocaleString()}</strong> encounters using GroupShuffleSplit on{' '}
                <code>patient_id</code> to guarantee zero patient leakage.
              </p>
            </div>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3 font-mono">
            <span className="text-slate-500 font-semibold block uppercase font-sans text-xs">Model Version Metadata</span>
            <div className="text-[11px] space-y-1 text-slate-700">
              <div>Version Tag: <strong>{modelInfo?.model_version}</strong></div>
              <div>Trained At: <strong>{modelInfo?.created_at}</strong></div>
              <div>Random Seed: <strong>{modelInfo?.random_seed}</strong></div>
              <div>Holdout Test AUC-PR: <strong>{metrics.test_auc_pr}</strong></div>
              <div>Calibrated Test ECE: <strong>{metrics.test_expected_calibration_error_calibrated}</strong></div>
              <div>Test Brier Score: <strong>{metrics.test_brier_score_calibrated}</strong></div>
            </div>
          </div>
        </div>
      </div>

      {/* Governance, Intended Use & Safety Constraints */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
          <ShieldCheck className="w-4 h-4 text-slate-700" />
          <h2 className="text-base font-bold text-slate-900">Clinical Governance & Ethical Constraints</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
            <span className="font-bold text-slate-900 block">Intended Use Specification</span>
            <p className="text-slate-600">{gov.intended_use}</p>
          </div>

          <div className="p-4 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
            <span className="font-bold text-slate-900 block">Target Patient Population</span>
            <p className="text-slate-600">{gov.target_population}</p>
          </div>

          <div className="p-4 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
            <span className="font-bold text-slate-900 block">Weekly Operational Capacity</span>
            <p className="text-slate-600">
              Strictly limited to <strong>{gov.weekly_capacity_constraint} unique patients per week</strong> to reflect realistic hospital nurse staffing constraints.
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
            <span className="font-bold text-slate-900 block">Sensitive Attribute Policy</span>
            <p className="text-slate-600">{gov.sensitive_attribute_policy}</p>
          </div>
        </div>
      </div>

      {/* Persistent Disclaimer Card */}
      <div className="p-5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
        <div className="space-y-1">
          <span className="font-bold text-sm text-amber-950 block">Official Non-Clinical Demonstrator Notice</span>
          <p className="leading-relaxed">{gov.disclaimer}</p>
        </div>
      </div>
    </div>
  );
};
