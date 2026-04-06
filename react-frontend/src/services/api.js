import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Separate axios instance for file uploads (without default JSON header)
const fileApi = axios.create({
  baseURL: '/api',
});

// ── Auth ──
export const login = (username, password) =>
  api.post('/auth/login', { username, password });

export const register = (username, password, role, fullName) =>
  api.post('/auth/register', { username, password, role, full_name: fullName });

// ── Chat ──
export const sendChat = (query, userId, username) =>
  api.post('/chat', { query, userId, username });

export const sendAudioMessage = (audioBlob, userId, username) => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'audio.webm');
  formData.append('user_id', userId);
  formData.append('username', username);
  return fileApi.post('/chat/audio', formData);
};

export const getChatStatus = () => api.get('/chat/status');

// ── Announcements ──
export const getAnnouncements = (limit = 50) => api.get('/announcements', { params: { limit } });

export const deleteAnnouncement = (id, userId, userRole) =>
  api.delete(`/announcements/${id}`, { headers: { 'X-User-ID': userId, 'X-User-Role': userRole } });

// ── Suggestions / Autocomplete ──
export const getSuggestions = (query, userId) =>
  api.get('/suggestions', { params: { q: query, user_id: userId } });

// ── Documents ──
export const uploadDocument = (file, uploadedBy) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('uploaded_by', uploadedBy);
  // Use fileApi instance which doesn't have Content-Type: application/json header
  return fileApi.post('/documents/upload', formData);
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

// ── Rate Limiting (Admin) ──
export const getRateLimits = () => api.get('/admin/rate-limits');

export const updateRateLimit = (endpoint, limitRequests, limitWindowSeconds, enabled = true) =>
  api.put(`/admin/rate-limits/${endpoint}`, { limit_requests: limitRequests, limit_window_seconds: limitWindowSeconds, enabled });

export const toggleRateLimit = (endpoint, enabled) =>
  api.patch(`/admin/rate-limits/${endpoint}/toggle`, { enabled });

export const resetRateLimits = () => api.post('/admin/rate-limits/reset');

export default api;
