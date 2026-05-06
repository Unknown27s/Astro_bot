import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  X,
  Layout,
  FileText,
  Users,
  Zap,
  Settings,
  LogOut,
  BookOpen,
  Moon,
  Sun,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { useState, useEffect } from 'react';

const menuItems = [
  { id: 'dashboard', label: 'Dashboard', icon: Layout, href: '/admin/dashboard' },
  { id: 'documents', label: 'Documents', icon: FileText, href: '/admin/documents' },
  { id: 'student-data', label: 'Student Data', icon: BookOpen, href: '/admin/student-data' },
  { id: 'timetable', label: 'Timetable', icon: FileText, href: '/admin/timetable' },
  { id: 'users', label: 'Users', icon: Users, href: '/admin/users' },
  { id: 'rate-limiting', label: 'Rate Limiting', icon: Zap, href: '/admin/rate-limiting' },
  { id: 'settings', label: 'Settings', icon: Settings, href: '/admin/settings' },
];

// Tiny star dots rendered in the sidebar background
function Stars() {
  const dots = Array.from({ length: 28 }, (_, i) => ({
    id: i,
    top: `${Math.round((i * 37 + 11) % 100)}%`,
    left: `${Math.round((i * 61 + 23) % 100)}%`,
    size: i % 5 === 0 ? 2 : 1,
    opacity: 0.12 + (i % 4) * 0.06,
  }));
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden>
      {dots.map((d) => (
        <span
          key={d.id}
          style={{
            position: 'absolute',
            top: d.top,
            left: d.left,
            width: d.size,
            height: d.size,
            borderRadius: '50%',
            background: '#c4b5fd',
            opacity: d.opacity,
          }}
        />
      ))}
    </div>
  );
}

