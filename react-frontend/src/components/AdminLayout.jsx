import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FileText, BarChart3, Users, Settings, Activity, MessageSquare, LogOut, Database, Zap } from 'lucide-react';

const navItems = [
  { to: '/admin/documents', icon: FileText, label: 'Documents' },
  { to: '/admin/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/admin/users', icon: Users, label: 'Users' },
  { to: '/admin/settings', icon: Settings, label: 'AI Settings' },
  { to: '/admin/rate-limiting', icon: Zap, label: 'Rate Limiting' },
  { to: '/admin/memory', icon: Database, label: 'Memory' },
  { to: '/admin/health', icon: Activity, label: 'Health' },
  { to: '/admin/chat', icon: MessageSquare, label: 'Test Chat' },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h2>🤖 AstroBot</h2>
          <p>Admin Dashboard</p>
        </div>
        <div style={{ padding: '0 4px 12px', fontSize: 13, color: 'var(--text-muted)' }}>
          🔑 {user?.username}
        </div>
        <nav className="sidebar-nav">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="divider" />
        <button className="sidebar-link" onClick={handleLogout}>
          <LogOut size={18} /> Logout
        </button>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
