import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

export interface CovidData {
  dates: string[];
  confirmed: number[];
  deaths: number[];
  cured: number[];
}

export interface PredictionData {
  dates: string[];
  predictions: number[];
  lower_bound: number[];
  upper_bound: number[];
}

export interface GrowthRateData {
  dates: string[];
  growth_rate: number[];
}

export interface RecoveryRateData {
  dates: string[];
  recovery_rate: number[];
}

export interface StateComparisonData {
  [key: string]: {
    dates: string[];
    confirmed: number[];
  };
}

const api = {
  getStates: async (): Promise<string[]> => {
    const response = await axios.get(`${API_BASE_URL}/states`);
    return response.data.states;
  },

  getData: async (state?: string, startDate?: string, endDate?: string): Promise<CovidData> => {
    const params = new URLSearchParams();
    if (state) params.append('state', state);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await axios.get(`${API_BASE_URL}/data`, { params });
    return response.data;
  },

  getPredictions: async (state?: string, days: number = 30): Promise<PredictionData> => {
    const params = new URLSearchParams();
    if (state) params.append('state', state);
    params.append('days', days.toString());
    
    const response = await axios.get(`${API_BASE_URL}/predictions`, { params });
    return response.data;
  },

  getGrowthRate: async (state?: string): Promise<GrowthRateData> => {
    const params = new URLSearchParams();
    if (state) params.append('state', state);
    
    const response = await axios.get(`${API_BASE_URL}/growth-rate`, { params });
    return response.data;
  },

  getRecoveryRate: async (state?: string): Promise<RecoveryRateData> => {
    const params = new URLSearchParams();
    if (state) params.append('state', state);
    
    const response = await axios.get(`${API_BASE_URL}/recovery-rate`, { params });
    return response.data;
  },

  getStateComparison: async (states: string[]): Promise<StateComparisonData> => {
    const params = new URLSearchParams();
    states.forEach(state => params.append('states[]', state));
    
    const response = await axios.get(`${API_BASE_URL}/state-comparison`, { params });
    return response.data;
  }
};

export default api; 