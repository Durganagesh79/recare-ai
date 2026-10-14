import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Search,
  Filter,
  X,
  ChevronLeft,
  ChevronRight,
  Activity,
  AlertTriangle,
  FileText,
  Clock,
  Sparkles,
  Stethoscope,
  ArrowUpDown,
} from 'lucide-react';
import { getPatients, getPatientDetail, PatientListItem } from '../services/api';

export const PatientRegistry: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [patients, setPatients] = useState<PatientListItem[]>([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  // Filters
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');
  const [riskCategory, setRiskCategory] = useState('');
  const [conditionName, setConditionName] = useState('');
  const [sortBy, setSortBy] = useState('predicted_risk');
  const [sortOrder, setSortOrder] = useState('desc');

  // Selected Patient Drawer State
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [patientDetail, setPatientDetail] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    fetchPatientsList();
  }, [page, riskCategory, conditionName, sortBy, sortOrder]);

  const fetchPatientsList = async () => {
    setLoading(true);
    try {
      const res = await getPatients({
        search: searchTerm || undefined,
        risk_category: riskCategory || undefined,
        condition_name: conditionName || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: 15,
      });
      setPatients(res.items);
      setTotalRecords(res.total_records);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load patient registry', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchPatientsList();
  };

  const openPatientDetail = async (patientId: string) => {
    setSelectedPatientId(patientId);
    setDetailLoading(true);
    try {
      const detail = await getPatientDetail(patientId);
      setPatientDetail(detail);
    } catch (err) {
      console.error('Failed to load patient detail', err);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Patient Encounter Registry</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Comprehensive repository of discharge encounters, calibrated risk assessments, and clinical drivers.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Patient ID (e.g. PT-10042), Encounter ID, or Condition..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-semibold hover:bg-slate-800 transition-colors shadow-xs"
          >
            Search Registry
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 text-xs">
          <div className="flex items-center space-x-1.5 text-slate-500 font-medium">
            <Filter className="w-3.5 h-3.5" />
            <span>Filters:</span>
          </div>

          {/* Risk Filter */}
          <select
            value={riskCategory}
            onChange={(e) => {
              setRiskCategory(e.target.value);
              setPage(1);
            }}
            aria-label="Filter by Risk Category"
            className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-slate-700 font-medium focus:outline-none"
          >
            <option value="">All Risk Tiers</option>
            <option value="High Risk">High Risk (≥30%)</option>
            <option value="Moderate Risk">Moderate Risk (15-30%)</option>
            <option value="Low Risk">Low Risk (&lt;15%)</option>
          </select>

          {/* Condition Filter */}
          <select
            value={conditionName}
            onChange={(e) => {
              setConditionName(e.target.value);
              setPage(1);
            }}
            aria-label="Filter by Clinical Condition"
            className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-slate-700 font-medium focus:outline-none"
          >
            <option value="">All Clinical Conditions</option>
            <option value="Heart Failure">Heart Failure</option>
            <option value="COPD / Chronic Lower Respiratory">COPD</option>
            <option value="Acute Myocardial Infarction">Acute Myocardial Infarction</option>
            <option value="Pneumonia">Pneumonia</option>
            <option value="Diabetes with Complications">Diabetes with Complications</option>
            <option value="Sepsis">Sepsis</option>
            <option value="Cerebrovascular Disease / Stroke">Stroke</option>
          </select>

          {/* Sort By */}
          <div className="ml-auto flex items-center space-x-2">
            <span className="text-slate-500 font-medium">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              aria-label="Sort Registry Records By"
              className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-slate-700 font-medium focus:outline-none"
            >
              <option value="predicted_risk">Predicted Risk</option>
              <option value="discharge_date">Discharge Date</option>
              <option value="encounter_id">Encounter ID</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="p-1.5 bg-slate-50 border border-slate-200 rounded-md text-slate-600 hover:bg-slate-100"
              title="Toggle Sort Direction"
              aria-label="Toggle Sort Direction"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Patients Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase font-semibold tracking-wider">
                <th className="py-3 px-4">Patient ID</th>
                <th className="py-3 px-4">Encounter ID</th>
                <th className="py-3 px-4">Demographics</th>
                <th className="py-3 px-4">Condition & Code</th>
                <th className="py-3 px-4">Stay & Meds</th>
                <th className="py-3 px-4">Discharge Disposition</th>
                <th className="py-3 px-4">Predicted Risk</th>
                <th className="py-3 px-4">Observed Label</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    Loading encounters...
                  </td>
                </tr>
              ) : patients.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    No encounters match the current filter criteria.
                  </td>
                </tr>
              ) : (
                patients.map((p) => {
                  const riskBadge =
                    p.risk_category === 'High Risk'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : p.risk_category === 'Moderate Risk'
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200';

                  return (
                    <tr
                      key={p.encounter_id}
                      onClick={() => openPatientDetail(p.patient_id)}
                      className="hover:bg-teal-50/40 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-4 font-mono font-bold text-teal-800">{p.patient_id}</td>
                      <td className="py-3 px-4 font-mono text-slate-500">{p.encounter_id}</td>
                      <td className="py-3 px-4">
                        <span className="font-medium text-slate-900">{p.age}yo</span> {p.sex}
                        <span className="text-[11px] text-slate-400 block">{p.payer_type}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-semibold text-slate-900 block">{p.condition_name}</span>
                        <span className="text-[11px] font-mono text-slate-500">{p.primary_diagnosis_code}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span>{p.length_of_stay} days</span>
                        <span className="text-[11px] text-slate-500 block">{p.medication_count} meds</span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 font-medium">{p.discharge_disposition}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold border ${riskBadge}`}>
                          {p.risk_percentage !== null ? `${p.risk_percentage}%` : 'Unscored'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {p.observed_readmission === 1 ? (
                          <span className="text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                            Readmitted
                          </span>
                        ) : p.observed_readmission === 0 ? (
                          <span className="text-[11px] text-slate-600 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                            Not Readmitted
                          </span>
                        ) : (
                          <span className="text-[11px] text-slate-400 italic">Unlabeled / Future</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            openPatientDetail(p.patient_id);
                          }}
                          className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded hover:bg-slate-200 font-medium"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>
            Showing <strong className="font-medium text-slate-700">{(page - 1) * 15 + 1}</strong> to{' '}
            <strong className="font-medium text-slate-700">{Math.min(page * 15, totalRecords)}</strong> of{' '}
            <strong className="font-medium text-slate-700">{totalRecords.toLocaleString()}</strong> encounters
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="p-1.5 rounded border border-slate-200 disabled:opacity-40 hover:bg-slate-50"
              aria-label="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-medium">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded border border-slate-200 disabled:opacity-40 hover:bg-slate-50"
              aria-label="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Individual Patient Clinical Drawer Modal */}
      {selectedPatientId && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col overflow-y-auto animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-xl font-bold text-slate-900">Patient File: {selectedPatientId}</h2>
                  <span className="text-xs bg-slate-200 text-slate-700 font-mono px-2 py-0.5 rounded">
                    Synthetic Encounter Record
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Multi-encounter history and clinical decision support</p>
              </div>
              <button
                onClick={() => setSelectedPatientId(null)}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
                aria-label="Close Patient Drawer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="p-6 flex-1 space-y-6">
              {detailLoading ? (
                <div className="py-20 text-center text-slate-400">Loading comprehensive patient record...</div>
              ) : patientDetail ? (
                <>
                  {/* Demographics Card */}
                  <div className="grid grid-cols-3 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
                    <div>
                      <span className="text-slate-400 block uppercase font-semibold">Age / Sex</span>
                      <span className="text-slate-900 font-bold text-sm">
                        {patientDetail.demographics?.age}yo {patientDetail.demographics?.sex}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block uppercase font-semibold">Coverage / Payer</span>
                      <span className="text-slate-900 font-bold text-sm">{patientDetail.demographics?.payer_type}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block uppercase font-semibold">Encounters On Record</span>
                      <span className="text-slate-900 font-bold text-sm">
                        {patientDetail.total_encounters_on_record} Inpatient Visits
                      </span>
                    </div>
                  </div>

                  {/* Active AI Risk Prediction Card */}
                  {patientDetail.ai_decision_support?.active_prediction && (
                    <div className="bg-gradient-to-br from-teal-500/5 to-blue-500/5 p-5 rounded-xl border border-teal-500/30 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Activity className="w-5 h-5 text-teal-600" />
                          <h3 className="font-bold text-slate-900 text-sm">Calibrated 30-Day Readmission Risk</h3>
                        </div>
                        <span className="text-lg font-black text-rose-600 bg-rose-50 border border-rose-200 px-3 py-1 rounded-lg">
                          {patientDetail.ai_decision_support.active_prediction.risk_percentage}%
                        </span>
                      </div>
                      <p className="text-xs text-slate-600">
                        Classified as <strong>{patientDetail.ai_decision_support.active_prediction.risk_category}</strong> based on clinical severity, prior acute utilization velocity, and discharge complexity.
                      </p>
                    </div>
                  )}

                  {/* Tailored Intervention Recommendations */}
                  {patientDetail.ai_decision_support?.intervention_recommendations && (
                    <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
                      <div className="flex items-center space-x-2">
                        <Sparkles className="w-4 h-4 text-teal-600" />
                        <h3 className="font-bold text-slate-900 text-sm">Recommended Care Interventions</h3>
                      </div>
                      <div className="bg-teal-50/70 p-3.5 rounded-lg border border-teal-200/80">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold text-teal-900">
                            {patientDetail.ai_decision_support.intervention_recommendations.primary_recommendation}
                          </span>
                          <span className="text-[10px] bg-teal-100 text-teal-800 font-bold px-2 py-0.5 rounded">
                            {patientDetail.ai_decision_support.intervention_recommendations.primary_priority} Priority
                          </span>
                        </div>
                        <p className="text-xs text-slate-700 mb-2">
                          {patientDetail.ai_decision_support.intervention_recommendations.primary_rationale}
                        </p>
                        <div className="text-xs bg-white p-2.5 rounded border border-teal-200 font-mono text-slate-800">
                          <strong>Action Plan:</strong> {patientDetail.ai_decision_support.intervention_recommendations.action_plan}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Top Actionable Risk Drivers */}
                  {patientDetail.ai_decision_support?.active_prediction?.top_drivers?.length > 0 && (
                    <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
                      <h3 className="font-bold text-slate-900 text-sm">Actionable Risk Drivers & Suggested Nurse Review</h3>
                      <div className="space-y-2.5">
                        {patientDetail.ai_decision_support.active_prediction.top_drivers.map((driver: any, idx: number) => (
                          <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                            <div className="flex items-center justify-between font-semibold text-slate-900 mb-0.5">
                              <span>{driver.feature_label}</span>
                              <span className={driver.direction === 'positive' ? 'text-rose-600' : 'text-emerald-600'}>
                                {driver.impact}
                              </span>
                            </div>
                            <p className="text-slate-500 mb-1">Observed Value: <span className="font-mono text-slate-700">{driver.value}</span></p>
                            <p className="text-slate-700 font-medium bg-white p-2 rounded border border-slate-200/80">
                              💡 {driver.actionable_suggestion}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Multi-Encounter Longitudinal History */}
                  <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
                    <h3 className="font-bold text-slate-900 text-sm">Longitudinal Encounter History ({patientDetail.all_encounters.length})</h3>
                    <div className="space-y-2">
                      {patientDetail.all_encounters.map((enc: any, i: number) => (
                        <div key={enc.encounter_id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs flex justify-between items-center">
                          <div>
                            <span className="font-mono font-bold text-slate-900">{enc.encounter_id}</span>
                            <span className="text-slate-500 block">{enc.condition_name} ({enc.primary_diagnosis_code})</span>
                            <span className="text-[11px] text-slate-400">Discharged: {enc.discharge_date} • {enc.discharge_disposition}</span>
                          </div>
                          <div className="text-right">
                            <span className="font-bold text-slate-900 block">{enc.prediction?.risk_percentage || 'N/A'}% Risk</span>
                            <span className="text-[11px] text-slate-500">LOS: {enc.length_of_stay}d</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
