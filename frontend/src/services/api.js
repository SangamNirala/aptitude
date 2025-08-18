import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API,
  timeout: 30000,
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    throw error;
  }
);

// =============================================================================
// SCRAPING MANAGEMENT APIS
// =============================================================================

export const fetchScrapingJobs = async () => {
  return await apiClient.get('/scraping/jobs');
};

export const createScrapingJob = async (jobData) => {
  return await apiClient.post('/scraping/jobs', jobData);
};

export const getScrapingJob = async (jobId) => {
  return await apiClient.get(`/scraping/jobs/${jobId}`);
};

export const startScrapingJob = async (jobId) => {
  return await apiClient.put(`/scraping/jobs/${jobId}/start`);
};

export const stopScrapingJob = async (jobId) => {
  return await apiClient.put(`/scraping/jobs/${jobId}/stop`);
};

export const pauseScrapingJob = async (jobId) => {
  return await apiClient.put(`/scraping/jobs/${jobId}/pause`);
};

export const deleteScrapingJob = async (jobId) => {
  return await apiClient.delete(`/scraping/jobs/${jobId}`);
};

export const fetchScrapingSources = async () => {
  return await apiClient.get('/scraping/sources');
};

export const fetchQueueStatus = async () => {
  return await apiClient.get('/scraping/queue-status');
};

export const fetchSystemStatus = async () => {
  return await apiClient.get('/scraping/system-status');
};

// =============================================================================
// ANALYTICS & MONITORING APIS  
// =============================================================================

export const fetchSourceAnalytics = async () => {
  return await apiClient.get('/scraping/analytics/sources');
};

export const fetchJobAnalytics = async () => {
  return await apiClient.get('/scraping/analytics/jobs');
};

export const fetchPerformanceMetrics = async () => {
  return await apiClient.get('/scraping/analytics/performance');
};

export const fetchQualityAnalytics = async () => {
  return await apiClient.get('/scraping/analytics/quality');
};

export const fetchSystemHealthAnalytics = async () => {
  return await apiClient.get('/scraping/analytics/system-health');
};

export const fetchTrendAnalysis = async () => {
  return await apiClient.get('/scraping/analytics/trends');
};

export const fetchRealTimeMonitoring = async () => {
  return await apiClient.get('/scraping/analytics/monitoring/real-time');
};

export const fetchAnalyticsReports = async () => {
  return await apiClient.get('/scraping/analytics/reports');
};

// =============================================================================
// PRODUCTION MONITORING APIS
// =============================================================================

export const fetchProductionHealth = async () => {
  return await apiClient.get('/production/health');
};

export const fetchProductionHealthComponent = async (component) => {
  return await apiClient.get(`/production/health/${component}`);
};

export const fetchProductionMetrics = async () => {
  return await apiClient.get('/production/metrics');
};

export const fetchProductionStatus = async () => {
  return await apiClient.get('/production/status');
};

export const fetchErrorsDashboard = async () => {
  return await apiClient.get('/production/errors/dashboard');
};

export const runPerformanceTest = async () => {
  return await apiClient.post('/production/performance/test');
};

export const validateProductionConfig = async () => {
  return await apiClient.get('/production/config/validation');
};

export const runAllHealthChecks = async () => {
  return await apiClient.get('/production/health-checks/all');
};

// =============================================================================
// QUESTIONS MANAGEMENT APIS
// =============================================================================

export const fetchQuestions = async (filters = {}) => {
  const params = new URLSearchParams();
  
  if (filters.category) params.append('category', filters.category);
  if (filters.difficulty) params.append('difficulty', filters.difficulty);
  if (filters.limit) params.append('limit', filters.limit);
  if (filters.skip) params.append('skip', filters.skip);
  if (filters.min_quality_score) params.append('min_quality_score', filters.min_quality_score);
  
  const queryString = params.toString();
  return await apiClient.get(`/questions/filtered${queryString ? `?${queryString}` : ''}`);
};

export const fetchQuestionById = async (questionId) => {
  return await apiClient.get(`/questions/${questionId}`);
};

export const fetchQuestionsByCategory = async (category, limit = 10) => {
  return await fetchQuestions({ category, limit });
};

export const fetchLogicalQuestions = async (limit = 10, difficulty = null) => {
  const filters = { category: 'logical', limit };
  if (difficulty) filters.difficulty = difficulty;
  return await fetchQuestions(filters);
};

export const fetchQuantitativeQuestions = async (limit = 10, difficulty = null) => {
  const filters = { category: 'quantitative', limit };
  if (difficulty) filters.difficulty = difficulty;
  return await fetchQuestions(filters);
};

export const fetchVerbalQuestions = async (limit = 10, difficulty = null) => {
  const filters = { category: 'verbal', limit };
  if (difficulty) filters.difficulty = difficulty;
  return await fetchQuestions(filters);
};

// =============================================================================
// AI SERVICES APIS
// =============================================================================

export const generateQuestions = async (requestData) => {
  return await apiClient.post('/ai/generate-questions', requestData);
};

export const analyzeQuestions = async (requestData) => {
  return await apiClient.post('/ai/analyze-questions', requestData);
};

export const getInstantFeedback = async (requestData) => {
  return await apiClient.post('/ai/instant-feedback', requestData);
};

// =============================================================================
// PERFORMANCE OPTIMIZATION APIS
// =============================================================================

export const fetchPerformanceHealth = async () => {
  return await apiClient.get('/performance/health');
};

export const fetchPerformanceStatus = async () => {
  return await apiClient.get('/performance/status');
};

export const initializePerformance = async () => {
  return await apiClient.post('/performance/initialize');
};

export const optimizeDatabase = async () => {
  return await apiClient.post('/performance/optimize/database');
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

export const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleString();
};

export const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'healthy':
    case 'running':
    case 'completed':
    case 'success':
      return 'green';
    case 'warning':
    case 'paused':
      return 'yellow';
    case 'critical':
    case 'failed':
    case 'error':
      return 'red';
    default:
      return 'blue';
  }
};