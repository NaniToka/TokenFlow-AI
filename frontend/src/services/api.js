import axios from 'axios';

const API_BASE_URL = import.meta.env.PROD ? '/api/v1' : 'http://127.0.0.1:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 25000,
});

export const compressPrompt = async (payload) => {
  const response = await apiClient.post('/compress', payload);
  return response.data;
};

export const batchCompressPrompts = async (requests) => {
  const response = await apiClient.post('/compress/batch', { requests });
  return response.data;
};

export const asyncCompressPrompt = async (payload) => {
  const response = await apiClient.post('/compress/async', payload);
  return response.data;
};

export const getTaskStatus = async (taskId) => {
  const response = await apiClient.get(`/tasks/${taskId}`);
  return response.data;
};

export const inspectRanking = async (payload) => {
  const response = await apiClient.post('/rank/inspect', payload);
  return response.data;
};

export const evaluateCompression = async (history, responsePayload) => {
  const response = await apiClient.post('/evaluate', {
    history,
    response: responsePayload,
  });
  return response.data;
};

export const indexRagDocument = async (payload) => {
  const response = await apiClient.post('/rag/index', payload);
  return response.data;
};

export const queryRagStore = async (payload) => {
  const response = await apiClient.post('/rag/query', payload);
  return response.data;
};

export const clearRagStore = async () => {
  const response = await apiClient.delete('/rag/clear');
  return response.data;
};

export const sanitizeText = async (text, redactPii = true) => {
  const response = await apiClient.post('/sanitize', { text, redact_pii: redactPii });
  return response.data;
};

export const getSupportedModels = async () => {
  const response = await apiClient.get('/models');
  return response.data;
};

export const getTelemetry = async () => {
  const response = await apiClient.get('/telemetry');
  return response.data;
};

export const clearSemanticCache = async () => {
  const response = await apiClient.post('/cache/clear');
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

export const getHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

// =========================================================================
// TokenFlow AI v3.0 Enterprise Endpoints
// =========================================================================

export const compressOpenAIChat = async (payload) => {
  const response = await apiClient.post('/chat/compress', payload);
  return response.data;
};

export const uploadRagFile = async (payload) => {
  const response = await apiClient.post('/rag/upload', payload);
  return response.data;
};

export const runNeedleTest = async (payload) => {
  const response = await apiClient.post('/evaluate/needle', payload);
  return response.data;
};

export const runABExperiment = async (payload) => {
  const response = await apiClient.post('/experiments/compare', payload);
  return response.data;
};

export const scanGuardrails = async (text, redactPii = true) => {
  const response = await apiClient.post('/guard/scan', { text, redact_pii: redactPii });
  return response.data;
};

export const getAuditLogs = async (limit = 50) => {
  const response = await apiClient.get('/logs', { params: { limit } });
  return response.data;
};

export const clearAuditLogs = async () => {
  const response = await apiClient.delete('/logs');
  return response.data;
};

export const getSdkSnippets = async (params = {}) => {
  const response = await apiClient.get('/sdk-snippets', { params });
  return response.data;
};

export const getCircuitBreaker = async () => {
  const response = await apiClient.get('/circuit-breaker');
  return response.data;
};

export const resetCircuitBreaker = async () => {
  const response = await apiClient.post('/circuit-breaker/reset');
  return response.data;
};

/**
 * Streams real-time compression stage events over Server-Sent Events (SSE).
 */
export const streamCompressSSE = async (payload, onStage) => {
  const res = await fetch(`${API_BASE_URL}/compress/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok || !res.body) {
    throw new Error(`SSE stream request failed with status ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let finalResult = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split('\n\n');
    buffer = frames.pop() || '';

    for (const frame of frames) {
      const dataLine = frame
        .split('\n')
        .find((line) => line.startsWith('data:'));
      if (!dataLine) continue;

      const parsed = JSON.parse(dataLine.slice(5).trim());
      if (onStage) onStage(parsed);
      if (parsed.stage === 'complete' && parsed.result) {
        finalResult = parsed.result;
      }
    }
  }

  if (!finalResult) {
    throw new Error('SSE stream completed without returning a result payload.');
  }
  return finalResult;
};

/**
 * Streams real-time compression stage events over WebSocket.
 */
export const streamCompressWS = (payload, onStage) => {
  return new Promise((resolve, reject) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.PROD ? window.location.host : '127.0.0.1:8000';
    const ws = new WebSocket(`${protocol}//${host}/api/v1/ws/compress`);

    ws.onopen = () => {
      ws.send(JSON.stringify(payload));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (onStage) onStage(msg);
        if (msg.stage === 'complete') {
          ws.close();
          resolve(msg.result);
        } else if (msg.stage === 'error') {
          ws.close();
          reject(new Error(msg.message || 'WebSocket compression error'));
        }
      } catch (err) {
        ws.close();
        reject(err);
      }
    };

    ws.onerror = () => {
      reject(new Error('WebSocket connection error — falling back to REST recommended.'));
    };
  });
};

export default apiClient;