export default function AdminSidebar({ isOpen, onClose }) {
  const navigate = useNavigate();
  const location = useLocation();

  const [isDark, setIsDark] = useState(
    () => (localStorage.getItem('astro_theme') || 'dark') === 'dark'
  );

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.remove('light');
      root.classList.add('dark');
      localStorage.setItem('astro_theme', 'dark');
    } else {
      root.classList.remove('dark');
      root.classList.add('light');
      localStorage.setItem('astro_theme', 'light');
    }
  }, [isDark]);

  const handleLogout = () => {
    localStorage.removeItem('astrobot_user');
    localStorage.removeItem('token');
    navigate('/login');
  };

  const sidebarContent = (
    <aside
      style={{
        width: 256,
        background: 'linear-gradient(175deg, #0f0c29 0%, #1a1040 50%, #0f0c29 100%)',
        borderRight: '1px solid rgba(139,92,246,0.18)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'relative',
        overflow: 'hidden',
        fontFamily: "'DM Sans', system-ui, sans-serif",
      }}
    >
      {/* Ambient glow top-right */}
      <div
        aria-hidden
        style={{
          position: 'absolute',
          top: -60,
          right: -60,
          width: 200,
          height: 200,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139,92,246,0.22) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />
      {/* Ambient glow bottom-left */}
      <div
        aria-hidden
        style={{
          position: 'absolute',
          bottom: 60,
          left: -40,
          width: 160,
          height: 160,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99,102,241,0.18) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      <Stars />

      {/* ── Header ── */}
      <div
        style={{
          padding: '24px 20px 20px',
          borderBottom: '1px solid rgba(139,92,246,0.15)',
          position: 'relative',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {/* Orbit icon */}
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 16px rgba(124,58,237,0.55)',
                flexShrink: 0,
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round">
                <circle cx="12" cy="12" r="3" />
                <ellipse cx="12" cy="12" rx="10" ry="4" />
                <line x1="12" y1="2" x2="12" y2="22" />
              </svg>
            </div>
            <div>
              <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#fff', letterSpacing: '-0.3px', lineHeight: 1 }}>
                AstroBot
              </h1>
              <p style={{ margin: 0, fontSize: 10, color: 'rgba(196,181,253,0.6)', letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: 3 }}>
                Admin Panel
              </p>
            </div>
          </div>

          {/* Mobile close */}
          <button
            onClick={onClose}
            aria-label="Close sidebar"
            className="md:hidden"
            style={{
              background: 'rgba(255,255,255,0.07)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8,
              padding: 4,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'rgba(255,255,255,0.7)',
              transition: 'background 0.15s',
            }}
          >
            <X size={15} />
          </button>
        </div>

        {/* Theme toggle */}
        <button
          onClick={() => setIsDark((v) => !v)}
          aria-label="Toggle theme"
          style={{
            marginTop: 14,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(139,92,246,0.25)',
            borderRadius: 8,
            padding: '6px 12px',
            cursor: 'pointer',
            width: '100%',
            color: 'rgba(196,181,253,0.85)',
            fontSize: 12,
            fontWeight: 500,
            letterSpacing: '0.02em',
            transition: 'background 0.15s, border-color 0.15s',
          }}
        >
          {isDark
            ? <><Sun size={13} style={{ color: '#fbbf24' }} /> Light Mode</>
            : <><Moon size={13} style={{ color: '#818cf8' }} /> Dark Mode</>
          }
        </button>
      </div>

      {/* ── Navigation ── */}
      <nav
        style={{
          flex: 1,
          padding: '14px 12px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {/* Section label */}
        <p style={{
          fontSize: 10,
          fontWeight: 600,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: 'rgba(139,92,246,0.5)',
          padding: '6px 12px 4px',
          margin: 0,
        }}>
          Navigation
        </p>

        {menuItems.map((item, i) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;

          return (
            <motion.button
              key={item.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04, duration: 0.25 }}
              onClick={() => { navigate(item.href); onClose?.(); }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: 11,
                padding: '9px 12px',
                borderRadius: 10,
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'background 0.18s, box-shadow 0.18s',
                position: 'relative',
                background: isActive
                  ? 'linear-gradient(90deg, rgba(124,58,237,0.85), rgba(79,70,229,0.75))'
                  : 'transparent',
                boxShadow: isActive ? '0 2px 18px rgba(124,58,237,0.35)' : 'none',
              }}
              whileHover={{
                background: isActive
                  ? 'linear-gradient(90deg, rgba(124,58,237,0.9), rgba(79,70,229,0.8))'
                  : 'rgba(255,255,255,0.05)',
              }}
            >
              {/* Active left bar */}
              {isActive && (
                <span
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: '20%',
                    height: '60%',
                    width: 3,
                    borderRadius: '0 3px 3px 0',
                    background: '#a78bfa',
                    boxShadow: '0 0 8px #a78bfa',
                  }}
                />
              )}

              <Icon
                size={16}
                style={{
                  color: isActive ? '#e9d5ff' : 'rgba(196,181,253,0.55)',
                  flexShrink: 0,
                  transition: 'color 0.15s',
                }}
              />
              <span
                style={{
                  fontSize: 13,
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? '#fff' : 'rgba(196,181,253,0.7)',
                  letterSpacing: '0.01em',
                  transition: 'color 0.15s',
                }}
              >
                {item.label}
              </span>

              {/* Active dot */}
              {isActive && (
                <span
                  style={{
                    marginLeft: 'auto',
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: '#c4b5fd',
                    boxShadow: '0 0 6px #a78bfa',
                    flexShrink: 0,
                  }}
                />
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* ── Footer ── */}
      <div
        style={{
          padding: '12px',
          borderTop: '1px solid rgba(139,92,246,0.15)',
        }}
      >
        <motion.button
          onClick={handleLogout}
          whileHover={{ background: 'rgba(239,68,68,0.12)' }}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: 11,
            padding: '9px 12px',
            borderRadius: 10,
            border: '1px solid rgba(239,68,68,0.2)',
            cursor: 'pointer',
            background: 'rgba(239,68,68,0.07)',
            color: '#f87171',
            fontSize: 13,
            fontWeight: 500,
            transition: 'background 0.18s',
          }}
        >
          <LogOut size={16} style={{ flexShrink: 0 }} />
          Logout
        </motion.button>
      </div>
    </aside>
  );

  return (
    <>
      {/* ── Mobile overlay ── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(2px)',
              zIndex: 40,
            }}
            className="md:hidden"
          />
        )}
      </AnimatePresence>

      {/*
        ── Desktop: always visible (no animation needed) ──
        ── Mobile:  slide in/out                         ──
      */}

      {/* Desktop — static, always rendered */}
      <div className="hidden md:block" style={{ height: '100vh', flexShrink: 0 }}>
        {sidebarContent}
      </div>

      {/* Mobile — animated */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="mobile-sidebar"
            initial={{ x: -256 }}
            animate={{ x: 0 }}
            exit={{ x: -256 }}
            transition={{ type: 'spring', stiffness: 320, damping: 32 }}
            style={{ position: 'fixed', top: 0, left: 0, zIndex: 50 }}
            className="md:hidden"
          >
            {sidebarContent}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}