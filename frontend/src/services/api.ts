import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Automatic fallback between port 8000 and 8001
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (
      !config._retry &&
      error.message &&
      (error.message.includes('Network Error') || error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK')
    ) {
      config._retry = true;
      if (config.baseURL?.includes('8000')) {
        config.baseURL = 'http://127.0.0.1:8001';
        return api(config);
      } else if (config.baseURL?.includes('8001')) {
        config.baseURL = 'http://127.0.0.1:8000';
        return api(config);
      }
    }
    return Promise.reject(error);
  }
);

export interface DashboardSummary {
  status: string;
  kpi: {
    total_encounters: number;
    unique_patients: number;
    predicted_high_risk: number;
    observed_readmission_rate: number;
    weekly_call_list_count: number;
    weekly_capacity_limit: number;
    average_predicted_risk: number;
    model_auc_pr: number;
    model_recall_at_50: number;
    model_precision_at_50: number;
    model_calibration_error: number;
    model_brier_score: number;
  };
  charts: {
    risk_distribution: { name: string; count: number; color: string }[];
    condition_distribution: { condition: string; total_encounters: number }[];
    age_distribution: { age_group: string; patient_count: number; average_risk_percentage: number }[];
  };
  data_quality_indicators: {
    missing_lab_encounters: number;
    missing_lab_percentage: number;
    planned_readmissions_flagged: number;
  };
  this_weeks_care_priorities: Array<{
    rank: number;
    patient_id: string;
    encounter_id: string;
    predicted_risk_probability: number;
    risk_percentage: number;
    expected_benefit_percentage: number;
    recommended_intervention: string;
    intervention_priority: string;
    contact_status: string;
    action_plan: string;
  }>;
}

export interface PatientListItem {
  encounter_id: string;
  patient_id: string;
  age: number | null;
  sex: string | null;
  payer_type: string | null;
  condition_name: string | null;
  primary_diagnosis_code: string | null;
  discharge_disposition: string | null;
  discharge_date: string | null;
  length_of_stay: number;
  medication_count: number;
  prior_admissions_6m: number;
  is_planned_readmission: boolean;
  predicted_risk_probability: number | null;
  risk_percentage: number | null;
  risk_category: string;
  observed_readmission: number | null;
}

export interface CallListPatient {
  entry_id?: number;
  rank: number;
  patient_id: string;
  encounter_id: string;
  age: number | null;
  sex: string;
  payer_type: string;
  condition_name: string;
  primary_diagnosis_code: string;
  discharge_disposition: string;
  discharge_date: string;
  predicted_risk_probability: number;
  risk_percentage: number;
  expected_benefit: number;
  expected_benefit_percentage: number;
  recommended_intervention: string;
  intervention_priority: string;
  intervention_action_plan: string;
  contact_status: string;
  follow_up_notes: string;
  selection_rationale: string;
  key_risk_drivers?: Array<{
    feature: string;
    feature_label: string;
    value: string;
    impact: string;
    direction: string;
    actionable_suggestion: string;
  }>;
}

export interface CallListResponse {
  call_list_id: string;
  reporting_period: string;
  ranking_mode: string;
  mode_description: string;
  capacity_limit: number;
  selected_count: number;
  remaining_capacity: number;
  summary: {
    average_selected_risk?: number;
    cohort_average_risk?: number;
    risk_enrichment_ratio?: number;
    estimated_readmissions_averted_illustrative?: number;
  };
  selected_patients: CallListPatient[];
}

export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const resp = await api.get('/api/dashboard/summary');
  return resp.data;
};

export const getPatients = async (params: Record<string, any>) => {
  const resp = await api.get('/api/patients', { params });
  return resp.data;
};

export const getPatientDetail = async (patientId: string) => {
  const resp = await api.get(`/api/patients/${patientId}`);
  return resp.data;
};

export const getCurrentCallList = async (): Promise<CallListResponse> => {
  const resp = await api.get('/api/call-list/current');
  return resp.data;
};

export const generateCallList = async (payload: { mode: string; max_capacity: number; filter_planned_readmissions: boolean }): Promise<CallListResponse> => {
  const resp = await api.post('/api/call-list/generate', payload);
  return resp.data;
};

export const updateCallListEntry = async (entryId: number, payload: { contact_status?: string; follow_up_notes?: string }) => {
  const resp = await api.patch(`/api/call-list/entries/${entryId}`, payload);
  return resp.data;
};

export const getEvaluationMetrics = async () => {
  const resp = await api.get('/api/evaluation/metrics');
  return resp.data;
};

export const getFairnessReport = async () => {
  const resp = await api.get('/api/fairness/report');
  return resp.data;
};

export const getImpactAnalysis = async (cohortSize: number = 50, avgRisk: number = 0.42) => {
  const resp = await api.get('/api/reports/impact-analysis', {
    params: { cohort_size: cohortSize, avg_risk: avgRisk },
  });
  return resp.data;
};

export const getDataQualityReport = async () => {
  const resp = await api.get('/api/datasets/quality');
  return resp.data;
};

export const uploadDataset = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const resp = await api.post('/api/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return resp.data;
};

export const triggerGenerateDataset = async (records: number = 25000, seed: number = 42) => {
  const resp = await api.post('/api/datasets/generate', null, {
    params: { records, seed },
  });
  return resp.data;
};

export const triggerTrainModel = async (seed: number = 42) => {
  const resp = await api.post('/api/datasets/train', null, {
    params: { seed },
  });
  return resp.data;
};

export const getModelInfo = async () => {
  const resp = await api.get('/api/model/info');
  return resp.data;
};

export const predictSingle = async (encounterData: any) => {
  const resp = await api.post('/api/predictions', encounterData);
  return resp.data;
};

export const getHealth = async () => {
  const resp = await api.get('/health');
  return resp.data;
};
