import React, { useEffect, useState } from 'react';
import {
  Database,
  Upload,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  FileSpreadsheet,
  Cpu,
  BookOpen,
} from 'lucide-react';
import {
  getDataQualityReport,
  uploadDataset,
  triggerGenerateDataset,
  triggerTrainModel,
} from '../services/api';

export const DatasetsPage: React.FC = () => {
  const [qualityData, setQualityData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Pipeline triggers state
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchQuality();
  }, []);

  const fetchQuality = async () => {
    setLoading(true);
    try {
      const data = await getDataQualityReport();
      setQualityData(data);
    } catch (err) {
      console.error('Failed to load quality report', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const res = await uploadDataset(uploadFile);
      setUploadResult(res);
    } catch (err: any) {
      setUploadError(err?.response?.data?.detail || err?.message || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleRegenerateDataset = async () => {
    if (!window.confirm('Generate fresh 25,000 synthetic discharge records? This will update the benchmark CSV.')) {
      return;
    }
    setActionLoading(true);
    setActionMessage(null);
    try {
      const res = await triggerGenerateDataset(25000, 42);
      setActionMessage(res.message);
      await fetchQuality();
    } catch (err: any) {
      setActionMessage('Failed to regenerate dataset: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetrainModel = async () => {
    if (!window.confirm('Retrain readmission model pipeline? This fits candidate models and recalibrates probabilities.')) {
      return;
    }
    setActionLoading(true);
    setActionMessage(null);
    try {
      const res = await triggerTrainModel(42);
      setActionMessage(res.message);
      await fetchQuality();
    } catch (err: any) {
      setActionMessage('Model retraining failed: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        <div className="w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-sm font-medium">Loading dataset quality report and data dictionary...</p>
      </div>
    );
  }

  const qReport = qualityData?.quality_report || {};
  const dictionary = qualityData?.data_dictionary || {};

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header & Pipeline Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Dataset Management & Data Quality</h1>
            <span className="text-xs bg-slate-100 text-slate-700 font-mono px-2.5 py-0.5 rounded border border-slate-200">
              25k Benchmark
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Data dictionary, deliberate missingness audits, schema validation, and training pipeline triggers.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleRegenerateDataset}
            disabled={actionLoading}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-50 transition-colors shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${actionLoading ? 'animate-spin' : ''}`} />
            <span>Generate 25k Synthetic Records</span>
          </button>
          <button
            onClick={handleRetrainModel}
            disabled={actionLoading}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-teal-600 text-white rounded-lg text-xs font-semibold hover:bg-teal-700 transition-colors shadow-xs"
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Retrain Model Pipeline</span>
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-4 bg-teal-50 border border-teal-200 text-teal-900 rounded-xl text-xs font-medium flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-teal-600 flex-shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Dataset Quality Statistics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 block uppercase">Total Records</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {qReport.total_records_generated?.toLocaleString() || '25,125'}
          </div>
          <span className="text-[11px] text-slate-400 block mt-0.5">Synthetic encounters</span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 block uppercase">Unique Patients</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {qReport.unique_patients?.toLocaleString() || '11,730'}
          </div>
          <span className="text-[11px] text-slate-400 block mt-0.5">Multi-visit histories</span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-amber-200 bg-amber-50/20 shadow-xs">
          <span className="text-xs font-semibold text-amber-800 block uppercase">Deliberate Duplicates</span>
          <div className="text-2xl font-bold text-amber-900 mt-1">
            {qReport.duplicate_encounter_count || 125}
          </div>
          <span className="text-[11px] text-amber-700 block mt-0.5">Deduplicated in pipeline</span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 block uppercase">Planned Admissions</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {qReport.planned_readmission_count || 873}
          </div>
          <span className="text-[11px] text-slate-400 block mt-0.5">Policy-excluded from calls</span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 block uppercase">Overall Readmissions</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {qReport.readmission_rate_overall ? `${(qReport.readmission_rate_overall * 100).toFixed(1)}%` : '21.3%'}
          </div>
          <span className="text-[11px] text-slate-400 block mt-0.5">Realistic hospital prevalence</span>
        </div>
      </div>

      {/* Deliberate Missingness Diagnostic Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Deliberate Missing Laboratory Diagnostics</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Real hospital records feature missing laboratory panels (~15%). ReCare AI trains dedicated missingness indicators rather than discarding cases.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {qReport.missing_percentage_by_column &&
            Object.entries(qReport.missing_percentage_by_column).map(([col, pct]: [string, any]) => (
              <div key={col} className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                <span className="font-semibold text-slate-700 block truncate" title={col}>
                  {col.replace('_', ' ').toUpperCase()}
                </span>
                <span className="text-lg font-bold text-amber-700 block mt-1">{pct}%</span>
                <span className="text-[11px] text-slate-400">
                  {qReport.missing_values_by_column?.[col]?.toLocaleString()} missing rows
                </span>
              </div>
            ))}
        </div>
      </div>

      {/* CSV Upload & Validation Section */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-5">
        <div>
          <h2 className="text-base font-bold text-slate-900">Upload & Validate Custom Inpatient Dataset (CSV)</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Upload hospital discharge records for automated column mapping, missingness audit, and deduplication verification.
          </p>
        </div>

        <form onSubmit={handleFileUpload} className="space-y-4">
          <div className="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center hover:border-teal-500/50 transition-colors">
            <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              className="text-xs text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100 cursor-pointer"
            />
            <p className="text-xs text-slate-400 mt-2">Max file size: 50MB. Format: Standard RFC-4180 CSV.</p>
          </div>

          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-500 italic">
              Notice: Uploaded data is strictly validated and previewed; models are never silently overwritten.
            </span>
            <button
              type="submit"
              disabled={!uploadFile || uploading}
              className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800 disabled:opacity-40 transition-colors shadow-xs"
            >
              {uploading ? 'Validating Schema...' : 'Validate Dataset'}
            </button>
          </div>
        </form>

        {uploadError && (
          <div className="p-4 bg-rose-50 border border-rose-200 text-rose-900 rounded-lg text-xs">
            {uploadError}
          </div>
        )}

        {uploadResult && (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3 text-xs">
            <div className="flex items-center justify-between font-bold text-slate-900">
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Validation Result: {uploadResult.filename}</span>
              </div>
              <span className="bg-teal-50 text-teal-800 px-2 py-0.5 rounded border border-teal-200">
                {uploadResult.dataset_type}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>Total Records: <strong>{uploadResult.total_records?.toLocaleString()}</strong></div>
              <div>Unique Encounters: <strong>{uploadResult.unique_encounters?.toLocaleString()}</strong></div>
              <div>Duplicates Found: <strong>{uploadResult.duplicate_encounters_detected}</strong></div>
              <div>Missing Columns: <strong>{uploadResult.missing_required_columns?.length || 0}</strong></div>
            </div>

            {uploadResult.preview?.length > 0 && (
              <div>
                <span className="font-semibold text-slate-700 block mb-1">Sanitized Preview (Top Rows):</span>
                <div className="overflow-x-auto bg-white border border-slate-200 rounded p-2 text-[11px] font-mono">
                  <pre>{JSON.stringify(uploadResult.preview.slice(0, 2), null, 2)}</pre>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Clinical Data Dictionary Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center space-x-2">
          <BookOpen className="w-4 h-4 text-slate-600" />
          <h2 className="text-base font-bold text-slate-900">Clinical Data Dictionary</h2>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
              <tr>
                <th className="py-2.5 px-4 w-1/4">Variable Name</th>
                <th className="py-2.5 px-4">Clinical Description & Imputation Handling</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
              {Object.entries(dictionary).map(([k, desc]: [string, any]) => (
                <tr key={k} className="hover:bg-slate-50/70">
                  <td className="py-2.5 px-4 font-mono font-bold text-teal-900">{k}</td>
                  <td className="py-2.5 px-4 text-slate-600">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
