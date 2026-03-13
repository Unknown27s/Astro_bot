import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// ── Auth ──
export const login = (username, password) =>
  api.post('/auth/login', { username, password });

export const register = (username, password, role, fullName) =>
  api.post('/auth/register', { username, password, role, full_name: fullName });

// ── Chat ──
export const sendChat = (query, userId, username) =>
  api.post('/chat', { query, userId, username });

export const getChatStatus = () => api.get('/chat/status');

// ── Documents ──
export const uploadDocument = (file, uploadedBy) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('uploaded_by', uploadedBy);
  return api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const listDocuments = () => api.get('/documents');

export const deleteDocument = (docId) => api.delete(`/documents/${docId}`);

export const getKnowledgeBaseStats = () => api.get('/documents/stats');

// ── Users ──
export const listUsers = () => api.get('/users');

export const createUser = (username, password, role, fullName) =>
  api.post('/users', { username, password, role, full_name: fullName });

export const toggleUser = (userId, isActive) =>
  api.patch(`/users/${userId}/toggle`, { is_active: isActive });

export const deleteUser = (userId) => api.delete(`/users/${userId}`);

// ── Analytics ──
export const getAnalytics = () => api.get('/analytics');

export const getQueryLogs = (limit = 50) =>
  api.get('/analytics/logs', { params: { limit } });

// ── Health ──
export const getHealth = () => api.get('/health');

export const getProviderStatuses = () => api.get('/health/providers');

// ── Settings ──
export const getSettings = () => api.get('/settings');

export const updateSettings = (settings) => api.put('/settings', settings);

export const testProvider = (provider) =>
  api.post(`/settings/test-provider/${provider}`);

// ── Memory ──
export const getMemoryStats = () => api.get('/memory/stats');

export const deleteMemoryEntry = (memoryId) =>
  api.delete(`/memory/${memoryId}`);

export const runMemoryCleanup = () => api.post('/memory/cleanup');

export const clearAllMemory = () => api.post('/memory/clear');

export default api;
