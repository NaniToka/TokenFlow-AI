import axios from 'axios';

const API_BASE_URL = import.meta.env.PROD ? '/api/v1' : 'http://127.0.0.1:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const compressPrompt = async (payload) => {
  const response = await apiClient.post('/compress', payload);
  return response.data;
};

export const getStats = async () => {
  const response = await apiClient.get('/stats');
  return response.data;
};

export const resetStats = async () => {
  const response = await apiClient.post('/stats/reset');
  return response.data;
};

export default apiClient;
