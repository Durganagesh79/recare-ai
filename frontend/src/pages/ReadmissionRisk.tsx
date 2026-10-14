import React, { useState } from 'react';
import { Activity, Sparkles, CheckCircle2, AlertTriangle, Play, RefreshCw } from 'lucide-react';
import { predictSingle } from '../services/api';

export const ReadmissionRisk: React.FC = () => {
  const [formData, setFormData] = useState({
    encounter_id: 'ENC-MANUAL-01',
    patient_id: 'PT-MANUAL-01',
    age: 69,
    sex: 'Male',
    payer_type: 'Medicare',
    primary_diagnosis_code: 'I50.9',
    secondary_diagnoses_count: 5,
    length_of_stay: 6,
    prior_admissions: 3,
    prior_admissions_6m: 2,
    num_procedures: 1,
    discharge_disposition: 'Home Health Care',
    medication_count: 14,
    hemoglobin: 10.4,
    serum_creatinine: 2.1,
    sodium: 134.0,
    bun: 28.0,
    glucose: 145.0,
    follow_up_scheduled: false,
    is_planned_readmission: false,
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleRunPrediction = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await predictSingle(formData);
      setResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to score encounter.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2.5">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Interactive Readmission Risk Scorer</h1>
          <span className="text-xs bg-teal-50 text-teal-800 border border-teal-300 font-bold px-2.5 py-0.5 rounded-full">
            Real-Time Inference
          </span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          Evaluate 30-day readmission risk on a new patient encounter without requiring ground-truth outcomes.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Form */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h2 className="text-base font-bold text-slate-900">Encounter Characteristics</h2>
            <button
              type="button"
              onClick={() =>
                setFormData({
                  encounter_id: `ENC-${Math.floor(100000 + Math.random() * 90000)}`,
                  patient_id: `PT-${Math.floor(10000 + Math.random() * 9000)}`,
                  age: 74,
                  sex: 'Female',
                  payer_type: 'Medicaid',
                  primary_diagnosis_code: 'J44.1',
                  secondary_diagnoses_count: 6,
                  length_of_stay: 8,
                  prior_admissions: 4,
                  prior_admissions_6m: 3,
                  num_procedures: 0,
                  discharge_disposition: 'Skilled Nursing Facility (SNF)',
                  medication_count: 16,
                  hemoglobin: 9.8,
                  serum_creatinine: 2.3,
                  sodium: 131.0,
                  bun: 32.0,
                  glucose: 160.0,
                  follow_up_scheduled: false,
                  is_planned_readmission: false,
                })
              }
              className="text-xs text-teal-700 hover:text-teal-800 font-semibold"
            >
              Load High-Risk Sample
            </button>
          </div>

          <form onSubmit={handleRunPrediction} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Age</label>
                <input
                  type="number"
                  value={formData.age}
                  onChange={(e) => handleInputChange('age', Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Sex</label>
                <select
                  value={formData.sex}
                  onChange={(e) => handleInputChange('sex', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other/Unknown">Other/Unknown</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Payer Coverage</label>
                <select
                  value={formData.payer_type}
                  onChange={(e) => handleInputChange('payer_type', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                >
                  <option value="Medicare">Medicare</option>
                  <option value="Medicaid">Medicaid</option>
                  <option value="Commercial">Commercial</option>
                  <option value="Uninsured/Self-pay">Uninsured/Self-pay</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Primary Diagnosis Code</label>
                <input
                  type="text"
                  value={formData.primary_diagnosis_code}
                  onChange={(e) => handleInputChange('primary_diagnosis_code', e.target.value)}
                  placeholder="e.g. I50.9, 428.0"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-mono"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Length of Stay (days)</label>
                <input
                  type="number"
                  value={formData.length_of_stay}
                  onChange={(e) => handleInputChange('length_of_stay', Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Medication Count</label>
                <input
                  type="number"
                  value={formData.medication_count}
                  onChange={(e) => handleInputChange('medication_count', Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Prior Admissions (6m)</label>
                <input
                  type="number"
                  value={formData.prior_admissions_6m}
                  onChange={(e) => handleInputChange('prior_admissions_6m', Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Total Lifetime Prior Admissions</label>
                <input
                  type="number"
                  value={formData.prior_admissions}
                  onChange={(e) => handleInputChange('prior_admissions', Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Discharge Disposition</label>
                <select
                  value={formData.discharge_disposition}
                  onChange={(e) => handleInputChange('discharge_disposition', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                >
                  <option value="Home">Home</option>
                  <option value="Home Health Care">Home Health Care</option>
                  <option value="Skilled Nursing Facility (SNF)">Skilled Nursing Facility (SNF)</option>
                  <option value="Inpatient Rehabilitation">Inpatient Rehabilitation</option>
                  <option value="Against Medical Advice (AMA)">Against Medical Advice (AMA)</option>
                </select>
              </div>
            </div>

            {/* Labs Row */}
            <div className="pt-2 border-t border-slate-100">
              <span className="text-xs font-bold text-slate-600 block mb-2">Laboratory Values (optional, can be empty)</span>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                <div>
                  <label className="block text-slate-500 mb-0.5">Creatinine (mg/dL)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.serum_creatinine || ''}
                    onChange={(e) => handleInputChange('serum_creatinine', e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded"
                  />
                </div>
                <div>
                  <label className="block text-slate-500 mb-0.5">Sodium (mEq/L)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={formData.sodium || ''}
                    onChange={(e) => handleInputChange('sodium', e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded"
                  />
                </div>
                <div>
                  <label className="block text-slate-500 mb-0.5">Hemoglobin (g/dL)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.hemoglobin || ''}
                    onChange={(e) => handleInputChange('hemoglobin', e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded"
                  />
                </div>
                <div>
                  <label className="block text-slate-500 mb-0.5">BUN (mg/dL)</label>
                  <input
                    type="number"
                    step="1"
                    value={formData.bun || ''}
                    onChange={(e) => handleInputChange('bun', e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded"
                  />
                </div>
                <div>
                  <label className="block text-slate-500 mb-0.5">Glucose (mg/dL)</label>
                  <input
                    type="number"
                    step="1"
                    value={formData.glucose || ''}
                    onChange={(e) => handleInputChange('glucose', e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-6 pt-3 text-xs">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.follow_up_scheduled}
                  onChange={(e) => handleInputChange('follow_up_scheduled', e.target.checked)}
                  className="rounded text-teal-600 focus:ring-teal-500"
                />
                <span className="text-slate-700 font-medium">Follow-Up Appointment Scheduled at Discharge</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_planned_readmission}
                  onChange={(e) => handleInputChange('is_planned_readmission', e.target.checked)}
                  className="rounded text-teal-600 focus:ring-teal-500"
                />
                <span className="text-slate-700 font-medium">Intentionally Planned Admission (Elective)</span>
              </label>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-teal-600 text-white rounded-lg text-sm font-bold hover:bg-teal-700 transition-colors shadow-xs flex items-center justify-center space-x-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Scoring Encounter with Calibrated Model...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" />
                    <span>Run Calibrated Readmission Risk Prediction</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Prediction Results Display */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 pb-3 border-b border-slate-100">
              Prediction Output & Clinical Drivers
            </h2>

            {result ? (
              <div className="space-y-4 mt-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-1">
                  <span className="text-xs text-slate-500 font-medium uppercase tracking-wider block">
                    Calibrated Readmission Probability
                  </span>
                  <div className="text-4xl font-black text-rose-600 tracking-tight">
                    {result.risk_percentage}%
                  </div>
                  <span className="inline-block px-2.5 py-0.5 rounded text-xs font-bold bg-rose-100 text-rose-800 mt-1">
                    {result.risk_category}
                  </span>
                </div>

                {result.top_contributing_features?.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-bold text-slate-700 block">Top Contributing Drivers:</span>
                    {result.top_contributing_features.map((driver: any, idx: number) => (
                      <div key={idx} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                        <div className="flex justify-between font-semibold text-slate-900">
                          <span>{driver.feature_label}</span>
                          <span className={driver.direction === 'positive' ? 'text-rose-600' : 'text-emerald-600'}>
                            {driver.impact}
                          </span>
                        </div>
                        <p className="text-slate-600 mt-1 text-[11px] leading-tight font-medium">
                          💡 {driver.actionable_suggestion}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="py-20 text-center text-slate-400 text-xs">
                Submit an encounter record to generate calibrated risk probability and actionable drivers.
              </div>
            )}
          </div>

          <div className="text-[11px] text-slate-400 border-t border-slate-100 pt-3">
            Active Engine: <strong>v1.2.0 Calibrated HistGB</strong>
          </div>
        </div>
      </div>
    </div>
  );
};
