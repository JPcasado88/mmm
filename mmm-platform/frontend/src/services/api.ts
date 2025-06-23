import axios from 'axios';

// Try to auto-detect backend URL if not set
const API_BASE_URL = process.env.REACT_APP_API_URL || 
  (window.location.hostname.includes('railway.app') 
    ? `https://${window.location.hostname.replace('-fe-', '-')}`  // Assumes backend has same prefix
    : 'http://localhost:8000');

console.log('API Base URL:', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.config?.url, error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

export interface Channel {
  name: string;
  spend: number;
  revenue: number;
  conversions: number;
  roas: number;
  clicks?: number;
  impressions?: number;
}

export interface OverviewMetrics {
  period: {
    start: string;
    end: string;
  };
  total_spend: number;
  total_revenue: number;
  roas: number;
  total_conversions: number;
  channels: Channel[];
  period_comparison: {
    spend_change: { value: number; percentage: number };
    revenue_change: { value: number; percentage: number };
    roas_change: { value: number; percentage: number };
  };
}

export interface ChannelPerformance {
  channel: string;
  period: {
    start: string;
    end: string;
  };
  metrics: {
    total_spend: number;
    total_revenue: number;
    roas: number;
    avg_daily_spend: number;
    optimal_daily_spend: number;
    current_daily_spend: number;
    opportunity: string;
  };
  time_series: {
    daily: Array<{
      date: string;
      spend: number;
      revenue: number;
      conversions: number;
    }>;
    weekly: Array<{
      week: string;
      spend: number;
      revenue: number;
      conversions: number;
    }>;
  };
  best_performing_days: Array<{
    date: string;
    roas: number;
    revenue: number;
  }>;
}

export interface OptimizationResult {
  total_budget: number;
  optimized_allocation: Record<string, number>;
  projected_revenue: number;
  current_revenue: number;
  revenue_lift: number;
  roi_improvement: number;
  recommendations: Array<{
    channel: string;
    action: string;
    current_spend: number;
    recommended_spend: number;
    change_amount: number;
    change_percentage: number;
    priority: string;
    message: string;
  }>;
}

export interface AttributionModel {
  id: string;
  name: string;
  description: string;
}

export interface AttributionResult {
  channel: string;
  attributed_conversions: number;
  attributed_revenue: number;
  percentage: number;
}

export interface DimishingReturnsData {
  [channel: string]: {
    saturation_point: number;
    current_spend: number;
    efficiency_status: string;
    marginal_returns_curve: Array<{
      spend: number;
      marginal_roas: number;
    }>;
  };
}

class APIService {
  async getOverviewMetrics(startDate: string, endDate: string): Promise<OverviewMetrics> {
    const response = await api.get('/api/metrics/overview', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  async getChannelPerformance(channel: string, startDate: string, endDate: string): Promise<ChannelPerformance> {
    const response = await api.get(`/api/channels/${channel}/performance`, {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  async getChannelTrends(channel: string, days: number = 30) {
    const response = await api.get(`/api/channels/${channel}/trends`, {
      params: { days },
    });
    return response.data;
  }

  async optimizeBudget(totalBudget: number, constraints?: Record<string, any>): Promise<OptimizationResult> {
    const response = await api.post('/api/optimize', {
      total_budget: totalBudget,
      constraints,
    });
    return response.data;
  }

  async simulateScenarios(scenarios: Array<{ name: string; total_budget: number; constraints?: any }>) {
    const response = await api.post('/api/optimize/scenarios', {
      scenarios,
    });
    return response.data;
  }

  async getDiminishingReturns(): Promise<DimishingReturnsData> {
    const response = await api.get('/api/optimize/diminishing-returns');
    return response.data;
  }

  async getAttributionModels(): Promise<{ models: AttributionModel[] }> {
    const response = await api.get('/api/attribution/models');
    return response.data;
  }

  async calculateAttribution(startDate: string, endDate: string, model: string = 'linear') {
    const response = await api.get('/api/attribution/calculate', {
      params: { start_date: startDate, end_date: endDate, model },
    });
    return response.data;
  }

  async compareAttributionModels(startDate: string, endDate: string) {
    const response = await api.get('/api/attribution/compare', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  async checkHealth() {
    const response = await api.get('/api/health');
    return response.data;
  }
}

export default new APIService();