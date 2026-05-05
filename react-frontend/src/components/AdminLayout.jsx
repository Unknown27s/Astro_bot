import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  FileText,
  BarChart3,
  Users,
  Settings,
  Activity,
  MessageSquare,
  LogOut,
  Database,
  MessageCircleQuestion,
  Zap,
  Menu,
  X,
  Shield,
  BookOpen,
  Calendar,
} from 'lucide-react';

const navItems = [
  { to: '/admin/documents', icon: FileText, label: 'Documents' },
  { to: '/admin/student-data', icon: BookOpen, label: 'Student Data' },
  { to: '/admin/timetable', icon: Calendar, label: 'Timetable' },
  { to: '/admin/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/admin/users', icon: Users, label: 'Users' },
  { to: '/admin/settings', icon: Settings, label: 'AI Settings' },
  { to: '/admin/rate-limiting', icon: Zap, label: 'Rate Limiting' },
  { to: '/admin/faq', icon: MessageCircleQuestion, label: 'FAQ' },
  { to: '/admin/memory', icon: Database, label: 'Memory' },
  { to: '/admin/trace-monitor', icon: Activity, label: 'Trace Monitor' },
  { to: '/admin/health', icon: Activity, label: 'Health' },
  { to: '/admin/chat', icon: MessageSquare, label: 'Test Chat' },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 font-astro-body text-slate-100">
      <div className="pointer-events-none absolute inset-0 astro-nebula-bg" />
      <div className="pointer-events-none absolute inset-0 astro-noise-overlay" />

      <button
        type="button"
        onClick={() => setSidebarOpen((open) => !open)}
        className="fixed left-4 top-4 z-50 rounded-xl border border-white/25 bg-slate-950/75 p-2 text-slate-100 backdrop-blur md:hidden"
        aria-label={sidebarOpen ? 'Close admin navigation' : 'Open admin navigation'}
      >
        {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      <div className="relative mx-auto flex min-h-screen w-full max-w-[1600px]">
        <aside
          className={`fixed left-0 top-0 z-40 flex h-screen w-72 flex-col border-r border-white/10 bg-slate-950/65 p-4 backdrop-blur-2xl transition-transform duration-300 md:static md:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
        >
          <div className="astro-glass flex h-full flex-col rounded-2xl border border-white/10">
            <div className="border-b border-white/10 px-4 py-5">
              <div className="flex items-center gap-3">
                <div className="astro-glow-cyan flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-300/80 to-blue-500/80 text-slate-950">
                  <Shield size={20} />
                </div>
                <div>
                  <h2 className="font-astro-headline text-lg font-extrabold tracking-tight text-white">AstroBot Admin</h2>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-200/80">Control Center</p>
                </div>
              </div>
            </div>

            <div className="border-b border-white/10 px-4 py-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-cyan-200/80">Signed In As</p>
              <p className="mt-1 text-sm font-semibold text-slate-100">{user?.username || 'admin'}</p>
              <p className="text-xs text-slate-300/80">{user?.role || 'admin'}</p>
            </div>

            <nav className="astro-scrollbar flex-1 space-y-1 overflow-y-auto px-3 py-3">
              {navItems.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-xl border px-3 py-2.5 text-sm font-semibold transition-all ${isActive
                      ? 'border-cyan-300/70 bg-cyan-300/15 text-white'
                      : 'border-transparent text-slate-200/85 hover:border-white/20 hover:bg-white/5 hover:text-white'
                    }`
                  }
                >
                  <Icon size={16} />
                  {label}
                </NavLink>
              ))}
            </nav>

            <div className="border-t border-white/10 p-3">
              <button
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-rose-300/30 bg-rose-400/10 px-3 py-2 text-sm font-semibold text-rose-100 transition-colors hover:bg-rose-400/20"
                onClick={handleLogout}
                type="button"
              >
                <LogOut size={16} />
                Logout
              </button>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="astro-glass border-b border-white/10 px-5 py-4 md:px-8">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h1 className="font-astro-headline text-xl font-extrabold tracking-tight text-white md:text-2xl">Administration</h1>
                <p className="text-xs uppercase tracking-[0.18em] text-cyan-200/80">Rajalakshmi Institute of Technology</p>
              </div>
              <div className="rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-right">
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-cyan-200/70">Workspace</p>
                <p className="text-sm font-semibold text-slate-100">Live API Panels</p>
              </div>
            </div>
          </header>

          <main className="astro-scrollbar min-h-0 flex-1 overflow-y-auto px-4 py-4 md:px-8 md:py-6">
            <div className="mx-auto w-full max-w-6xl">
              <Outlet />
            </div>
          </main>
        </div>

        {sidebarOpen && (
          <div
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-30 bg-black/60 md:hidden"
          />
        )}
      </div>
    </div>
  );
}
