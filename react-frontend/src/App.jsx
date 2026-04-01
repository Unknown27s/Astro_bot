import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import AdminLayout from './components/AdminLayout';
import DocumentsPage from './pages/admin/DocumentsPage';
import AnalyticsPage from './pages/admin/AnalyticsPage';
import UsersPage from './pages/admin/UsersPage';
import SettingsPage from './pages/admin/SettingsPage';
import HealthPage from './pages/admin/HealthPage';
import MemoryPage from './pages/admin/MemoryPage';
import RateLimitingPage from './pages/admin/RateLimitingPage';

function ProtectedRoute({ children, roles }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/chat" />;
  return children;
}

export default function App() {
  const { user } = useAuth();

  return (
    <>
      <Toaster position="top-right" toastOptions={{
        style: { background: '#1e293b', color: '#f1f5f9', border: '1px solid #334155' }
      }} />
      <Routes>
        <Route path="/login" element={user ? <Navigate to={user.role === 'admin' ? '/admin/documents' : '/chat'} /> : <LoginPage />} />
        <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute roles={['admin']}><AdminLayout /></ProtectedRoute>}>
          <Route index element={<Navigate to="documents" />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="rate-limiting" element={<RateLimitingPage />} />
          <Route path="memory" element={<MemoryPage />} />
          <Route path="health" element={<HealthPage />} />
          <Route path="chat" element={<ChatPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </>
  );
}
