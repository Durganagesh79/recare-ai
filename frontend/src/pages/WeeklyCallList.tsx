import React, { useEffect, useState } from 'react';
import {
  PhoneCall,
  Download,
  FileText,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Clock,
  PhoneForwarded,
  XCircle,
  HelpCircle,
  RefreshCw,
  Save,
} from 'lucide-react';
import {
  getCurrentCallList,
  generateCallList,
  updateCallListEntry,
  CallListResponse,
  CallListPatient,
  API_BASE_URL,
} from '../services/api';

export const WeeklyCallList: React.FC = () => {
  const [callList, setCallList] = useState<CallListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [activeMode, setActiveMode] = useState<'risk_first' | 'expected_benefit'>('risk_first');
  const [statusUpdating, setStatusUpdating] = useState<number | null>(null);

  // Editable notes state { entry_id: noteText }
  const [notesState, setNotesState] = useState<Record<number, string>>({});

  useEffect(() => {
    fetchCallList();
  }, []);

  const fetchCallList = async () => {
    setLoading(true);
    try {
      const data = await getCurrentCallList();
      setCallList(data);
      if (data.ranking_mode === 'expected_benefit') {
        setActiveMode('expected_benefit');
      } else {
        setActiveMode('risk_first');
      }
      // Populate notes
      const initialNotes: Record<number, string> = {};
      data.selected_patients.forEach((p) => {
        if (p.entry_id) {
          initialNotes[p.entry_id] = p.follow_up_notes || '';
        }
      });
      setNotesState(initialNotes);
    } catch (err) {
      console.error('Failed to load call list', err);
    } finally {
      setLoading(false);
    }
  };

  const handleModeSwitch = async (newMode: 'risk_first' | 'expected_benefit') => {
    setActiveMode(newMode);
    setGenerating(true);
    try {
      const data = await generateCallList({
        mode: newMode,
        max_capacity: 50,
        filter_planned_readmissions: true,
      });
      setCallList(data);
      const initialNotes: Record<number, string> = {};
      data.selected_patients.forEach((p) => {
        if (p.entry_id) {
          initialNotes[p.entry_id] = p.follow_up_notes || '';
        }
      });
      setNotesState(initialNotes);
    } catch (err) {
      console.error('Failed to regenerate call list', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleStatusChange = async (entryId: number | undefined, newStatus: string) => {
    if (!entryId) return;
    setStatusUpdating(entryId);
    try {
      await updateCallListEntry(entryId, { contact_status: newStatus });
      // Update local state
      if (callList) {
        setCallList({
          ...callList,
          selected_patients: callList.selected_patients.map((p) =>
            p.entry_id === entryId ? { ...p, contact_status: newStatus } : p
          ),
        });
      }
    } catch (err) {
      console.error('Failed to update contact status', err);
    } finally {
      setStatusUpdating(null);
    }
  };

  const handleSaveNotes = async (entryId: number | undefined) => {
    if (!entryId) return;
    const noteText = notesState[entryId] || '';
    setStatusUpdating(entryId);
    try {
      await updateCallListEntry(entryId, { follow_up_notes: noteText });
    } catch (err) {
      console.error('Failed to save notes', err);
    } finally {
      setStatusUpdating(null);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        <div className="w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-sm font-medium">Loading weekly 50-patient care coordination roster...</p>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header and Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Monday Morning Care Coordination Brief</h1>
            <span className="text-xs bg-teal-50 text-teal-800 border border-teal-300 font-bold px-2.5 py-0.5 rounded-full">
              Capacity: 50 Unique Pts
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Period: <strong>{callList?.reporting_period}</strong> | Call List ID: <code className="text-xs">{callList?.call_list_id}</code>
          </p>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center space-x-3">
          <a
            href={`${API_BASE_URL}/api/reports/call-list.csv`}
            download
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-50 transition-colors shadow-xs"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export CSV</span>
          </a>
          <a
            href={`${API_BASE_URL}/api/reports/call-list.pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800 transition-colors shadow-xs"
          >
            <FileText className="w-3.5 h-3.5 text-teal-400" />
            <span>Download Care Brief PDF</span>
          </a>
        </div>
      </div>

      {/* Optimizer Mode Switcher & Summary Card */}
      <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Intervention Ranking Strategy
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleModeSwitch('risk_first')}
                disabled={generating}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeMode === 'risk_first'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Mode A: Risk-First Baseline
              </button>
              <button
                onClick={() => handleModeSwitch('expected_benefit')}
                disabled={generating}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1.5 ${
                  activeMode === 'expected_benefit'
                    ? 'bg-teal-700 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Mode B: Expected Benefit</span>
              </button>
              {generating && <RefreshCw className="w-4 h-4 text-teal-600 animate-spin ml-2" />}
            </div>
          </div>

          <div className="text-xs text-slate-500 max-w-md">
            {activeMode === 'expected_benefit' ? (
              <span className="text-teal-900 bg-teal-50 border border-teal-200 p-2 rounded block">
                <strong>Mode B Active:</strong> Ranks patients by expected avoided readmissions: <code className="text-[11px]">P(readmit) × Actionability RRR</code>. Prioritizes patients with addressable clinical risk.
              </span>
            ) : (
              <span className="text-slate-700 bg-slate-50 border border-slate-200 p-2 rounded block">
                <strong>Mode A Active:</strong> Transparent baseline ranking strictly by calibrated readmission risk probability.
              </span>
            )}
          </div>
        </div>

        {/* Optimizer Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-1">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 font-medium block">Selected Capacity</span>
            <span className="text-lg font-bold text-slate-900">
              {callList?.selected_count} / {callList?.capacity_limit} Patients
            </span>
            <span className="text-[11px] text-teal-700 block mt-0.5">Strict Unique Patient Rule</span>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 font-medium block">Average Selected Risk</span>
            <span className="text-lg font-bold text-slate-900">
              {Math.round((callList?.summary?.average_selected_risk || 0) * 100)}%
            </span>
            <span className="text-[11px] text-slate-500 block mt-0.5">
              vs Cohort Avg: {Math.round((callList?.summary?.cohort_average_risk || 0) * 100)}%
            </span>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 font-medium block">Risk Enrichment</span>
            <span className="text-lg font-bold text-teal-700">
              {callList?.summary?.risk_enrichment_ratio?.toFixed(1)}x Lift
            </span>
            <span className="text-[11px] text-slate-500 block mt-0.5">Over unprioritized baseline</span>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 font-medium block">Est. Readmissions Averted</span>
            <span className="text-lg font-bold text-emerald-700">
              ~{callList?.summary?.estimated_readmissions_averted_illustrative?.toFixed(1)}
            </span>
            <span className="text-[11px] text-slate-400 block mt-0.5 italic">Illustrative literature scenario</span>
          </div>
        </div>
      </div>

      {/* Prioritized 50-Patient Call List Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase font-semibold tracking-wider">
                <th className="py-3 px-3">Rank</th>
                <th className="py-3 px-3">Patient / Encounter</th>
                <th className="py-3 px-3">Demographics</th>
                <th className="py-3 px-3">Condition & Disposition</th>
                <th className="py-3 px-3">Risk & Benefit</th>
                <th className="py-3 px-3">Recommended Intervention</th>
                <th className="py-3 px-3">Contact Status</th>
                <th className="py-3 px-3">Follow-Up Clinical Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {callList?.selected_patients.map((p) => (
                <tr key={p.encounter_id} className="hover:bg-slate-50/70 transition-colors">
                  {/* Rank */}
                  <td className="py-3 px-3 font-bold text-slate-900">#{p.rank}</td>

                  {/* Patient & Encounter */}
                  <td className="py-3 px-3 font-mono">
                    <span className="font-bold text-teal-900 block">{p.patient_id}</span>
                    <span className="text-[11px] text-slate-400 block">{p.encounter_id}</span>
                  </td>

                  {/* Demographics */}
                  <td className="py-3 px-3">
                    <span className="font-medium text-slate-900">{p.age}yo {p.sex}</span>
                    <span className="text-[11px] text-slate-500 block">{p.payer_type}</span>
                  </td>

                  {/* Condition */}
                  <td className="py-3 px-3">
                    <span className="font-semibold text-slate-900 block">{p.condition_name}</span>
                    <span className="text-[11px] text-slate-500 block">{p.discharge_disposition}</span>
                  </td>

                  {/* Risk & Benefit */}
                  <td className="py-3 px-3">
                    <span className="inline-block px-2 py-0.5 rounded text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                      {p.risk_percentage}% Risk
                    </span>
                    <span className="text-[11px] font-semibold text-emerald-700 block mt-0.5">
                      +{p.expected_benefit_percentage}% Benefit
                    </span>
                  </td>

                  {/* Recommended Intervention */}
                  <td className="py-3 px-3 max-w-xs">
                    <span className="font-bold text-slate-900 block">{p.recommended_intervention}</span>
                    <span className="text-[11px] text-slate-500 block line-clamp-2" title={p.intervention_action_plan}>
                      {p.intervention_action_plan}
                    </span>
                    <span className="text-[10px] text-teal-700 bg-teal-50 px-1.5 py-0.2 rounded font-medium border border-teal-200 inline-block mt-1">
                      {p.intervention_priority} Priority
                    </span>
                  </td>

                  {/* Contact Status Dropdown */}
                  <td className="py-3 px-3">
                    <select
                      value={p.contact_status}
                      onChange={(e) => handleStatusChange(p.entry_id, e.target.value)}
                      disabled={statusUpdating === p.entry_id}
                      aria-label={`Contact status for patient ${p.patient_id}`}
                      className="px-2 py-1 bg-white border border-slate-200 rounded text-xs font-semibold focus:outline-none"
                    >
                      <option value="Pending">🕒 Pending</option>
                      <option value="Attempted">📞 Attempted</option>
                      <option value="Connected">✅ Connected</option>
                      <option value="Declined">❌ Declined</option>
                    </select>
                  </td>

                  {/* Notes Field */}
                  <td className="py-3 px-3">
                    <div className="flex items-center space-x-1.5">
                      <input
                        type="text"
                        placeholder="Nurse notes..."
                        value={notesState[p.entry_id || 0] || ''}
                        onChange={(e) =>
                          setNotesState({
                            ...notesState,
                            [p.entry_id || 0]: e.target.value,
                          })
                        }
                        className="w-36 px-2 py-1 text-xs bg-slate-50 border border-slate-200 rounded focus:outline-none focus:bg-white"
                      />
                      <button
                        onClick={() => handleSaveNotes(p.entry_id)}
                        disabled={statusUpdating === p.entry_id}
                        title="Save note"
                        aria-label={`Save note for patient ${p.patient_id}`}
                        className="p-1 text-slate-500 hover:text-teal-700 hover:bg-slate-100 rounded"
                      >
                        <Save className="w-3.5 h-3.5" />
                      </button>
                    </div>
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
